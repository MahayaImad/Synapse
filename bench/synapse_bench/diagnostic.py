"""Diagnostic d'un serveur compatible OpenAI (Ollama, vLLM) : quelles fonctions du banc il accepte."""
from __future__ import annotations

import base64
import io
import time

import openai
import pandas as pd
from PIL import Image, ImageDraw

from .schema import CHOIX_SCHEMA


def _tiny_png() -> bytes:
    img = Image.new("RGB", (240, 60), "white")
    ImageDraw.Draw(img).text((10, 20), "DOLIPRANE 1g", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def diagnostic(engine) -> pd.DataFrame:
    """Quatre appels courts : texte simple, raisonnement coupé, sortie JSON par schéma, image."""
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(_tiny_png()).decode()}}
    essais = [
        ("texte simple", [{"type": "text", "text": "Réponds seulement : OK"}], {}),
        ("raisonnement coupé (reasoning_effort none)", [{"type": "text", "text": "Réponds seulement : OK"}],
         {"extra_body": {"reasoning_effort": "none"}}),
        ("sortie JSON par schéma", [{"type": "text", "text": "Réponds choix=incertain, raison=test."}],
         {"response_format": {"type": "json_schema", "json_schema": {"name": "choix", "schema": CHOIX_SCHEMA, "strict": True}}}),
        ("image", [image, {"type": "text", "text": "Quel mot lis-tu ?"}], {}),
    ]
    rows = []
    for nom, content, kwargs in essais:
        t = time.perf_counter()
        try:
            r = engine.client.chat.completions.create(model=engine.model, max_tokens=200, temperature=0,
                                                      messages=[{"role": "user", "content": content}], **kwargs)
            texte = (r.choices[0].message.content or "").strip().replace("\n", " ")
            rows.append({"essai": nom, "ok": True, "secondes": round(time.perf_counter() - t, 1), "réponse": texte[:120]})
        except openai.APIError as e:
            rows.append({"essai": nom, "ok": False, "secondes": round(time.perf_counter() - t, 1),
                         "réponse": f"{type(e).__name__}: {e}"[:300]})
    return pd.DataFrame(rows)
