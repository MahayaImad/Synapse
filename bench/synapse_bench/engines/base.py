"""Interface commune des moteurs de lecture."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..schema import Choix, Lecture


@dataclass
class EngineResult:
    lecture: Lecture | None
    secondes: float
    erreur: str | None = None
    brut: str = ""
    usage: dict = field(default_factory=dict)


class Engine(Protocol):
    name: str
    #: True si le modèle tourne hors d'Algérie : l'image doit alors être anonymisée (masque ou zone).
    external: bool

    def read(self, png: bytes) -> EngineResult: ...

    def choose(self, ligne_texte: str, candidats_texte: str) -> tuple[Choix | None, float, str | None]: ...
