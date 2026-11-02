"""Construit banc_essai.ipynb (le notebook est généré pour rester relisible dans git)."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
nb.cells = [
    md("""# Banc d'essai — lecture des ordonnances (TEMPORAIRE)

Compare les moteurs de lecture sur les **mêmes ordonnances** et avec les **cibles du cahier des charges** (§ 8) :
produit exact ≥ 95 % (imprimée) / ≥ 85 % (manuscrite, le reste « incertain »), posologie correcte ≥ 90 %,
**zéro dose inventée**.

**Données de santé** : les ordonnances réelles vont dans `bench/data/` (ignoré par git) avec leur fichier YAML
(masques et zone). Un moteur **hors d'Algérie** (Claude API) ne reçoit jamais une image sans masque ni zone :
le banc refuse l'envoi."""),
    md("## 1. Configuration\n\nLes moteurs s'activent par variables d'environnement (rien n'est écrit dans le notebook)."),
    code("""import os
from pathlib import Path

from synapse_bench.dataset import load
from synapse_bench.display import avant_apres, graphique, tableau_lignes
from synapse_bench.runner import run
from synapse_bench.scoring import synthese

BENCH = Path.cwd()
NOMENCLATURE = Path(os.environ.get("SYNAPSE_NOMENCLATURE", BENCH.parent / "app/assets/nomenclature/nomenclature.sqlite"))
DATA = Path(os.environ.get("SYNAPSE_DATA", BENCH / "data"))
if not any(DATA.glob("*.yaml")):
    DATA = BENCH / "examples"  # ordonnances FICTIVES pour essayer
ordonnances = load(DATA)
print(f"{len(ordonnances)} ordonnances dans {DATA} — nomenclature : {NOMENCLATURE.name}")"""),
    code("""engines = []

# Claude (API Anthropic, hors d'Algérie) : ANTHROPIC_API_KEY ou profil `ant auth login`
if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("SYNAPSE_CLAUDE"):
    from synapse_bench.engines.claude import ClaudeEngine
    engines.append(ClaudeEngine(model=os.environ.get("SYNAPSE_CLAUDE_MODEL", "claude-opus-5-5")))

# Modèle open-weight sur la machine GPU (vLLM / Ollama), en Algérie : SYNAPSE_LOCAL_URL + SYNAPSE_LOCAL_MODEL
# Plusieurs modèles : SYNAPSE_LOCAL_MODEL="Qwen/Qwen3-VL-32B-Instruct-FP8,Qwen/Qwen3-VL-4B-Instruct"
if os.environ.get("SYNAPSE_LOCAL_URL"):
    from synapse_bench.engines.openai_compat import OpenAICompatEngine
    for m in os.environ["SYNAPSE_LOCAL_MODEL"].split(","):
        engines.append(OpenAICompatEngine(os.environ["SYNAPSE_LOCAL_URL"], m.strip()))

# Deux temps : OCR spécialisé local (PaddleOCR-VL, GLM-OCR…) puis structuration du texte par le 1er moteur ci-dessus
if os.environ.get("SYNAPSE_OCR_URL") and engines:
    from synapse_bench.engines.openai_compat import OpenAICompatEngine
    from synapse_bench.engines.two_stage import TwoStageEngine
    ocr = OpenAICompatEngine(os.environ["SYNAPSE_OCR_URL"], os.environ["SYNAPSE_OCR_MODEL"], structured=False)
    engines.append(TwoStageEngine(ocr, engines[0]))

print("Moteurs :", [e.name for e in engines] or "aucun (définir les variables d'environnement)")"""),
    md("## 2. Ce qui part vers le modèle\n\nÀ gauche l'ordonnance telle qu'elle reste sur place ; à droite l'image envoyée (masques gravés, recadrage, métadonnées retirées)."),
    code("""for o in ordonnances:
    avant_apres(o)"""),
    md("## 3. Lecture, liaison à la nomenclature, notation"),
    code("""if engines:
    lignes, par_ordonnance, details = run(engines, ordonnances, NOMENCLATURE, BENCH / "results")
    resume = synthese(lignes, par_ordonnance)
else:
    lignes = par_ordonnance = resume = None
    print("Aucun moteur configuré : voir la section 1.")"""),
    md("### Synthèse par moteur et par type, face aux cibles\n\n`erreur` = mauvais produit choisi avec assurance (le pire cas) ; `atteint` exige aussi zéro erreur et zéro dose inventée."),
    code("""resume if resume is not None else None"""),
    code("""graphique(resume) if resume is not None else None"""),
    md("### Détail ligne par ligne\n\nVert : produit exact · jaune : incertain ou ligne manquée · rouge : erreur."),
    code("""tableau_lignes(lignes) if lignes is not None else None"""),
    md("### Temps et échecs par ordonnance"),
    code("""par_ordonnance if par_ordonnance is not None else None"""),
    md("""## 4. Lecture brute d'une ordonnance

La trace complète (lecture JSON, candidats proposés, choix et raison) est aussi enregistrée dans `results/run-*.jsonl`."""),
    code("""import json
if engines and details:
    print(json.dumps(details[0], ensure_ascii=False, indent=1, default=str)[:4000])"""),
]
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, "banc_essai.ipynb")
print("banc_essai.ipynb écrit")
