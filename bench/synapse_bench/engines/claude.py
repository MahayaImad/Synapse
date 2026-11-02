"""Moteur Claude (API Anthropic). Hors d'Algérie : n'accepte que des images anonymisées (voir runner)."""
from __future__ import annotations

import base64
import json
import time

import anthropic
from pydantic import ValidationError

from .. import prompts
from ..schema import CHOIX_SCHEMA, LECTURE_SCHEMA, Choix, Lecture
from .base import EngineResult


class ClaudeEngine:
    external = True

    def __init__(self, model: str = "claude-opus-5-5", effort_lecture: str = "high", effort_choix: str = "medium",
                 client: anthropic.Anthropic | None = None):
        self.model = model
        self.name = f"claude:{model}"
        self.effort_lecture = effort_lecture
        self.effort_choix = effort_choix
        self.client = client or anthropic.Anthropic()  # ANTHROPIC_API_KEY ou profil `ant auth login`

    def _call(self, content: list[dict], schema: dict, effort: str):
        return self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # en cas de refus d'un filtre de sécurité, relance serveur sur le modèle recommandé
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": content}],
        )

    @staticmethod
    def _text(resp) -> str:
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"refus : {getattr(resp.stop_details, 'category', None)}")
        if resp.stop_reason == "max_tokens":
            raise RuntimeError("réponse tronquée (max_tokens)")
        return next(b.text for b in resp.content if b.type == "text")

    @staticmethod
    def _usage(resp) -> dict:
        u = resp.usage
        return {"input_tokens": u.input_tokens, "output_tokens": u.output_tokens}

    def _lecture(self, content: list[dict]) -> EngineResult:
        t = time.perf_counter()
        try:
            resp = self._call(content, LECTURE_SCHEMA, self.effort_lecture)
            brut = self._text(resp)
            return EngineResult(Lecture.model_validate(json.loads(brut)), time.perf_counter() - t, brut=brut,
                                usage=self._usage(resp))
        except (anthropic.APIStatusError, anthropic.APIConnectionError, RuntimeError, ValidationError, ValueError) as e:
            return EngineResult(None, time.perf_counter() - t, erreur=f"{type(e).__name__}: {e}")

    def read(self, png: bytes) -> EngineResult:
        image = {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                              "data": base64.standard_b64encode(png).decode()}}
        return self._lecture([image, {"type": "text", "text": prompts.LECTURE}])

    def read_text(self, transcription: str) -> EngineResult:
        return self._lecture([{"type": "text", "text": f"{prompts.LECTURE_TEXTE}\n\n<transcription>\n{transcription}\n</transcription>"}])

    def choose(self, ligne_texte: str, candidats_texte: str):
        t = time.perf_counter()
        try:
            resp = self._call([{"type": "text", "text": f"{prompts.CHOIX}\n\nLigne lue :\n{ligne_texte}\n\nCandidats :\n{candidats_texte}"}],
                              CHOIX_SCHEMA, self.effort_choix)
            return Choix.model_validate(json.loads(self._text(resp))), time.perf_counter() - t, None
        except (anthropic.APIStatusError, anthropic.APIConnectionError, RuntimeError, ValidationError, ValueError) as e:
            return None, time.perf_counter() - t, f"{type(e).__name__}: {e}"
