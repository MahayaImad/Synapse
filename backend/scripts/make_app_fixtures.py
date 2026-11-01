"""Génère les fichiers de test de l'app Flutter : nomenclature de test, cas de recherche et d'équivalents.

Les résultats attendus sont calculés par le code de référence du backend (search.py) :
l'app doit rendre exactement les mêmes.

Usage : uv run python scripts/make_app_fixtures.py ../app/test/fixtures
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import date
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from rows import product  # noqa: E402

from synapse_admin.export import export_sqlite  # noqa: E402
from synapse_admin.search import STATUS_RANK, search  # noqa: E402

LONG_PACKAGING = ("B/1 FLC DE LYOPHILISAT +1 FLC DE 05 ML DE SOLVANT (EAU POUR PREPARATIONS INJECTABLES)"
                  "+1 SERINGUE+2 CANULES+1 CATHETER VEINEUX PERIPHERIQUE+2 TAMPONS ALCOOLISES ET 1 NOTICE PATIENT EN LANGUE FRANCAISE ET ARABE")

CETI = dict(code="01 A 003", dci="CETIRIZINE DICHLORHYDRATE", forme="COMPRIME PELLICULE")
PARA = dict(code="05 A 010", dci="PARACÉTAMOL", forme="COMPRIME")
METF = dict(code="07 B 021", dci="METFORMINE CHLORHYDRATE", forme="COMPRIME PELLICULE")
AMOX = dict(code="02 C 011", dci="AMOXICILLINE", forme="GELULE")
OMEP = dict(code="09 A 044", dci="OMEPRAZOLE", forme="GELULE GASTRORESISTANTE")
AMLO = dict(code="03 D 017", dci="AMLODIPINE BESILATE", forme="COMPRIME")
KETO = dict(code="06 B 030", dci="KETOPROFENE", forme="COMPRIME A LIBERATION PROLONGEE")

# (marque, dosage, conditionnement, feuille, n° d'enregistrement, extra)
CATALOG = [
    ("CETIRIPEX", "10MG", "B/15", "en_vigueur", "035/01 A 003/17/23", CETI),
    ("ZYTREX", "10MG", "B/10", "en_vigueur", "077/01 A 003/17/24", CETI),
    ("HISTARIZINE", "10 MG", "B/10", "en_vigueur", "304/01 A 003/04/17", CETI),
    ("CETIRIZINE MYLAN", "10MG", "B/15", "retire", "450/01 A 003/07/13",
     {**CETI, "date_retrait": date(2024, 3, 31), "motif_retrait": "RETRAIT PAR LE DETENTEUR POUR MOTIF COMMERCIAL"}),
    ("ARTIZ", "10MG", "B/10", "non_renouvele", "352/01 A 003/06/22", CETI),
    ("CETIRIPEX", "5MG/ML", "FL/150ML", "en_vigueur", "035/01 A 004/18", {**CETI, "forme": "SOLUTION BUVABLE"}),
    ("ZYTREX ENFANT", "5MG", "B/20", "en_vigueur", "077/01 A 003/19", CETI),
    ("DOLIPRANE", "1G", "B/8", "en_vigueur", "111/05 A 010/20", PARA),
    ("DOLIPRANE", "500MG", "B/16", "en_vigueur", "111/05 A 010/21", PARA),
    ("EFFERALGAN", "1G", "B/8", "en_vigueur", "112/05 A 010/19", PARA),
    ("PARALGAN", "1G", "B/10", "retire", "113/05 A 010/09",
     {**PARA, "date_retrait": "ABROGATION", "motif_retrait": "PRODUIT NON COMMERCIALISE ET DECISION NON RENOUVELEE"}),
    ("DOLKA", "500 MG", "B/20", "non_renouvele", "114/05 A 010/12", PARA),
    ("GLUCOPHAGE", "500MG", "B/30", "en_vigueur", "201/07 B 021/15", METF),
    ("GLUCOPHAGE", "850MG", "B/30", "en_vigueur", "201/07 B 021/16", METF),
    ("GLUCOPHAGE", "1000MG", "B/30", "en_vigueur", "201/07 B 021/17", METF),
    ("METFORAL", "850MG", "B/40", "en_vigueur", "202/07 B 021/18", METF),
    ("DIAFORMINE", "850MG", "B/30", "retire", "203/07 B 021/05",
     {**METF, "date_retrait": date(2022, 6, 30), "motif_retrait": "ARRET DE COMMERCIALISATION"}),
    ("CLAMOXYL", "1G", "B/14", "retire", "301/02 C 011/03",
     {**AMOX, "forme": "COMPRIME DISPERSIBLE", "date_retrait": date(2023, 1, 15), "motif_retrait": "RETRAIT PAR LE DETENTEUR"}),
    ("AMOXIL", "500MG", "B/12", "en_vigueur", "302/02 C 011/20", AMOX),
    ("HICONCIL", "500MG", "B/12", "en_vigueur", "303/02 C 011/21", AMOX),
    ("AMOXYPEN", "250MG/5ML", "FL/60ML", "en_vigueur", "304/02 C 011/22", {**AMOX, "forme": "POUDRE POUR SUSPENSION BUVABLE"}),
    ("MOPRAL", "20MG", "B/14", "en_vigueur", "401/09 A 044/14", OMEP),
    ("OMEPRAZ", "20MG", "B/28", "en_vigueur", "402/09 A 044/16", OMEP),
    ("OMEPRAZ", "40MG", "B/14", "en_vigueur", "402/09 A 044/17", OMEP),
    ("AMLOR", "5MG", "B/30", "en_vigueur", "501/03 D 017/11", AMLO),
    ("AMLOR", "10MG", "B/30", "en_vigueur", "501/03 D 017/12", AMLO),
    ("AMLODIPINE SAIDAL", "5MG", "B/30", "en_vigueur", "003/03 D 017/19", {**AMLO, "labo": "GROUPE SAIDAL"}),
    ("BIPROFENID", "100MG", "B/20", "en_vigueur", "601/06 B 030/10", KETO),
    ("PROFENID", "100MG", "B/20", "non_renouvele", "602/06 B 030/02", KETO),
    ("ALCOOL CHIRURGICAL 90°", "90°", "FL./1000ML", "en_vigueur", "003/20 B 030/97/09",
     dict(code="20 B 030", dci="ALCOOL ETHYLIQUE", forme="SOL. USAGE EXTERNE", labo="GROUPE SAIDAL", liste="")),
    ("CODOLIPRANE", "500MG/30MG", "B/16", "en_vigueur", "111/05 A 012/20",
     dict(code="05 A 012", dci="PARACÉTAMOL/CODEINE PHOSPHATE", forme="COMPRIME", liste="STUPEFIANT")),
    ("COAGIL-VII", "4,8MG", LONG_PACKAGING, "en_vigueur", "003/12 J 118/24",
     dict(code="12 J 118", dci="EPTACOG ALFA (FACTEUR VII DE COAGULATION HUMAIN RECOMBINANT ACTIVE)",
          forme="POUDRE ET SOLVANT POUR SOLUTION INJECTABLE", liste="LISTE I", labo="GROUPE SAIDAL", type="BIO")),
    ("NOVOSEVEN", "4,8MG", "B/1 FLACON", "en_vigueur", "640/12 J 118/22",
     dict(code="12 J 118", dci="EPTACOG ALFA (FACTEUR VII DE COAGULATION HUMAIN RECOMBINANT ACTIVE)",
          forme="POUDRE ET SOLVANT POUR SOLUTION INJECTABLE", liste="LISTE I", labo="NOVO NORDISK", pays="DANEMARK",
          type="BIO", statut="I")),
    ("VENTOLINE", "100UG/DOSE", "FL/200 DOSES", "en_vigueur", "701/10 C 005/08",
     dict(code="10 C 005", dci="SALBUTAMOL", forme="SUSPENSION POUR INHALATION", labo="GLAXOSMITHKLINE", pays="ROYAUME UNI", statut="I")),
    ("ASTHALIN", "100UG/DOSE", "FL/200 DOSES", "en_vigueur", "702/10 C 005/15",
     dict(code="10 C 005", dci="SALBUTAMOL", forme="SUSPENSION POUR INHALATION", labo="CIPLA", pays="INDE", statut="I")),
    ("LEVOTHYROX", "50UG", "B/30", "en_vigueur", "801/11 H 002/13",
     dict(code="11 H 002", dci="LEVOTHYROXINE SODIQUE", forme="COMPRIME SECABLE", labo="MERCK", pays="FRANCE", statut="I")),
    ("LEVOTHYROX", "100UG", "B/30", "en_vigueur", "801/11 H 002/14",
     dict(code="11 H 002", dci="LEVOTHYROXINE SODIQUE", forme="COMPRIME SECABLE", labo="MERCK", pays="FRANCE", statut="I")),
    ("SPASFON", "80MG", "B/10", "en_vigueur", "901/04 A 001/10",
     dict(code="04 A 001", dci="PHLOROGLUCINOL", forme="COMPRIME ORODISPERSIBLE", liste="")),
    ("SPASFON", "40MG/4ML", "B/6 AMP", "en_vigueur", "901/04 A 002/10",
     dict(code="04 A 002", dci="PHLOROGLUCINOL", forme="SOLUTION INJECTABLE")),
    ("XYDOL ENFANTS ET NOURRISSONS", "2,4%", "FL/100ML", "en_vigueur", "115/05 A 013/22",
     dict(code="05 A 013", dci="PARACÉTAMOL", forme="SUSPENSION BUVABLE", liste="")),
]

QUERIES = [
    "cetiri", "cetirizine", "zytrex", "zytrex enfant", "histarizine", "artiz", "mylan", "01 A 003", "01 a 003",
    "doliprane", "doliprane 1g", "doliprane 500", "paracetamol", "PARACÉTAMOL", "efferalgan", "paralgan",
    "glucophage", "glucophage 850", "metformine", "metforal", "diaformine", "clamoxyl", "amoxicilline", "amox",
    "omeprazole", "mopral", "amlor", "amlodipine", "saidal", "groupe saidal", "biprofenid", "biprofnid", "biprofenide",
    "profenid", "ketoprofene", "alcool", "alcool 90", "l'alcool 90°", "codoliprane", "codeine", "coagil", "eptacog",
    "novoseven", "ventoline", "ventolin", "salbutamol", "levothyrox", "levotyrox", "spasfon", "phloroglucinol",
    "xydol", "nourrissons", "cetripex", "dolipran", "glucofage", "zzzz", "12 J 118",
    '"', "*", "-", "L'ALCOOL", "é", "", "AND OR NOT", "a" * 300, "  doliprane  ", "d'alcool",
]


def build_catalog():
    items = []
    for i, (marque, dosage, packaging, sheet, reg, extra) in enumerate(CATALOG, start=1):
        extra = dict(extra)
        p = product(sheet=sheet, row_number=i, n_enregistrement=reg, marque=marque, dosage=dosage,
                    conditionnement=packaging, **{"labo": "LABO TEST", "pays": "ALGERIE", "liste": "LISTE II", **extra})
        items.append((uuid5(NAMESPACE_URL, f"synapse-test/{reg}/{marque}/{dosage}/{packaging}"), p))
    return items


def dosage_key(d: str) -> str:
    return "".join(d.split())


def equivalents(items, pid):
    by_id = {str(i): p for i, p in items}
    me = by_id[pid]
    others = [(str(i), p) for i, p in items if str(i) != pid and p.dci_code == me.dci_code]
    order = lambda x: (STATUS_RANK[x[1].sheet], x[1].brand, x[0])
    same = sorted([x for x in others if dosage_key(x[1].dosage) == dosage_key(me.dosage)], key=order)
    groups: dict[str, list] = {}
    for x in sorted([x for x in others if dosage_key(x[1].dosage) != dosage_key(me.dosage)], key=order):
        groups.setdefault(dosage_key(x[1].dosage), []).append(x)
    other = [{"dosage": g[0][1].dosage, "ids": [i for i, _ in g]} for _, g in sorted(groups.items())]
    return {"id": pid, "statut": me.sheet, "same_dosage": [i for i, _ in same],
            "active_same_dosage": [i for i, p in same if p.sheet == "en_vigueur"], "other_dosages": other}


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    items = build_catalog()
    meta = {"version": "2026-08", "reference_date": "2026-08-31", "source_sha256": "test", "source_filename": "test"}
    path = export_sqlite(items, meta, out_dir, write_manifest=False)
    final = out_dir / "nomenclature-test.sqlite"
    path.replace(final)
    with sqlite3.connect(final) as c:  # horodatage fixe : fichier reproductible
        c.execute("update meta set valeur='2026-09-01T00:00:00+00:00' where cle='published_at'")
    sqlite3.connect(final).execute("VACUUM").connection.close()
    cases = [{"query": q, "limit": lim, "ids": [h.product_id for h in search(final, q, lim)]}
             for q in QUERIES for lim in ((20, 3) if q in ("cetirizine", "doliprane") else (20,))]
    (out_dir / "search_cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    eq = [equivalents(items, str(i)) for i, _ in items]
    (out_dir / "equivalents_cases.json").write_text(json.dumps(eq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(items)} produits, {len(cases)} cas de recherche, {len(eq)} cas d'équivalents -> {out_dir}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
