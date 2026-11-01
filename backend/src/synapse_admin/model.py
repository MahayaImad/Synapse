"""Types partagés du noyau d'import."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal
from uuid import UUID

from .regnum import RegistrationNumber

SheetKind = Literal["en_vigueur", "non_renouvele", "retire"]
SHEET_KINDS: tuple[SheetKind, ...] = ("en_vigueur", "non_renouvele", "retire")

# Champs dont la modification a un impact clinique : jamais automatique.
CLINICAL_FIELDS = ("brand", "dosage", "form")


@dataclass
class RawRow:
    sheet: SheetKind
    sheet_title: str
    row_number: int
    values: dict[str, object]  # champ canonique -> valeur de cellule
    raw: dict[str, object]  # en-tête d'origine -> valeur JSON-sérialisable


@dataclass
class Anomaly:
    sheet: SheetKind
    row_number: int
    field: str
    value: str
    message: str


@dataclass
class Product:
    sheet: SheetKind
    row_number: int
    reg_raw: str
    registration: RegistrationNumber | None
    dci_code: str
    dci: str
    brand: str
    form: str
    dosage: str
    packaging: str
    liste: Literal["I", "II", "STUPEFIANT"] | None
    hospital: bool
    pharmacy: bool
    type: Literal["GE", "RE", "BIO"] | None
    origin: Literal["fabrique_localement", "importe"] | None
    lab: str
    country: str
    initial_date: date | None
    final_date: date | None
    stability: str
    obs: str
    withdrawal_date: date | None
    withdrawal_reason: str
    raw: dict[str, object] = field(repr=False)

    @property
    def presentation_key(self) -> tuple[str, str, str]:
        return (self.brand, self.dosage, self.packaging)

    @property
    def stem(self) -> tuple[str, str, str] | None:
        return self.registration.stem if self.registration else None


# Attributs ignorés quand on compare deux versions d'un même produit.
NON_COMPARED_FIELDS = {"sheet", "row_number", "raw", "registration"}
