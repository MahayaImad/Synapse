# Conception — App Synapse : recherche hors connexion et fiche produit

Date : 2026-11-01 · Statut : approuvé le 2026-11-01 · Phase 1, sous-projet 2

## 1. Intention

Au comptoir, le pharmacien doit retrouver en quelques frappes, d'une main et
sans réseau, le produit exact d'une ordonnance, voir sans ambiguïté s'il est
en vigueur, retiré ou non renouvelé, et trouver un équivalent substituable.
Ce sous-projet livre la première version de l'app Android, alimentée par le
fichier SQLite que publie `synapse-admin`, et qui se met à jour seule.

## 2. Objectifs, non-objectifs, anti-objectifs

**Objectifs**
- Recherche hors connexion (marque, DCI, code DCI, labo ; préfixes, accents,
  fautes de frappe) avec les mêmes résultats que `synapse-admin search`.
- Fiche produit : statut en tête, DCI, code DCI, dosage, forme,
  conditionnement, liste I / II / stupéfiant, type, origine, labo et pays,
  disponibilité hôpital / officine, n° d'enregistrement, date et motif de retrait.
- Équivalents de même code DCI : même dosage d'abord, puis les autres dosages
  regroupés ; produit retiré ou non renouvelé → équivalents en vigueur de même
  dosage proposés juste sous le statut.
- Mise à jour automatique de la nomenclature depuis une URL configurable.
- Recherche < 300 ms sur l'appareil.

**Non-objectifs (jalons suivants)**
- Photo d'ordonnance, lecture LLM, interactions, posologie.
- Traduction arabe (chaînes externalisées et mise en page directionnelle dès
  maintenant ; traduction et tests RTL plus tard).
- iOS, tablette dédiée (la mise en page téléphone s'étire proprement).
- Compte utilisateur, vérification du statut de pharmacien, télémétrie.

**Anti-objectifs**
- Un statut retiré ou non renouvelé qui passerait inaperçu.
- Une information affichée qui ne vient pas de la nomenclature, ou sans sa version.
- Une mise à jour qui laisse l'app sans base valide (fichier corrompu, coupure).
- Une app inutilisable hors connexion.

## 3. Approches envisagées

| Approche | Résumé | Arbitrage |
| --- | --- | --- |
| **A — retenue** | `sqlite3` + `sqlite3_flutter_libs` : SQLite récent embarqué (FTS5 + trigram) | Recherche identique sur tous les Android ; ≈ +1,5 Mo d'APK |
| B | `sqflite` (SQLite du système) | APK plus léger, mais le tokenizer trigram manque sur beaucoup d'Android encore en service |
| C | Recherche par le serveur | Contraire à « toujours disponible hors connexion » |

Choix de l'utilisateur : **A**.

## 4. Décisions de l'utilisateur

- Jalon : recherche + fiche + mise à jour automatique.
- Interface en français seulement pour ce jalon.
- Mises à jour : nomenclature embarquée dans l'APK + `manifest.json` lu à une
  URL configurable.
- Appareil principal : téléphone.
- Équivalents : même dosage d'abord.
- Produit retiré / non renouvelé : statut + équivalents en vigueur proposés.
- Direction visuelle : Material 3 standard, finition des apps Google
  (brief : `.impeccable/surfaces/app-lib-main-dart.md`).

## 5. Conception

### 5.1 Écrans

**Recherche (écran d'accueil)**
- Barre de recherche Material 3 en haut, focus et clavier ouverts au
  lancement ; sous-titre « Nomenclature août 2026 ».
- Résultats : une ligne par présentation — marque (titre), dosage · forme ·
  conditionnement (corps), libellé de liste à droite ; chip de statut tonale
  (« Retiré » couleur d'erreur, « Non renouvelé » couleur d'avertissement)
  pour tout produit non en vigueur. Ordre : celui de la recherche de
  référence (en vigueur, non renouvelés, retirés).
- États : vide (aide courte : « Marque, DCI, code DCI ou laboratoire ») ;
  aucun résultat (« Aucun produit pour “…” » + rappel de la version) ;
  base en cours de préparation au premier lancement.
- Recherche à chaque frappe, avec un délai de 120 ms.
- Menu de la barre : « À propos et mises à jour ».

**Fiche produit**
- Barre d'app avec retour (geste Retour système respecté).
- En-tête : marque, dosage, forme.
- Statut si non en vigueur : bandeau en tête (« Retiré le 31/03/2024 —
  retrait par le détenteur pour motif commercial »), puis immédiatement
  « Équivalents en vigueur — même dosage ».
- Informations : DCI, code DCI, conditionnement, liste, type (générique /
  référence / biologique), origine (fabriqué localement / importé), labo et
  pays, hôpital / officine, n° d'enregistrement.
- Équivalents : « Même dosage » (en vigueur d'abord) puis « Autres dosages »
  groupés par dosage ; chaque ligne ouvre sa fiche.
- Pied : « Source : nomenclature nationale, version août 2026 ».

**À propos et mises à jour**
- Version de la nomenclature, date de publication, nombre de produits,
  dernière vérification et son résultat, bouton « Vérifier maintenant ».
- Adresse du manifeste (valeur de build, modifiable ici pour le pilote).
- Mention : outil d'aide à la dispensation, la décision reste au pharmacien.

### 5.2 Données sur l'appareil

- Le fichier `nomenclature-AAAA-MM.sqlite` publié est embarqué comme asset et
  copié au premier lancement dans le stockage de l'app ; ouvert en lecture seule.
- Recherche : portage fidèle de `backend/src/synapse_admin/search.py`
  (jetons sans accents, élisions, FTS5 préfixes, repli trigrammes avec score
  de Dice ≥ 0,5, ordre par statut).
- Équivalents : même `code_dci` ; « même dosage » = dosage égal en ignorant
  les espaces (règle déjà utilisée par le backend).
- **Parité garantie par les tests** : le backend génère un jeu de cas
  (requête → identifiants attendus) sur un fichier publié de test ; l'app
  doit rendre exactement les mêmes résultats.

### 5.3 Mise à jour

1. Au lancement puis toutes les 24 h, si le réseau n'est pas facturé
   à l'usage (Wi-Fi) : lecture de `manifest.json`.
2. Si `version` est postérieure à la version installée : téléchargement dans
   un fichier temporaire, vérification taille + SHA-256, ouverture et
   vérification (`meta.version` = manifeste, `PRAGMA integrity_check`).
3. Remplacement atomique (renommage), réouverture, snackbar
   « Nomenclature mise à jour : septembre 2026 ».
4. Tout échec laisse la base en place ; il est visible dans « À propos ».
   Jamais de retour à une version antérieure.

### 5.4 Architecture

```
app/
  lib/
    main.dart, app.dart            # thème Material 3, routes
    data/                          # base, recherche, équivalents, mise à jour
    ui/search/, ui/product/, ui/about/
    l10n/app_fr.arb                # toutes les chaînes
  assets/nomenclature/             # fichier publié + manifest.json
  test/                            # unitaires, widgets, captures (goldens)
```

- État : `ChangeNotifier` / `ValueListenableBuilder`, sans bibliothèque
  d'état ; navigation `Navigator` standard.
- Thème : `dynamic_color` (Material You) avec repli statique ; thème sombre
  complet ; couleur « non renouvelé » via `ThemeExtension` harmonisée.
- Mise en page directionnelle (`EdgeInsetsDirectional`, `start/end`) pour l'arabe.
- Paquets : `sqlite3`, `sqlite3_flutter_libs`, `path_provider`, `http`,
  `crypto`, `connectivity_plus`, `dynamic_color`, `flutter_localizations`.

### 5.5 Vérification

- Tests unitaires : recherche (parité backend), équivalents, mise à jour
  (manifeste plus récent / identique / plus ancien / SHA faux / fichier
  corrompu / coupure réseau).
- Tests de widgets : recherche, fiche, produit retiré, états vides.
- Captures générées par les tests (goldens) : clair, sombre, police ×1,3.
- APK de debug construit. Pas d'émulateur dans cet environnement : le
  contrôle sur un vrai téléphone reste à faire par l'utilisateur.
- Revue de finition Impeccable puis rédaction de `DESIGN.md` à partir du
  résultat construit.

## 6. Choix faits par Claude (à vérifier)

- Recherche à chaque frappe (120 ms), sans bouton « Rechercher ».
- Mise à jour seulement en Wi-Fi, au lancement et toutes les 24 h ;
  notification discrète (snackbar), pas de dialogue.
- URL du manifeste fixée au build (`--dart-define=SYNAPSE_MANIFEST_URL=…`) et modifiable dans « À propos » pendant le pilote ; vide par défaut tant qu'aucun hébergement n'existe : la mise à jour est alors désactivée et « À propos » le dit.
- Fichier embarqué : la dernière version publiée (`nomenclature/publications/`), copiée dans `app/assets/` par un script ; les tests utilisent un petit fichier généré par le backend.
- Aucune donnée personnelle, aucune télémétrie.
- Dossier `app/` à la racine du dépôt, application `dz.synapse.app`.

## 7. Laissé au constructeur

Structure fine des widgets, choix des icônes Material, texte exact des aides
(dans les limites ci-dessus), stratégie de génération du fichier de test.
