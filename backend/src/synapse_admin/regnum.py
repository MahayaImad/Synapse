"""Numéro d'enregistrement : LLL/FF S NNN/AA[/RR].

LLL = labo, FF S NNN = code DCI (famille, sous-famille, n° molécule-forme),
AA = année d'enregistrement initial, RR = année de renouvellement.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_REG = re.compile(
    r"^\s*(\d{3})\s*/\s*(\d{2})\s*([A-Z])\s*(\d{3})\s*/\s*(\d{2})(?:\s*/\s*(\d{2}))?\s*$"
)
_CODE = re.compile(r"^\s*(\d{2})\s*([A-Z])\s*(\d{3})\s*$")


@dataclass(frozen=True)
class RegistrationNumber:
    raw: str
    lab: str
    dci_code: str
    family: str
    subfamily: str
    molecule_num: str
    initial_year: str
    renewal_year: str | None

    @property
    def stem(self) -> tuple[str, str, str]:
        """Racine stable au renouvellement : (labo, code DCI, année initiale)."""
        return (self.lab, self.dci_code, self.initial_year)


def parse_registration(raw: str) -> RegistrationNumber | None:
    m = _REG.match(raw or "")
    if not m:
        return None
    lab, fam, sub, num, init, renew = m.groups()
    return RegistrationNumber(
        raw=raw.strip(),
        lab=lab,
        dci_code=f"{fam} {sub} {num}",
        family=fam,
        subfamily=sub,
        molecule_num=num,
        initial_year=init,
        renewal_year=renew,
    )


def normalize_dci_code(raw: str) -> str:
    """'01  A 003' / '01A003' -> '01 A 003' ; sinon texte nettoyé."""
    text = " ".join(str(raw or "").split()).upper()
    m = _CODE.match(text)
    return f"{m.group(1)} {m.group(2)} {m.group(3)}" if m else text
