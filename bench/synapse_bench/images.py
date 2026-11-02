"""Préparation de l'image avant envoi : orientation, masques gravés, recadrage, métadonnées retirées."""
from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageOps

Box = tuple[float, float, float, float]  # x0, y0, x1, y1 en fraction de la largeur/hauteur (0–1)
MAX_SIDE = 2000


@dataclass
class Prepared:
    png: bytes  # image envoyée au modèle (sans métadonnées)
    image: Image.Image  # même image, pour l'affichage dans le notebook


def _px(box: Box, w: int, h: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError(f"rectangle hors image ou inversé : {box}")
    return round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h)


def prepare(raw: bytes, masks: list[Box] = (), zone: Box | None = None) -> Prepared:
    """Masques noirs gravés dans les pixels, puis recadrage éventuel sur la zone des médicaments.

    L'image est ré-encodée en PNG à partir des seuls pixels : EXIF, GPS et autres métadonnées disparaissent.
    """
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for m in masks:
        draw.rectangle(_px(m, w, h), fill=(0, 0, 0))
    if zone is not None:
        img = img.crop(_px(zone, w, h))
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE))
    clean = Image.frombytes("RGB", img.size, img.tobytes())  # pixels seuls : aucune métadonnée ne survit
    buf = io.BytesIO()
    clean.save(buf, format="PNG", optimize=True)
    return Prepared(buf.getvalue(), clean)
