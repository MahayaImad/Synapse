"""Correspondance en-têtes du ministère -> champs canoniques."""
from __future__ import annotations

from .normalize import strip_accents

CANONICAL_FIELDS = (
    "n_enregistrement", "code", "dci", "marque", "forme", "dosage", "conditionnement", "liste", "p1", "p2", "obs",
    "labo", "pays", "date_enregistrement_initial", "date_enregistrement_final", "type", "statut", "duree_stabilite",
    "date_retrait", "motif_retrait",
)
REQUIRED_FIELDS = {"n_enregistrement", "code", "dci", "marque", "forme", "dosage", "conditionnement"}

HEADER_ALIASES = {
    "N°ENREGISTREMENT": "n_enregistrement",
    "N° ENREGISTREMENT": "n_enregistrement",
    "CODE": "code",
    "DENOMINATION COMMUNE INTERNATIONALE": "dci",
    "NOM DE MARQUE": "marque",
    "FORME": "forme",
    "DOSAGE": "dosage",
    "CONDITIONNEMENT": "conditionnement",
    "COND": "conditionnement",
    "LISTE": "liste",
    "P1": "p1",
    "P2": "p2",
    "OBS": "obs",
    "LABORATOIRES DETENTEUR DE LA DECISION D'ENREGISTREMENT": "labo",
    "PAYS DU LABORATOIRE DETENTEUR DE LA DECISION D'ENREGISTREMENT": "pays",
    "DATE D'ENREGISTREMENT INITIAL": "date_enregistrement_initial",
    "DATE D'ENREGISTREMENT FINAL": "date_enregistrement_final",
    "TYPE": "type",
    "STATUT": "statut",
    "DUREE DE STABILITE": "duree_stabilite",
    "DATE DE RETRAIT": "date_retrait",
    "MOTIF DE RETRAIT": "motif_retrait",
}

# Libellé affiché quand un champ obligatoire manque.
FIELD_LABELS = {v: k for k, v in reversed(list(HEADER_ALIASES.items()))}


def normalize_header(h: object) -> str:
    text = strip_accents(str(h or "")).replace("’", "'").upper()
    return " ".join(text.split())


def canonical_field(h: object) -> str | None:
    return HEADER_ALIASES.get(normalize_header(h))


def is_header_start(cell: object) -> bool:
    return normalize_header(cell).replace(" ", "") in ("N°", "N", "NO", "Nº")
