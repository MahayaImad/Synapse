"""Génère app/lib/data/accents.g.dart depuis la normalisation de référence du backend
(NFKD puis suppression des marques combinantes, comme synapse_admin.normalize.strip_accents).

Usage : uv run python scripts/make_accent_table.py ../app/lib/data/accents.g.dart
"""
import sys
import unicodedata
from pathlib import Path

RANGES = [(0x00A0, 0x024F), (0x0370, 0x03FF), (0x1E00, 0x1EFF), (0x2000, 0x218F), (0x2460, 0x24FF),
          (0x3000, 0x303F), (0xFB00, 0xFB06), (0xFF00, 0xFFEF)]


def strip(c: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", c) if not unicodedata.combining(ch))


def dart(s: str) -> str:
    return "'" + "".join(ch if ch.isascii() and ch not in "'\\$" else f"\\u{{{ord(ch):X}}}" for ch in s) + "'"


entries = []
for lo, hi in RANGES:
    for cp in range(lo, hi + 1):
        c = chr(cp)
        if unicodedata.category(c) == "Cn":
            continue
        s = strip(c)
        if s != c:
            entries.append(f"  0x{cp:04X}: {dart(s)},")
out = Path(sys.argv[1])
out.write_text("// GÉNÉRÉ par backend/scripts/make_accent_table.py — ne pas modifier à la main.\n"
               "// NFKD sans marques combinantes (référence : synapse_admin.normalize.strip_accents).\n"
               "const accentTable = <int, String>{\n" + "\n".join(entries) + "\n};\n", encoding="utf-8")
print(f"{len(entries)} entrées -> {out}")
