"""Jeu d'essai : une image + un fichier YAML d'annotation par ordonnance.

data/ORD-001.jpg
data/ORD-001.yaml :
    type: manuscrite            # ou imprimee
    masques: [[0.0, 0.0, 1.0, 0.18]]   # zones à noircir (patient, médecin, cachet), fractions 0–1
    zone: [0.0, 0.18, 1.0, 0.85]       # optionnel : seule zone envoyée (lignes de médicaments)
    attendu:
      age: null
      poids: null
      lignes:
        - produit_id: "…"        # identifiant dans la nomenclature (ou null si absent de la nomenclature)
          marque: AUGMENTIN
          dosage: 1G/125MG
          forme: COMPRIME
          posologie: {dose_par_prise: 1, unite: cp, frequence: 2/j, duree: 7 j, voie: orale}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")


@dataclass
class Attendu:
    produit_id: str | None
    marque: str
    dosage: str | None
    forme: str | None
    posologie: dict


@dataclass
class Ordonnance:
    id: str
    image_path: Path
    type: str  # imprimee | manuscrite
    masques: list[tuple[float, float, float, float]]
    zone: tuple[float, float, float, float] | None
    lignes: list[Attendu]
    age: str | None = None
    poids: str | None = None
    notes: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def anonymisee(self) -> bool:
        """Au moins un masque ou une zone : condition minimale avant tout envoi hors du serveur local."""
        return bool(self.masques) or self.zone is not None


def load(folder: Path) -> list[Ordonnance]:
    folder = Path(folder)
    out = []
    for y in sorted(folder.glob("*.yaml")):
        meta = yaml.safe_load(y.read_text(encoding="utf-8")) or {}
        img = next((y.with_suffix(e) for e in IMAGE_EXT if y.with_suffix(e).exists()), None)
        if img is None:
            raise FileNotFoundError(f"image absente pour {y.name}")
        if meta.get("type") not in ("imprimee", "manuscrite"):
            raise ValueError(f"{y.name} : type doit valoir imprimee ou manuscrite")
        att = meta.get("attendu") or {}
        out.append(Ordonnance(
            id=y.stem,
            image_path=img,
            type=meta["type"],
            masques=[tuple(m) for m in meta.get("masques") or []],
            zone=tuple(meta["zone"]) if meta.get("zone") else None,
            lignes=[Attendu(l.get("produit_id"), l["marque"], l.get("dosage"), l.get("forme"), l.get("posologie") or {})
                    for l in att.get("lignes") or []],
            age=att.get("age"),
            poids=att.get("poids"),
            notes=meta.get("notes", ""),
        ))
    return out
