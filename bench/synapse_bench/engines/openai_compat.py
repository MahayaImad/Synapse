"""Moteur open-weight servi par une API compatible OpenAI (vLLM, Ollama, LM Studio…) sur votre machine GPU.

Exemples :
    vllm serve Qwen/Qwen3-VL-32B-Instruct-FP8 --max-model-len 16384      → base_url=http://GPU:8000/v1
    ollama run qwen3-vl:8b                                               → base_url=http://GPU:11434/v1
"""
from __future__ import annotations

import base64
import json
import time

import openai
from pydantic import ValidationError

from .. import prompts
from ..schema import CHOIX_SCHEMA, LECTURE_SCHEMA, Choix, Lecture
from .base import EngineResult


class OpenAICompatEngine:
    def __init__(self, base_url: str, model: str, *, external: bool = False, api_key: str = "local",
                 structured: bool = True, timeout: float = 300, client: openai.OpenAI | None = None):
        self.model = model
        self.name = f"local:{model}"
        #: False si le serveur est en Algérie (aucune donnée ne quitte le pays).
        self.external = external
        #: Sortie JSON contrainte par schéma (vLLM et Ollama récents) ; sinon JSON demandé dans la consigne.
        self.structured = structured
        self.client = client or openai.OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)

    def _complete(self, content: list[dict], schema: dict | None, name: str) -> tuple[str, dict]:
        kwargs = {}
        if schema is not None and self.structured:
            kwargs["response_format"] = {"type": "json_schema", "json_schema": {"name": name, "schema": schema, "strict": True}}
        resp = self.client.chat.completions.create(model=self.model, temperature=0, max_tokens=8000,
                                                   messages=[{"role": "user", "content": content}], **kwargs)
        u = resp.usage
        usage = {"input_tokens": u.prompt_tokens, "output_tokens": u.completion_tokens} if u else {}
        return resp.choices[0].message.content or "", usage

    @staticmethod
    def _json(text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`").split("\n", 1)[1] if "\n" in text else text
        start, end = text.find("{"), text.rfind("}")
        return json.loads(text[start:end + 1])

    @staticmethod
    def _image(png: bytes) -> dict:
        return {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}}

    def _lecture(self, content: list[dict]) -> EngineResult:
        t = time.perf_counter()
        try:
            brut, usage = self._complete(content, LECTURE_SCHEMA, "lecture")
            return EngineResult(Lecture.model_validate(self._json(brut)), time.perf_counter() - t, brut=brut, usage=usage)
        except (openai.APIError, ValidationError, ValueError) as e:
            return EngineResult(None, time.perf_counter() - t, erreur=f"{type(e).__name__}: {e}")

    def read(self, png: bytes) -> EngineResult:
        hint = "" if self.structured else "\nRéponds uniquement avec un objet JSON conforme à ce schéma :\n" + json.dumps(LECTURE_SCHEMA)
        return self._lecture([self._image(png), {"type": "text", "text": prompts.LECTURE + hint}])

    def read_text(self, transcription: str) -> EngineResult:
        return self._lecture([{"type": "text", "text": f"{prompts.LECTURE_TEXTE}\n\n<transcription>\n{transcription}\n</transcription>"}])

    def ocr(self, png: bytes, consigne: str | None = None) -> tuple[str, float]:
        """Transcription brute (modèles OCR spécialisés : deepseek-ocr, PaddleOCR-VL…). Certains attendent
        leur propre consigne (ex. « Free OCR. » pour deepseek-ocr)."""
        t = time.perf_counter()
        text, _ = self._complete([self._image(png), {"type": "text", "text": consigne or prompts.OCR}], None, "ocr")
        return text, time.perf_counter() - t

    def choose(self, ligne_texte: str, candidats_texte: str):
        t = time.perf_counter()
        try:
            brut, _ = self._complete([{"type": "text", "text": f"{prompts.CHOIX}\n\nLigne lue :\n{ligne_texte}\n\nCandidats :\n{candidats_texte}"}],
                                     CHOIX_SCHEMA, "choix")
            return Choix.model_validate(self._json(brut)), time.perf_counter() - t, None
        except (openai.APIError, ValidationError, ValueError) as e:
            return None, time.perf_counter() - t, f"{type(e).__name__}: {e}"
