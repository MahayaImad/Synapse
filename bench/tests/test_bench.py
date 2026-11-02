import io
import json

import pytest
from PIL import Image

from synapse_bench.dataset import Attendu, Ordonnance
from synapse_bench.images import prepare
from synapse_bench.linking import candidats, lier, quantites
from synapse_bench.runner import EnvoiRefuse, garde_fou, run
from synapse_bench.schema import Choix, Lecture, LigneLue, Posologie
from synapse_bench.engines.base import EngineResult
from synapse_bench.scoring import apparier, norm_duree, norm_frequence, posologie_ok, synthese, verdict_produit

DOLIPRANE_1000 = "24914b95-166d-4232-9f4c-22cae90ddd21"


def ligne(nom, dosage, dose=1, unite="cp", freq="3/j", duree="5 j", lisibilite="claire"):
    return LigneLue(texte_brut=f"{nom} {dosage}", nom_lu=nom, dosage_lu=dosage, forme_lue=None,
                    posologie=Posologie(dose_par_prise=dose, unite=unite, frequence=freq, duree=duree, voie="orale"),
                    lisibilite=lisibilite)


def png(w=400, h=300, color=(255, 255, 255), exif=False):
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    if exif:
        ex = Image.Exif()
        ex[0x010F] = "Fabricant"  # Make
        img.save(buf, format="JPEG", exif=ex)
    else:
        img.save(buf, format="PNG")
    return buf.getvalue()


def test_mask_is_burned_in_and_metadata_removed():
    p = prepare(png(exif=True), masks=[(0, 0, 1, 0.5)])
    img = Image.open(io.BytesIO(p.png))
    assert img.getpixel((10, 10)) == (0, 0, 0) and img.getpixel((10, 250)) == (255, 255, 255)
    assert not img.getexif() and not img.info.get("exif")


def test_zone_crop():
    p = prepare(png(400, 300), zone=(0, 0.5, 1, 1))
    assert p.image.size == (400, 150)


def test_invalid_box_refused():
    with pytest.raises(ValueError):
        prepare(png(), masks=[(0.5, 0, 0.2, 1)])


class FakeEngine:
    def __init__(self, external, lecture, choix="p1"):
        self.name, self.external, self.lecture, self._choix = "faux", external, lecture, choix

    def read(self, png):
        return EngineResult(self.lecture, 0.01)

    def choose(self, ligne_texte, candidats_texte):
        return Choix(choix=self._choix, raison="test"), 0.0, None


def ordonnance(tmp_path, masques=(), typ="imprimee"):
    img = tmp_path / "ORD.png"
    img.write_bytes(png())
    return Ordonnance("ORD", img, typ, list(masques), None,
                      [Attendu(DOLIPRANE_1000, "DOLIPRANE", "1000MG", "COMPRIME",
                               {"dose_par_prise": 1, "unite": "cp", "frequence": "3/j", "duree": "5 j", "voie": "orale"})])


def test_external_engine_refused_without_anonymisation(tmp_path):
    with pytest.raises(EnvoiRefuse):
        garde_fou(FakeEngine(True, None), ordonnance(tmp_path))
    garde_fou(FakeEngine(False, None), ordonnance(tmp_path))  # serveur en Algérie : autorisé
    garde_fou(FakeEngine(True, None), ordonnance(tmp_path, masques=[(0, 0, 1, 0.2)]))


def test_run_never_sends_unmasked_image_to_external_engine(tmp_path, db):
    sent = []

    class Spy(FakeEngine):
        def read(self, png):
            sent.append(png)
            return super().read(png)

    lignes, ords, _ = run([Spy(True, Lecture(lignes=[], age=None, poids=None))], [ordonnance(tmp_path)], db)
    assert sent == [] and "refusé" in ords.erreur.iloc[0] and list(lignes.verdict) == ["manquee"]


def test_quantites_convert_units():
    assert quantites("1g") == [(1000.0, "MG")]
    assert quantites("1G/125MG") == [(1000.0, "MG"), (125.0, "MG")]
    assert quantites("100µg/dose")[0] == pytest.approx((0.1, "MG"))


def test_candidates_rank_dosage_with_unit_conversion(db):
    hits = candidats(db, ligne("Doliprane", "1g"))
    assert hits[0].product_id == DOLIPRANE_1000  # « 1g » = 1000MG (forme « COMRPIME » telle que publiée)


def test_illegible_line_has_no_candidates(db):
    assert candidats(db, ligne("xxx", None, lisibilite="illisible")) == []


def test_choice_outside_list_is_uncertain(db):
    li = lier(FakeEngine(True, None, choix="p99"), db, ligne("Doliprane", "1g"))
    assert li.produit_id is None and li.hors_liste


def test_end_to_end_scoring(tmp_path, db):
    lecture = Lecture(lignes=[ligne("Doliprane", "1g"), ligne("Inventé", "5mg", dose=2)], age=None, poids=None)
    lignes, ords, details = run([FakeEngine(False, lecture)], [ordonnance(tmp_path)], db, tmp_path / "res")
    assert list(lignes.verdict) == ["exact"] and bool(lignes.posologie_ok.iloc[0])
    assert ords.lignes_inventees.iloc[0] == 1 and ords.lignes_inventees_dose.iloc[0] == 1
    s = synthese(lignes, ords)
    assert s.exact.iloc[0] == 1.0 and s.doses_inventees.iloc[0] == 1 and not s.atteint.iloc[0]
    assert json.loads((next((tmp_path / "res").glob("*.jsonl"))).read_text().splitlines()[0])["moteur"] == "faux"


def test_scoring_helpers():
    assert norm_frequence("3 fois par jour") == "3/J" and norm_duree("7 jours") == "7J"
    assert posologie_ok({"dose_par_prise": 1, "unite": "comprimé", "frequence": "3/j", "duree": "7 jours", "voie": "orale"},
                        {"dose_par_prise": 1.0, "unite": "cp", "frequence": "3 /j", "duree": "7 j", "voie": "Orale"})
    a = [Attendu(None, "AUGMENTIN", "1G", None, {}), Attendu(None, "SMECTA", None, None, {})]
    lues = [ligne("Smecta", None), ligne("Augmentin", "1g")]
    assert apparier(a, lues) == [(0, 1), (1, 0)]
    assert verdict_produit(a[0], None) == "incertain"
    assert verdict_produit(Attendu("x", "A", None, None, {}), {"id": "y", "marque": "A", "dosage": "", "forme": ""}) == "erreur"
