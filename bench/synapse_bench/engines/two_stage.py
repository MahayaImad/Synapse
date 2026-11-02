"""Lecture en deux temps : OCR local (en Algérie), puis structuration du TEXTE seul par un autre modèle.

C'est la variante « ne pas envoyer l'image » : seul le texte des lignes (zones masquées absentes) quitte le serveur.
"""
from __future__ import annotations

import time

from .base import EngineResult
from .openai_compat import OpenAICompatEngine


class TwoStageEngine:
    def __init__(self, ocr: OpenAICompatEngine, structurer, consigne_ocr: str | None = None):
        if ocr.external:
            raise ValueError("l'OCR doit tourner localement (en Algérie) dans ce mode")
        self.ocr = ocr
        self.structurer = structurer
        self.consigne_ocr = consigne_ocr
        self.name = f"2temps:{ocr.model}+{structurer.name}"
        # L'image ne sort jamais ; seul le texte part vers le structurateur (local ou Claude).
        self.external = False

    def read(self, png: bytes) -> EngineResult:
        t = time.perf_counter()
        try:
            text, _ = self.ocr.ocr(png, self.consigne_ocr)
        except Exception as e:  # noqa: BLE001 — banc d'essai : toute panne OCR est un résultat à afficher
            return EngineResult(None, time.perf_counter() - t, erreur=f"OCR : {e}")
        r = self.structurer.read_text(text)
        r.secondes = time.perf_counter() - t
        r.usage = {**r.usage, "ocr_texte": text}
        return r

    def choose(self, ligne_texte: str, candidats_texte: str):
        return self.structurer.choose(ligne_texte, candidats_texte)
