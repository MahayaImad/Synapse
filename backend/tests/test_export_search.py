import hashlib
import json
import random
import time
from uuid import uuid4

import pytest

from rows import product
from synapse_admin.publish import export_sqlite
from synapse_admin.search import STATUS_RANK, search

META = {"version": "2026-08", "reference_date": "2026-08-31", "source_sha256": "f00d"}


def catalog():
    return [
        (uuid4(), product()),
        (uuid4(), product(n_enregistrement="077/01 A 003/17/24", marque="ZYTREX", labo="LAM")),
        (uuid4(), product(sheet="retire", n_enregistrement="450/01 A 003/07/13", marque="CETIRIZINE MYLAN", labo="MYLAN SAS")),
        (uuid4(), product(n_enregistrement="003/20 B 030/97/09", code="20 B 030", dci="ALCOOL ETHYLIQUE",
                          marque="ALCOOL CHIRURGICAL 90°", forme="SOL. USAGE EXTERNE", dosage="90°", labo="GROUPE SAIDAL")),
        (uuid4(), product(n_enregistrement="111/05 A 010/20", code="05 A 010", dci="PARACÉTAMOL", marque="DOLIPRANE",
                          dosage="1G", labo="SANOFI")),
    ]


@pytest.fixture
def published(tmp_path):
    return export_sqlite(catalog(), META, tmp_path)


def names(hits):
    return [h.marque for h in hits]


def test_prefix(published):
    assert names(search(published, "cetiri"))[0] == "CETIRIPEX"


def test_dci_search(published):
    assert {"CETIRIPEX", "ZYTREX", "CETIRIZINE MYLAN"} <= set(names(search(published, "cetirizine")))


def test_accents_ignored_both_ways(published):
    assert names(search(published, "paracetamol")) == ["DOLIPRANE"]
    assert names(search(published, "PARACÉTAMOL")) == ["DOLIPRANE"]


def test_multi_word_and_code(published):
    assert names(search(published, "doliprane 1g")) == ["DOLIPRANE"]
    assert "ALCOOL CHIRURGICAL 90°" in names(search(published, "20 B 030"))


def test_typo_via_trigram(published):
    assert "CETIRIPEX" in names(search(published, "cetripex"))
    assert "DOLIPRANE" in names(search(published, "dolipran"))


def test_withdrawn_listed_after_active(published):
    st = [h.statut for h in search(published, "cetirizine")]
    assert st == sorted(st, key=STATUS_RANK.get) and st[-1] == "retire"


@pytest.mark.parametrize("q", ['"', "*", "-", "L'ALCOOL", "é", "", "   ", "AND OR NOT", "NEAR(", "a" * 300])
def test_special_queries_never_raise(published, q):
    search(published, q)


def test_apostrophe_query(published):
    assert "ALCOOL CHIRURGICAL 90°" in names(search(published, "l'alcool"))


def test_manifest_sha_matches_file(published):
    m = json.loads((published.parent / "manifest.json").read_text())
    assert m["file"] == published.name and m["version"] == "2026-08" and m["source_sha256"] == "f00d"
    assert m["sha256"] == hashlib.sha256(published.read_bytes()).hexdigest() and m["size"] == published.stat().st_size


def test_meta_table(published):
    import sqlite3
    with sqlite3.connect(published) as c:
        assert dict(c.execute("select cle, valeur from meta"))["version"] == "2026-08"


@pytest.fixture
def big_published(tmp_path):
    rnd = random.Random(7)
    syll = ["CE", "TI", "RI", "PEX", "DO", "LI", "PRA", "NE", "AMO", "XI", "CIL", "ZO", "LAN", "MET", "FOR", "MINE"]
    rows = []
    for i in range(6000):
        brand = "".join(rnd.choice(syll) for _ in range(rnd.randint(2, 4)))
        rows.append((uuid4(), product(row_number=i, n_enregistrement=f"{i % 900:03d}/01 A {i % 999:03d}/20",
                                      marque=brand, dci=f"DCI {brand[:4]}", dosage=f"{rnd.randint(1, 1000)}MG",
                                      sheet=rnd.choice(["en_vigueur", "en_vigueur", "retire", "non_renouvele"]))))
    return export_sqlite(rows, META, tmp_path), [p.brand for _, p in rows]


def test_search_under_300ms(big_published):
    path, brands = big_published
    rnd = random.Random(1)
    queries = [b[: rnd.randint(3, len(b))] for b in rnd.sample(brands, 40)] + ["cetripex", "doliprn", "zz", "amoxicilin",
                                                                              "a", "metformine 500", "x", "pex", "ne", "lan"]
    worst = 0.0
    for q in queries:
        t = time.perf_counter(); search(path, q); worst = max(worst, time.perf_counter() - t)
    assert worst < 0.3, worst
