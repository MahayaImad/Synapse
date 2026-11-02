"""Format de sortie demandé aux modèles (lecture) et au choix du produit (liaison)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Posologie(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dose_par_prise: float | None  # nombre seulement, jamais calculé
    unite: str | None  # cp, gélule, ml, mg, goutte, sachet, cuillère, bouffée, application…
    frequence: str | None  # forme « N/j », « N/sem », « si besoin »
    duree: str | None  # forme « N j », « N sem », « N mois »
    voie: str | None  # orale, cutanée, inhalée, injectable…


class LigneLue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texte_brut: str  # transcription exacte de la ligne
    nom_lu: str | None
    dosage_lu: str | None
    forme_lue: str | None
    posologie: Posologie
    lisibilite: Literal["claire", "douteuse", "illisible"]


class Lecture(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lignes: list[LigneLue]
    age: str | None
    poids: str | None


def _nullable(t: str) -> dict:
    return {"anyOf": [{"type": t}, {"type": "null"}]}


POSOLOGIE_SCHEMA = {
    "type": "object",
    "properties": {
        "dose_par_prise": _nullable("number"),
        "unite": _nullable("string"),
        "frequence": _nullable("string"),
        "duree": _nullable("string"),
        "voie": _nullable("string"),
    },
    "required": ["dose_par_prise", "unite", "frequence", "duree", "voie"],
    "additionalProperties": False,
}

LECTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "lignes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "texte_brut": {"type": "string"},
                    "nom_lu": _nullable("string"),
                    "dosage_lu": _nullable("string"),
                    "forme_lue": _nullable("string"),
                    "posologie": POSOLOGIE_SCHEMA,
                    "lisibilite": {"type": "string", "enum": ["claire", "douteuse", "illisible"]},
                },
                "required": ["texte_brut", "nom_lu", "dosage_lu", "forme_lue", "posologie", "lisibilite"],
                "additionalProperties": False,
            },
        },
        "age": _nullable("string"),
        "poids": _nullable("string"),
    },
    "required": ["lignes", "age", "poids"],
    "additionalProperties": False,
}

CHOIX_SCHEMA = {
    "type": "object",
    "properties": {
        "choix": {"type": "string"},  # une référence de la liste (« p3 ») ou « incertain »
        "raison": {"type": "string"},
    },
    "required": ["choix", "raison"],
    "additionalProperties": False,
}


class Choix(BaseModel):
    model_config = ConfigDict(extra="forbid")
    choix: str
    raison: str
