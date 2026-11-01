# Conception — Import de la nomenclature et recherche hors connexion

Date : 2026-11-01 · Statut : en attente d'approbation · Phase 1, sous-projet 1

## 1. Intention

Toute la phase 1 (liaison des produits lus sur l'ordonnance, fiche produit,
recherche hors connexion) repose sur une nomenclature nationale propre,
versionnée et à jour. Chaque mois, le ministère publie un fichier Excel ;
Synapse doit l'intégrer **sans erreur silencieuse** et le livrer aux
téléphones sans effort pour le pharmacien.

Ce sous-projet livre l'outil d'administration en ligne de commande qui
importe le fichier, montre les changements, enregistre les décisions de
l'admin et publie le fichier de nomenclature embarqué dans l'app, ainsi
qu'une commande de recherche qui prouve la recherche hors connexion.

## 2. Objectifs, non-objectifs, anti-objectifs

**Objectifs**
- Importer n'importe quel fichier mensuel du ministère (formats 2024 à 2026
  constatés) sans adaptation manuelle du fichier.
- Comparer à la version en vigueur et classer chaque écart.
- Faire trancher par l'admin les cas douteux, avec trace écrite (audit).
- Conserver l'historique complet de toutes les versions.
- Publier un fichier SQLite autonome avec recherche plein texte, et son
  manifeste, prêt à être embarqué par l'app Flutter.
- Commande `search` sur ce fichier : < 300 ms par requête.

**Non-objectifs (sous-projets suivants)**
- Back-office web, app Flutter, distribution réelle aux téléphones.
- Téléchargement automatique depuis miph.gov.dz.
- Pivot des substances, classes ATC, interactions, posologie.
- Tout usage de LLM.

**Anti-objectifs** (échec même si « ça marche »)
- Fusionner à tort deux produits différents, ou en scinder un sans le dire.
- Perdre une version ou une décision passée.
- Modifier une donnée sans trace (qui, quand, pourquoi).
- Publier une version qui contient des cas non tranchés.

## 3. Constats sur les données (5 fichiers, août 2024 → août 2026)

- **3 feuilles** : nomenclature en vigueur (~5 400 lignes), non renouvelés
  (~1 500), retraits (~2 700, avec date et motif de retrait).
- **En-têtes variables** : première cellule « N° » ou « N » ; ligne
  d'en-tête entre 10 et 16 ; « COND » ou « CONDITIONNEMENT » ; la feuille
  Retraits n'a ni OBS ni date d'enregistrement finale ; titres de feuille
  avec espaces. → Lecture **par nom de colonne normalisé**, jamais par position.
- **Valeurs saisies à la main** : LISTE en 10 graphies (« Liste I »,
  « lISTE I », « LISTE I ␠ », vide…), P1/P2 avec « 0FF », « HOP* », espaces.
- **Numéro d'enregistrement** `LLL/FF S NNN/AA[/RR]` : labo, code DCI
  (famille, sous-famille, numéro de molécule-forme), année initiale, année
  de renouvellement facultative. Quelques numéros mal saisis
  (`001/09 H 178 20`, `528/04 B 035/  `).
- **Le renouvellement change le numéro** (`077/01 A 003/17` →
  `077/01 A 003/17/24`). Comparer sur le numéro complet donne 863 ajouts /
  564 suppressions entre déc. 2024 et avril 2026 ; sur la **racine**
  (labo + code + année initiale) : 450 / 152.
- **Une décision couvre parfois plusieurs présentations** (NOBAC fraise et
  menthe, LYANA et YASMINE, deux conditionnements de RAPIFEN).
- **Changements de titulaire** : GOAGIL-VII (labo 640) disparaît, COAGIL-VII
  (labo 003, même code DCI) existe.
- **Corrections silencieuses** entre juin et août 2026, à racine égale :
  119 conditionnements, 6 marques, 6 dosages.

## 4. Approches envisagées

| Approche | Résumé | Arbitrage |
| --- | --- | --- |
| **A — retenue** | PostgreSQL source de vérité, validation par fichier de décisions, publication SQLite | Un peu plus d'installation ; aucun travail jeté quand le back-office web arrivera ; le fichier de décisions sert de journal d'audit |
| B | SQLite partout | Démarrage plus rapide, mais migration, recherche floue (pg_trgm) et historique à refaire |
| C | Comme A, validation par questions dans le terminal | Ingérable au-delà de quelques cas, aucune trace écrite |

Choix de l'utilisateur : **A**. Admin : l'utilisateur lui-même pour l'instant.

## 5. Conception

### 5.1 Emplacement et outillage

- `backend/` : paquet Python 3.12+, géré par `uv`, CLI `synapse-admin`
  (Typer), tests `pytest`.
- PostgreSQL 16 (Docker Compose fourni ; un PostgreSQL local fonctionne aussi),
  extensions `pg_trgm` et `unaccent`. Schéma par migrations (Alembic).
- Fichiers sources Excel : non versionnés dans git ; leur empreinte SHA-256,
  nom et date d'import sont enregistrés en base. Des extraits réduits servent
  de jeux de test, eux versionnés.

### 5.2 Commandes

```
synapse-admin import <fichier.xlsx> --version 2026-08
synapse-admin review 2026-08          # rapport + fichier de décisions
synapse-admin publish 2026-08         # refuse si une décision manque
synapse-admin search "augmentin 1g" [--fichier nomenclature-2026-08.sqlite]
synapse-admin status                  # versions, en vigueur, brouillons
```

### 5.3 Lecture du fichier

1. Repérer chaque feuille par son titre normalisé : `nomenclature…` → en
   vigueur, `non renouv…` → non renouvelé, `retrait…` → retiré.
2. Repérer la ligne d'en-tête (première cellule `N°`/`N`), associer chaque
   colonne à un champ par table d'alias (`COND` = `CONDITIONNEMENT`…).
   Colonne obligatoire absente → import refusé avec message clair.
3. Ne garder que les lignes dont la première cellule est un numéro.
4. Conserver **la ligne brute** (JSON) à côté des valeurs normalisées.

### 5.4 Normalisation

| Champ | Règle |
| --- | --- |
| Textes | trim, espaces multiples réduits, majuscules ; casse d'origine gardée dans le brut |
| LISTE | `I`, `II`, `STUPEFIANT`, ou vide (non classé) |
| P1/P2 | booléens `hopital`, `officine` (`HOP*`, `0FF`… reconnus) |
| TYPE | `GE`, `RE`, `BIO`, ou vide |
| STATUT | valeur d'origine (`F`/`I`) conservée telle quelle |
| Dates | date ISO ; texte non convertible → anomalie |
| N° d'enregistrement | décomposé en `labo`, `code_dci`, `famille`, `sous_famille`, `num_molecule`, `annee_initiale`, `annee_renouvellement` ; échec → anomalie, ligne importée quand même |

Chaque anomalie est listée dans le rapport ; aucune n'est corrigée en silence.

### 5.5 Identité d'un produit et comparaison

Un **produit** = une présentation (décision d'enregistrement + marque +
dosage + conditionnement). Il reçoit un identifiant interne stable, qui
traverse les versions. L'app et, plus tard, la liaison des ordonnances
s'appuient sur cet identifiant, jamais sur le numéro d'enregistrement.

Rapprochement de chaque ligne de la nouvelle version avec la version en
vigueur, par paliers ; une ligne déjà rapprochée sort du jeu :

1. **Sûr** — même numéro complet et même présentation normalisée.
2. **Sûr** — même racine (labo + code + année initiale) et même présentation
   (renouvellement).
3. **Sûr** — même racine, un seul candidat de chaque côté, présentation
   légèrement différente (correction de saisie) → « modifié ».
4. **À trancher** — même code DCI et même dosage, marque proche, labo
   différent (changement de titulaire probable) ; ou plusieurs candidats.
5. Sinon : **nouveau** (côté nouvelle version) ou **disparu** (côté ancienne).

Les passages d'une feuille à l'autre (en vigueur → retrait, etc.) sont des
changements de statut d'un même produit. Un produit **disparu** sans
apparaître en retrait ou non-renouvelé est **à trancher**.

Règles complémentaires :
- Au palier 3, un changement de **marque, dosage ou forme** n'est jamais
  « sûr » : il passe **à trancher** (impact clinique). Seuls conditionnement,
  durée de stabilité, OBS, dates, labo (orthographe) passent en « modifié ».
- **Premier import** (aucune version publiée) : tout est « nouveau », aucune
  décision requise.
- **Ordre chronologique** : une version dont la date de référence est
  antérieure à la version publiée est refusée. Les 5 fichiers disponibles
  s'importent dans l'ordre pour constituer l'historique initial.
- **Même produit présent dans deux feuilles** d'un même fichier (ex. en
  vigueur et retiré) → à trancher.
- **Doublon dans une même feuille** (identique après normalisation, ex.
  « VITAMINE C  BGL ») → fusionné, signalé en anomalie.

### 5.6 Rapport et décisions

`review` produit :
- `reports/2026-08.md` : totaux par catégorie (nouveaux, changements de
  statut, modifiés champ par champ, à trancher, anomalies), puis le détail.
- `decisions/2026-08.yaml` : un élément par cas à trancher, avec les
  candidats et un champ `choix` vide (`meme_produit: <id>`, `nouveau`,
  `disparu`), plus `par` et `le`.

L'admin remplit le fichier puis lance `publish`. Le fichier de décisions est
versionné dans git **et** enregistré en base à la publication (audit).

### 5.7 Modèle de données (PostgreSQL)

- `nomenclature_version` : libellé (`2026-08`), date de référence, fichier
  source (nom, SHA-256), état (`brouillon`, `publiee`, `remplacee`), dates.
- `produit` : identifiant stable, date de création.
- `produit_version` : un enregistrement par produit et par version — tous les
  champs normalisés, statut (`en_vigueur`, `non_renouvele`, `retire`), date et
  motif de retrait, ligne brute (JSONB), feuille et numéro de ligne d'origine.
- `ecart` : résultat de la comparaison (catégorie, palier, champs modifiés).
- `decision` : cas, choix, auteur, date, version.
- `anomalie` : version, feuille, ligne, champ, valeur, message.

Index `pg_trgm` sur marque et DCI (recherche floue côté serveur et
rapprochement du palier 4).

### 5.8 Fichier publié pour l'app

`nomenclature-2026-08.sqlite` (autonome, lecture seule) :
- table `produit` : identifiant stable, marque, DCI, code DCI, forme, dosage,
  conditionnement, liste, statut, date et motif de retrait, labo, pays, type,
  hôpital/officine ;
- table `meta` : version, date de référence, SHA-256 de la source, date de
  publication ;
- index FTS5 sur marque, DCI, code DCI et labo, tokenizer `unicode61
  remove_diacritics 2`, recherche par préfixe ;
- index FTS5 `trigram` sur la marque pour les fautes et fragments.

Plus `manifest.json` : version, taille, SHA-256 du fichier publié — c'est ce
que l'app comparera pour se mettre à jour toute seule (sous-projet suivant).

Classement des résultats : produits en vigueur d'abord, puis non renouvelés,
puis retirés (toujours affichés avec leur statut, car une ordonnance peut
citer une ancienne marque).

### 5.9 Tests

- Développement piloté par les tests.
- Extraits réduits des 5 fichiers réels comme jeux d'essai (en-têtes 2024 et
  2026, numéros mal saisis, décision multi-présentations, cas GOAGIL/COAGIL).
- Test de bout en bout sur les vrais fichiers juin → août 2026 (si présents
  localement) : écarts attendus vérifiés, aucune ligne perdue
  (lignes lues = lignes rapprochées + nouvelles + anomalies bloquantes).
- Mesure de performance de `search` sur le fichier publié complet.

## 6. Décisions prises (par l'utilisateur)

- Commencer par l'import de la nomenclature puis la recherche hors connexion.
- Import, vérification et validation faits par l'admin du serveur ; le
  pharmacien ne fait rien, ou un seul bouton (mise à jour auto prévue).
- Admin = l'utilisateur pour l'instant ; outil en ligne de commande d'abord.
- Approche A.

## 7. Choix faits par Claude (à vérifier)

- Les trois feuilles sont importées et publiées, pas seulement la nomenclature
  en vigueur.
- Identifiant produit interne stable plutôt que le numéro d'enregistrement.
- Fichiers Excel sources hors git, tracés par empreinte.
- `STATUT` (`F`/`I`) gardé tel quel, sans interprétation.
- Noms : CLI `synapse-admin`, dossier `backend/`.
- Changement de marque, dosage ou forme sous un même numéro : toujours à
  trancher par l'admin, jamais automatique.
- Import strictement chronologique ; produit présent dans deux feuilles d'un
  même fichier : à trancher.

## 8. Laissé au constructeur

Bibliothèques précises (lecture Excel, YAML), structure interne des modules,
seuils de similarité du palier 4 (à calibrer sur les cas réels, documentés),
format exact du rapport Markdown.
