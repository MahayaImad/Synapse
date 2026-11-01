"""Fabriques de lignes de test (valeurs copiées des fichiers réels)."""
from __future__ import annotations

from datetime import datetime

from synapse_admin.model import RawRow
from synapse_admin.normalize import normalize_row

HEADERS = {
    "n_enregistrement": "N°ENREGISTREMENT",
    "code": "CODE",
    "dci": "DENOMINATION COMMUNE INTERNATIONALE",
    "marque": "NOM DE MARQUE",
    "forme": "FORME",
    "dosage": "DOSAGE",
    "conditionnement": "CONDITIONNEMENT",
    "liste": "LISTE",
    "p1": "P1",
    "p2": "P2",
    "obs": "OBS",
    "labo": "LABORATOIRES DETENTEUR DE LA DECISION D'ENREGISTREMENT",
    "pays": "PAYS DU LABORATOIRE DETENTEUR DE LA DECISION D'ENREGISTREMENT",
    "date_enregistrement_initial": "DATE D'ENREGISTREMENT INITIAL",
    "date_enregistrement_final": "DATE D'ENREGISTREMENT  FINAL",
    "type": "TYPE",
    "statut": "STATUT",
    "duree_stabilite": "DUREE DE STABILITE",
    "date_retrait": "DATE DE RETRAIT",
    "motif_retrait": "MOTIF DE RETRAIT",
}

CETIRIPEX = {
    "n_enregistrement": "035/01 A 003/17/23",
    "code": "01 A 003",
    "dci": "CETIRIZINE DICHLORHYDRATE",
    "marque": "CETIRIPEX",
    "forme": "COMPRIME PELLICULE SECABLE",
    "dosage": "10MG",
    "conditionnement": "B/15",
    "liste": "LISTE II",
    "p1": "HOP",
    "p2": "OFF",
    "labo": "PHARMALLIANCE",
    "pays": "ALGERIE",
    "date_enregistrement_initial": datetime(2017, 9, 10),
    "date_enregistrement_final": datetime(2023, 12, 4),
    "type": "GE",
    "statut": "F",
    "duree_stabilite": "24 MOIS",
}


def raw(sheet="en_vigueur", row_number=20, base=None, **overrides) -> RawRow:
    values = dict(base or CETIRIPEX)
    values.update(overrides)
    return RawRow(
        sheet=sheet,
        sheet_title="Nomenclature Aout 2026",
        row_number=row_number,
        values=values,
        raw={HEADERS[k]: (v.isoformat() if isinstance(v, datetime) else v) for k, v in values.items()},
    )


def product(sheet="en_vigueur", row_number=20, base=None, **overrides):
    p, _ = normalize_row(raw(sheet=sheet, row_number=row_number, base=base, **overrides))
    return p
