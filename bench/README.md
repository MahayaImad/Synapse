# Banc d'essai — lecture des ordonnances (TEMPORAIRE)

Outil jetable pour **choisir** le moteur de lecture (Claude API, modèle open-weight sur serveur en Algérie,
petit modèle « mobile », ou OCR local + structuration du texte). Ce n'est pas du code de production.

## Données de santé : règles

- Les ordonnances réelles vont dans `bench/data/` (**ignoré par git**), jamais ailleurs dans le dépôt.
- Chaque image a un fichier YAML avec ses **masques** (patient, médecin, cachet, téléphone) et, de préférence,
  la **zone** des lignes de médicaments. L'image envoyée est recalculée à partir des pixels : masques gravés,
  recadrage, métadonnées (EXIF, GPS) supprimées.
- Un moteur hors d'Algérie (Claude API) **refuse** toute ordonnance sans masque ni zone.
- Ne partagez pas d'ordonnance non masquée dans une session Claude Code cloud : c'est déjà un transfert.

## Installation

```bash
cd bench
uv sync
uv run python examples/make_examples.py      # 3 ordonnances FICTIVES pour essayer
uv run pytest                                # 16 tests, sans réseau
```

## Annoter une ordonnance réelle

`data/ORD-001.jpg` + `data/ORD-001.yaml` :

```yaml
type: manuscrite                # ou imprimee
masques: [[0.0, 0.0, 1.0, 0.18], [0.55, 0.80, 1.0, 0.95]]   # x0, y0, x1, y1 en fractions (0–1)
zone: [0.0, 0.18, 1.0, 0.80]    # seule zone envoyée (lignes de médicaments)
attendu:
  age: null
  poids: null
  lignes:
    - produit_id: 24914b95-166d-4232-9f4c-22cae90ddd21   # id dans la nomenclature (synapse-admin search), ou null
      marque: DOLIPRANE
      dosage: 1000MG
      forme: COMPRIME
      posologie: {dose_par_prise: 1, unite: cp, frequence: 3/j, duree: 5 j, voie: orale}
```

Le notebook (section 2) montre côte à côte l'original et l'image envoyée : vérifiez chaque masque avant d'exécuter.

## Moteurs (variables d'environnement)

| Moteur | Variables |
| --- | --- |
| Claude (API Anthropic) | `ANTHROPIC_API_KEY` (ou `ant auth login` + `SYNAPSE_CLAUDE=1`), `SYNAPSE_CLAUDE_MODEL` (défaut `claude-opus-5-5`) |
| Open-weight sur la machine GPU | `SYNAPSE_LOCAL_URL=http://localhost:11434/v1` (Ollama), `SYNAPSE_LOCAL_MODEL=qwen3-vl:8b,qwen3-vl:30b`, `SYNAPSE_LOCAL_STRUCTURED=0` si le serveur refuse le JSON par schéma, `SYNAPSE_LOCAL_THINK=1` pour réactiver le raisonnement (désactivé par défaut) |
| OCR local + structuration du texte | `SYNAPSE_OCR_MODEL=deepseek-ocr`, `SYNAPSE_OCR_PROMPT="Free OCR."`, `SYNAPSE_STRUCTURER_MODEL=qwen3-coder:30b` (modèle texte local ; sans lui, le premier moteur configuré structure le texte) |

Serveurs sur la machine GPU (exemples, à adapter à la mémoire disponible) :

```bash
vllm serve Qwen/Qwen3-VL-32B-Instruct-FP8 --max-model-len 16384 --port 8000
ollama run qwen3-vl:8b        # alternative plus simple (base_url http://GPU:11434/v1)
```

Vérifiez la licence de chaque modèle pour un usage commercial avant de le retenir.

**Raisonnement (« thinking »)** : désactivé par défaut pour les moteurs locaux, en envoyant
`reasoning_effort: "none"` (accepté par Ollama et llama.cpp sur `/v1`). Il multiplie le temps de lecture
(plusieurs minutes par ordonnance) sans améliorer la transcription. Les balises `<think>…</think>` qu'un modèle
laisserait dans sa réponse sont retirées avant la lecture du JSON. Pour comparer, relancez avec
`SYNAPSE_LOCAL_THINK=1`. Si un serveur refuse ce champ (erreur 400), mettez `SYNAPSE_LOCAL_THINK=1`.

## Lancer

```bash
cd bench
SYNAPSE_DATA=data SYNAPSE_LOCAL_URL=http://GPU:8000/v1 SYNAPSE_LOCAL_MODEL=Qwen/Qwen3-VL-32B-Instruct-FP8 \
  uv run jupyter lab banc_essai.ipynb
```

Le notebook affiche : la synthèse par moteur et par type face aux cibles du cahier des charges, un graphique
exact / incertain / erreur, le détail ligne par ligne (vert, jaune, rouge), le temps par ordonnance, et
enregistre la trace complète dans `results/run-*.jsonl` (ignoré par git).

## Ce que mesure le banc

- **exact** : le produit choisi est celui attendu (identifiant de la nomenclature).
- **incertain** : le moteur a répondu « incertain », a cité un produit hors de la liste, ou a manqué la ligne.
- **erreur** : mauvais produit choisi avec assurance — le pire cas, doit rester à 0.
- **posologie_ok** : dose par prise, unité, fréquence, durée et voie identiques après normalisation.
- **doses inventées** : une dose donnée là où l'ordonnance n'en écrit pas (ou sur une ligne inventée) — cible 0.
- Le choix du produit se fait toujours **parmi des produits réels** proposés par la recherche Synapse.

Le notebook est généré par `make_notebook.py` (le modifier là, puis relancer le script).
