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

# Modèles de vision open-weight sur la machine GPU (Ollama / vLLM), en Algérie
# SYNAPSE_LOCAL_URL=http://localhost:11434/v1   SYNAPSE_LOCAL_MODEL="qwen3-vl:8b,qwen3-vl:30b"
# SYNAPSE_LOCAL_STRUCTURED=0 si le serveur refuse la sortie JSON par schéma (le JSON est alors demandé dans la consigne)
# SYNAPSE_LOCAL_THINK=1 pour laisser les modèles « raisonner » (désactivé par défaut : beaucoup plus lent)
from synapse_bench.engines.openai_compat import OpenAICompatEngine
URL = os.environ.get("SYNAPSE_LOCAL_URL", "")
STRUCT = os.environ.get("SYNAPSE_LOCAL_STRUCTURED", "1") != "0"
THINK = os.environ.get("SYNAPSE_LOCAL_THINK", "0") == "1"
if URL and os.environ.get("SYNAPSE_LOCAL_MODEL"):
    for m in os.environ["SYNAPSE_LOCAL_MODEL"].split(","):
        engines.append(OpenAICompatEngine(URL, m.strip(), structured=STRUCT, think=THINK))

# Deux temps : OCR local (ex. deepseek-ocr) puis structuration du TEXTE par un modèle texte local (ex. qwen3-coder:30b)
# SYNAPSE_OCR_MODEL=deepseek-ocr  SYNAPSE_OCR_PROMPT="Free OCR."  SYNAPSE_STRUCTURER_MODEL=qwen3-coder:30b
# Sans SYNAPSE_STRUCTURER_MODEL, le texte est structuré par le premier moteur configuré (attention : Claude = hors d'Algérie).
if os.environ.get("SYNAPSE_OCR_MODEL"):
    from synapse_bench.engines.two_stage import TwoStageEngine
    ocr = OpenAICompatEngine(os.environ.get("SYNAPSE_OCR_URL", URL), os.environ["SYNAPSE_OCR_MODEL"], structured=False,
                             think=THINK)
    if os.environ.get("SYNAPSE_STRUCTURER_MODEL"):
        structurer = OpenAICompatEngine(URL, os.environ["SYNAPSE_STRUCTURER_MODEL"], structured=STRUCT, think=THINK)
    else:
        structurer = engines[0] if engines else None
    if structurer is not None:
        engines.append(TwoStageEngine(ocr, structurer, os.environ.get("SYNAPSE_OCR_PROMPT")))

print("Moteurs :", [e.name for e in engines] or "aucun (définir les variables d'environnement)")"""),
    md("""### Diagnostic des moteurs locaux

Quatre appels courts par moteur local : texte simple, raisonnement coupé, sortie JSON par schéma, image.
Une ligne `ok = False` indique l'option à changer (voir le README : `SYNAPSE_LOCAL_STRUCTURED=0`, `SYNAPSE_LOCAL_THINK=1`)."""),
    code("""from synapse_bench.diagnostic import diagnostic
for e in engines:
    if e.name.startswith("local:"):
        print(e.name)
        display(diagnostic(e))"""),
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
    md("### Échecs de lecture\n\nSi la colonne `lu` est vide partout, la lecture a échoué : le message est ici."),
    code("""if par_ordonnance is not None:
    echecs = par_ordonnance[par_ordonnance.erreur.notna()][["moteur", "ordonnance", "secondes", "erreur"]]
    display(echecs if len(echecs) else "Aucun échec de lecture.")"""),
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
