"""Génère des ordonnances FICTIVES (aucune donnée réelle) pour essayer le banc d'essai.

Usage : uv run python examples/make_examples.py
"""
from __future__ import annotations

import random
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "app"
ROBOTO = FONTS / "test" / "fonts" / "Roboto-Regular.ttf"
NUNITO = FONTS / "assets" / "fonts" / "Nunito-Regular.ttf"

DOLIPRANE = "24914b95-166d-4232-9f4c-22cae90ddd21"   # DOLIPRANE 1000MG COMRPIME (sic, tel que publié)
AUGMENTIN = "15ea9ae5-c6d6-42b1-8b77-7c96997b6c2b"   # AUGMENTIN 1G/125MG poudre en sachet
SMECTA = "a510e119-db6e-4aa9-a78c-a0cb3a670f5d"      # SMECTA FRAISE 3G/SACHET
VENTOLINE = "9c38ffaf-f71d-49c5-bc4c-8de1de9cc7c3"   # VENTOLINE 100µG/DOSE aérosol

ORDONNANCES = {
    "EX-001": ("imprimee", [
        ("DOLIPRANE 1g comprimé", "1 cp 3 fois par jour pendant 5 jours", DOLIPRANE, "DOLIPRANE", "1000MG", "COMPRIME",
         {"dose_par_prise": 1, "unite": "cp", "frequence": "3/j", "duree": "5 j", "voie": "orale"}),
        ("AUGMENTIN 1g/125mg sachet", "1 sachet 2 fois par jour pendant 7 jours", AUGMENTIN, "AUGMENTIN", "1G/125MG", None,
         {"dose_par_prise": 1, "unite": "sachet", "frequence": "2/j", "duree": "7 j", "voie": "orale"}),
    ]),
    "EX-002": ("imprimee", [
        ("SMECTA 3g sachet", "1 sachet 3 fois par jour pendant 3 jours", SMECTA, "SMECTA FRAISE", "3G/SACHET", None,
         {"dose_par_prise": 1, "unite": "sachet", "frequence": "3/j", "duree": "3 j", "voie": "orale"}),
        ("VENTOLINE 100µg aérosol", "2 bouffées si besoin", VENTOLINE, "VENTOLINE", "100µG/DOSE", "AEROSOL",
         {"dose_par_prise": 2, "unite": "bouffée", "frequence": "si besoin", "duree": None, "voie": "inhalée"}),
    ]),
    "EX-003": ("manuscrite", [
        ("Doliprane 1g", "1cp x3/j  5j", DOLIPRANE, "DOLIPRANE", "1000MG", "COMPRIME",
         {"dose_par_prise": 1, "unite": "cp", "frequence": "3/j", "duree": "5 j", "voie": None}),
        ("Smecta", "1 sachet x 3/j", SMECTA, "SMECTA FRAISE", "3G/SACHET", None,
         {"dose_par_prise": 1, "unite": "sachet", "frequence": "3/j", "duree": None, "voie": None}),
    ]),
}


def draw(oid: str, typ: str, lignes) -> tuple[Image.Image, list, list]:
    W, H = 1240, 1754  # A4 à 150 dpi
    img = Image.new("RGB", (W, H), (252, 251, 247))
    d = ImageDraw.Draw(img)
    rnd = random.Random(oid)
    f_head = ImageFont.truetype(str(ROBOTO), 34)
    f_text = ImageFont.truetype(str(NUNITO if typ == "manuscrite" else ROBOTO), 40 if typ == "manuscrite" else 34)
    d.text((80, 70), "Dr FICTIF Médecin — Médecine générale", font=f_head, fill="black")
    d.text((80, 115), "Cité FICTIVE, Alger — Tél 000 00 00 00", font=f_head, fill="black")
    d.text((80, 230), "Patient : PATIENT FICTIF        Âge : 34 ans", font=f_head, fill="black")
    d.text((W - 380, 230), "Le 02/11/2026", font=f_head, fill="black")
    d.line((80, 300, W - 80, 300), fill="black", width=2)
    y = 380
    for nom, poso, *_ in lignes:
        jitter = rnd.randint(-8, 8) if typ == "manuscrite" else 0
        d.text((120 + jitter, y), f"- {nom}", font=f_text, fill=(20, 30, 90) if typ == "manuscrite" else "black")
        d.text((170 + jitter, y + 55), poso, font=f_text, fill=(20, 30, 90) if typ == "manuscrite" else "black")
        y += 170
    d.text((W - 420, H - 300), "Signature / cachet FICTIFS", font=f_head, fill="black")
    if typ == "manuscrite":
        img = img.rotate(1.2, fillcolor=(252, 251, 247)).filter(ImageFilter.GaussianBlur(0.8))
    masques = [[0.0, 0.0, 1.0, 0.16], [0.6, 0.78, 1.0, 0.9]]  # en-tête (médecin, patient) et cachet
    zone = [0.0, 0.18, 1.0, 0.75]  # lignes de médicaments seulement
    return img, masques, zone


def main() -> None:
    for oid, (typ, lignes) in ORDONNANCES.items():
        img, masques, zone = draw(oid, typ, lignes)
        img.save(HERE / f"{oid}.png")
        meta = {
            "type": typ,
            "notes": "Ordonnance FICTIVE générée par make_examples.py",
            "masques": masques,
            "zone": zone,
            "attendu": {"age": "34 ans", "poids": None, "lignes": [
                {"produit_id": pid, "marque": marque, "dosage": dosage, "forme": forme, "posologie": poso}
                for _, _, pid, marque, dosage, forme, poso in lignes]},
        }
        (HERE / f"{oid}.yaml").write_text(yaml.safe_dump(meta, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"{len(ORDONNANCES)} ordonnances fictives -> {HERE}")


if __name__ == "__main__":
    main()
