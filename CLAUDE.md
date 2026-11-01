# Synapse — instructions pour Claude

Synapse aide le pharmacien d'officine à lire une ordonnance, à retrouver chaque
médicament dans la nomenclature algérienne et à repérer les risques avant la
délivrance. Référence complète : `Cahier des charges` (racine du dépôt).

## Règles non négociables (sécurité clinique)

- Le LLM **lit et reformule** uniquement. Identification produit, interactions et
  doses sont décidées par des données sourcées et des règles déterministes.
- Aucune dose ni interaction produite par un LLM ; chaque alerte cite sa source et
  sa version ; le pharmacien valide toujours. En cas de doute : « incertain ».
- Seule la photo masquée (nom du patient caché sur le téléphone) quitte l'appareil ;
  données de santé hébergées en Algérie ; photos non conservées par défaut.

## Stack cible

- App : Flutter (Android puis iOS), nomenclature embarquée en SQLite + FTS (hors connexion).
- Backend : Python / FastAPI, Redis (files), PostgreSQL (pg_trgm, unaccent, pgvector).
- Interface FR + AR (RTL), utilisable d'une main, texte agrandissable.

## Skills et plugins du projet

Installés dans le dépôt pour être disponibles à chaque session :

| Outil | Emplacement | Usage dans Synapse |
| --- | --- | --- |
| **Task Observer** | `.claude/skills/task-observer` | Observer chaque tâche, consigner corrections et méthodes, améliorer les skills |
| **Find Skills** | `.claude/skills/find-skills` | Chercher un skill existant avant de réinventer (Flutter, FastAPI, OCR…) |
| **Superpowers** | plugin `superpowers@superpowers-dev` | Brainstorming → plan → TDD → revue → vérification avant de conclure |
| **Impeccable** | plugin `impeccable@impeccable` | Qualité UI/UX de l'app et du back-office (`/impeccable audit`, `polish`, `critique`) |
| **Claude-Mem** | plugin `claude-mem@thedotmack` | Mémoire persistante entre sessions (`mem-search`) |

Les plugins sont déclarés dans `.claude/settings.json` et s'installent au démarrage
d'une session (accepter la confiance des marketplaces si demandé).

### Mode opératoire

1. **Avant le premier appel d'outil de chaque session**, invoquer le skill
   `task-observer` (activation session-start).
2. Pour toute nouvelle fonctionnalité : `superpowers:brainstorming` puis
   `superpowers:writing-plans`, puis implémentation en TDD
   (`superpowers:test-driven-development`) et `superpowers:verification-before-completion`.
3. Pour tout écran (Flutter ou back-office) : passer par `impeccable` (gérer le RTL arabe).
4. Avant de créer un outil maison, utiliser `find-skills`.
5. Consulter la mémoire `claude-mem` (`mem-search`) pour retrouver les décisions passées.
