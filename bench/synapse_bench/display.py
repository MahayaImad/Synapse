"""Affichage pour le notebook : image d'origine / image envoyée, tableaux colorés, graphiques."""
from __future__ import annotations

import io

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

from .dataset import Ordonnance
from .images import prepare

COULEURS = {"exact": "#d7f0dd", "incertain": "#fdf0c4", "manquee": "#fdf0c4", "erreur": "#f9d0cc"}


def avant_apres(o: Ordonnance, largeur: float = 11):
    """Ce qui reste sur le serveur (à gauche) et ce qui serait envoyé au modèle (à droite)."""
    origine = Image.open(io.BytesIO(o.image_path.read_bytes()))
    envoyee = prepare(o.image_path.read_bytes(), o.masques, o.zone).image
    fig, ax = plt.subplots(1, 2, figsize=(largeur, largeur * 0.7))
    for a, img, titre in ((ax[0], origine, f"{o.id} — original ({o.type})"), (ax[1], envoyee, "image envoyée")):
        a.imshow(img)
        a.set_title(titre)
        a.axis("off")
    fig.tight_layout()
    return fig


def tableau_lignes(lignes: pd.DataFrame):
    cols = ["moteur", "ordonnance", "attendu", "lu", "choisi", "verdict", "posologie_ok", "dose_inventee", "raison"]
    return lignes[cols].style.apply(
        lambda r: [f"background-color: {COULEURS.get(r.verdict, '')}"] * len(r), axis=1)


def graphique(synthese: pd.DataFrame):
    if synthese.empty:
        return None
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for i, typ in enumerate(["imprimee", "manuscrite"]):
        s = synthese[synthese.type == typ].set_index("moteur")[["exact", "incertain", "erreur"]]
        if s.empty:
            ax[i].set_title(f"{typ} : aucune ordonnance")
            continue
        s.plot.barh(stacked=True, ax=ax[i], color=["#4caf50", "#f2c037", "#e53935"], xlim=(0, 1))
        cible = 0.95 if typ == "imprimee" else 0.85
        ax[i].axvline(cible, color="black", linestyle="--", linewidth=1)
        ax[i].set_title(f"{typ} — produit exact (cible {cible:.0%})")
    fig.tight_layout()
    return fig
