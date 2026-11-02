---
name: Synapse
description: Nomenclature algérienne des médicaments au comptoir de l'officine, hors connexion, statut d'abord.
colors:
  azure-seed: "#4A90E2"
  primary: "#2F78C4"
  on-primary: "#FFFFFF"
  primary-container: "#D4E3FF"
  on-primary-container: "#204876"
  surface: "#F3F5F8"
  on-surface: "#191C20"
  on-surface-variant: "#43474E"
  surface-container-lowest: "#FFFFFF"
  surface-container-low: "#F8FAFC"
  outline-variant: "#E3E8EF"
  field-fill: "#DCE9F8"
  error: "#BA1A1A"
  error-container: "#FFDAD6"
  on-error-container: "#93000A"
  warning: "#6E5D0E"
  warning-container: "#FAE287"
  on-warning-container: "#544600"
  secondary-container: "#D8E3F8"
  on-secondary-container: "#3C4758"
  inverse-surface: "#2E3035"
  on-inverse-surface: "#EFF0F7"
  primary-dark: "#8AB8F0"
  on-primary-dark: "#0B2E55"
  surface-dark: "#1B1F25"
  on-surface-dark: "#E3E6EB"
  on-surface-variant-dark: "#C3C6CF"
  surface-container-lowest-dark: "#262B33"
  surface-container-low-dark: "#222730"
  outline-variant-dark: "#353B45"
  field-fill-dark: "#2C3A4D"
  error-dark: "#FFB4AB"
  error-container-dark: "#93000A"
  on-error-container-dark: "#FFDAD6"
  warning-container-dark: "#544600"
  on-warning-container-dark: "#FAE287"
  secondary-container-dark: "#3C4758"
  on-secondary-container-dark: "#D8E3F8"
typography:
  headline:
    fontFamily: "Nunito, sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.33
    letterSpacing: "0px"
  title-section:
    fontFamily: "Nunito, sans-serif"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: 1.27
    letterSpacing: "0px"
  title-bar:
    fontFamily: "Nunito, sans-serif"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: 1.27
    letterSpacing: "0px"
  title:
    fontFamily: "Nunito, sans-serif"
    fontSize: "16px"
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0.15px"
  body:
    fontFamily: "Nunito, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0.5px"
  body-strong:
    fontFamily: "Nunito, sans-serif"
    fontSize: "16px"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "0.5px"
  body-numeric:
    fontFamily: "Nunito, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0.5px"
    fontFeature: "'tnum' 1"
  body-secondary:
    fontFamily: "Nunito, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.43
    letterSpacing: "0.25px"
  body-secondary-numeric:
    fontFamily: "Nunito, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.43
    letterSpacing: "0.25px"
    fontFeature: "'tnum' 1"
  body-small:
    fontFamily: "Nunito, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.33
    letterSpacing: "0.4px"
  label-large:
    fontFamily: "Nunito, sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: 1.43
    letterSpacing: "0.1px"
    fontFeature: "'tnum' 1"
  label:
    fontFamily: "Nunito, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.33
    letterSpacing: "0.5px"
rounded:
  sm: "8px"
  lg: "16px"
  full: "9999px"
spacing:
  hair: "2px"
  xs: "4px"
  card-gap: "6px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  search-field:
    backgroundColor: "{colors.field-fill}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    height: "56px"
  search-field-dark:
    backgroundColor: "{colors.field-fill-dark}"
    textColor: "{colors.on-surface-dark}"
  card:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "16px"
  card-dark:
    backgroundColor: "{colors.surface-container-lowest-dark}"
    textColor: "{colors.on-surface-dark}"
  result-row:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-strong}"
    padding: "8px 16px"
  status-chip-retired:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.on-error-container}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "4px 8px"
  status-chip-not-renewed:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.on-warning-container}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "4px 8px"
  status-chip-active:
    backgroundColor: "{colors.secondary-container}"
    textColor: "{colors.on-secondary-container}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "4px 8px"
  status-banner-retired:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.on-error-container}"
    typography: "{typography.title}"
    rounded: "{rounded.lg}"
    padding: "16px"
  status-banner-not-renewed:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.on-warning-container}"
    typography: "{typography.title}"
    rounded: "{rounded.lg}"
    padding: "16px"
  section-title:
    textColor: "{colors.on-surface}"
    typography: "{typography.title-section}"
    padding: "16px 16px 4px 16px"
  field-row:
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    padding: "8px 16px"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-large}"
    rounded: "{rounded.full}"
    height: "40px"
    padding: "0 24px"
  button-primary-dark:
    backgroundColor: "{colors.primary-dark}"
    textColor: "{colors.on-primary-dark}"
  button-text:
    textColor: "{colors.primary}"
    typography: "{typography.label-large}"
    rounded: "{rounded.full}"
    height: "40px"
    padding: "0 12px"
  text-field:
    backgroundColor: "{colors.field-fill}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
  snackbar:
    backgroundColor: "{colors.inverse-surface}"
    textColor: "{colors.on-inverse-surface}"
    typography: "{typography.body-secondary}"
---

# Design System: Synapse

## Overview

**Creative North Star: "Le registre au comptoir"**

Synapse est un outil de service public qu'on consulte debout, téléphone dans une main et ordonnance dans l'autre. Le système visuel reprend le vocabulaire familier des applications administratives algériennes (référence El Hana fournie par l'utilisateur) : fond gris clair, cartes blanches arrondies qui regroupent l'information, bleu azur pour tout ce qui agit ou désigne, champs remplis bleu pâle avec icône en tête, une icône Material devant chaque information de la fiche. C'est une inspiration de grammaire, pas d'identité : aucun logo, nom ni couleur propre à la CNAS.

La hiérarchie est réglementaire avant d'être esthétique. Le statut d'un produit (retiré, non renouvelé, en vigueur) est l'information la plus visible de chaque ligne et de chaque fiche ; le reste de l'interface est volontairement calme, bleu et gris, pour que le rouge d'erreur et l'ambre harmonisé gardent toute leur force. La densité est celle d'un registre : une ligne par présentation, marque en gras, dosage · forme · conditionnement en chiffres tabulaires, séparateurs fins.

Le mode sombre est un gris ardoise (pas un noir pur) : les cartes y sont plus claires que le fond, le bleu est éclairci, les statuts gardent leurs rôles. Tout le texte suit la taille de police système (vérifié à 130 %).

**Key Characteristics:**
- Fond gris clair, cartes blanches de 16 dp à ombre douce ; en sombre, cartes ardoise plus claires sans ombre.
- Un seul accent, le bleu azur, pour actions, icônes et focus.
- Le statut est porté par la couleur de conteneur (erreur, ambre harmonisé, tonal neutre) et toujours par un libellé texte.
- Nunito arrondie pour tout le texte, chiffres tabulaires pour dosages, codes et numéros.
- Titre de barre centré ; pas de FAB ; navigation par pile d'écrans.

## Colors

Un bleu azur sur des neutres gris-bleu, et trois couleurs de statut qui n'ont pas d'autre usage. Les rôles viennent d'un `ColorScheme.fromSeed` sur le bleu azur (#4A90E2), corrigé à la main pour le primaire, les surfaces et les séparateurs ; le jaune-ambre est une `ThemeExtension` harmonisée avec le primaire.

### Primary
- **Bleu azur d'action** (`primary`, sombre `primary-dark`) : boutons pleins, icônes de tête des champs et des lignes d'information, loupe du champ de recherche, curseur et focus. Plus profond que la graine (#4A90E2) en clair pour tenir le contraste sur blanc ; éclairci en sombre.
- **Bleu pâle de champ** (`field-fill`, sombre `field-fill-dark`) : remplissage du champ de recherche et des champs de saisie. Seul usage de cette teinte.

### Secondary
- **Ardoise tonale** (`secondary-container` / `on-secondary-container`) : uniquement l'étiquette « En vigueur » de la fiche produit. Neutre à dessein : l'état normal ne crie pas.

### Tertiary
- **Rouge de retrait** (`error-container` / `on-error-container`, `error`) : étiquette et bandeau « Retiré », libellé « Stupéfiant » en colonne de statut (`error`, graisse 600), icône d'erreur au démarrage.
- **Ambre harmonisé** (`warning-container` / `on-warning-container`) : étiquette et bandeau « Non renouvelé ». Calculé depuis #B8860B harmonisé avec le primaire, puis tonal spot (`StatusColors.forScheme`).

### Neutral
- **Gris de comptoir** (`surface`, sombre `surface-dark` ardoise) : fond de tous les écrans (scaffold).
- **Blanc de carte** (`surface-container-lowest`, sombre `surface-container-lowest-dark`) : cartes et barre d'application.
- **Encre** (`on-surface`) : texte principal ; **encre secondaire** (`on-surface-variant`) : libellés de champ, sous-titres, version de la nomenclature, pied de source, icônes des états vides.
- **Filet** (`outline-variant`) : séparateurs de 1 dp entre les lignes, en retrait de 16 dp de chaque côté.
- **Inverse** (`inverse-surface` / `on-inverse-surface`) : snackbars de mise à jour.

### Named Rules
**The Reserved Amber Rule.** L'ambre et toute teinte orangée sont réservés au statut « non renouvelé ». Aucun orange décoratif, aucun accent chaud ailleurs (l'orange de la référence El Hana n'est pas repris).

**The Status Colour Rule.** Rouge = retiré (et stupéfiant), ambre = non renouvelé, ardoise tonale = en vigueur. Ces conteneurs ne servent à rien d'autre, et la couleur n'est jamais seule : un libellé texte l'accompagne toujours.

**The One Accent Rule.** Le bleu azur est le seul accent. Pas de deuxième couleur de marque, pas de dégradé.

## Typography

**Display Font:** aucune (pas de rôle display)
**Body Font:** Nunito (400, 600, 700 embarquées, OFL), repli sans-serif
**Label/Mono Font:** Nunito, avec chiffres tabulaires (`tnum`) pour les données

**Character:** Une sans-serif arrondie, amicale et lisible, qui adoucit des données ministérielles en MAJUSCULES abrégées (« SOL. INJ. », « B/30 ») sans les rendre froides.

Les tailles sont celles de l'échelle Material 3 de Flutter, en dp logiques, multipliées par la taille de police système de l'utilisateur. Les rôles à 500 sont rendus par la graisse embarquée la plus proche (seules 400, 600 et 700 sont fournies).

### Hierarchy
- **Headline** (`headline`, headlineSmall en 700) : nom de marque en tête de fiche produit, une fois par écran.
- **Title section** (`title-section`, titleLarge en 600) : titre de chaque carte de section (« Informations », « Équivalents en vigueur — même dosage »…), marqué comme en-tête pour les lecteurs d'écran.
- **Title bar** (`title-bar`, titleLarge en 400) : titre centré de la barre d'application.
- **Title** (`title`, titleMedium) : titre du bandeau de statut, titre des états vides.
- **Body** (`body`, bodyLarge) : valeurs des champs, texte saisi ; **body-strong** (700) : marque dans chaque ligne de résultat.
- **Body secondary** (`body-secondary`, bodyMedium) : sous-titre des lignes, détails du bandeau, notes, avertissement.
- **Body small** (`body-small`) : pied « source : nomenclature … ».
- **Label large** (`label-large`) : boutons et en-têtes de groupe de dosage (tabulaires).
- **Label** (`label`, labelMedium) : étiquettes de statut, libellés de champ, version de la nomenclature.

### Named Rules
**The Tabular Data Rule.** Dosage, code DCI, conditionnement, numéro d'enregistrement et groupes de dosage utilisent les chiffres tabulaires. Une barre « / » n'est jamais suivie d'une coupure de ligne (« B/10 », « 5MG/ML » restent entiers).

**The Ministry Text Rule.** Les données de nomenclature s'affichent telles que publiées (majuscules, abréviations) ; seule l'interface est en casse normale. Jamais de capitales forcées par le style.

## Layout

Une seule colonne, pleine largeur, faite pour le pouce. Gouttière latérale de 16 dp pour les cartes et le champ de recherche ; 6 dp de marge verticale par carte (12 dp entre deux cartes). Rythme interne : 16 dp de padding de carte et d'écart icône-texte, 8 dp entre lignes de champ, 4 et 2 dp pour les micro-écarts (libellé → valeur). Les états vides sont centrés avec 32 dp de marge latérale et 48 dp au-dessus ; l'erreur de démarrage utilise 24 dp.

Écran de recherche : champ en haut (focus au lancement), version de la nomenclature dessous (retrait de 28 dp, aligné sur le texte du champ), puis une seule carte de résultats défilante qui ferme le clavier au glissement. Fiche produit : barre d'application épinglée au nom du produit, carte d'identité, bandeau de statut et équivalents en vigueur si le produit n'est pas en vigueur, puis informations, équivalents, autres dosages, pied de source. Tous les espacements sont directionnels (`EdgeInsetsDirectional`) pour l'arabe RTL à venir.

## Elevation & Depth

Hybride, et léger. En clair, les cartes blanches portent une ombre douce (élévation 1,5, ombre noire à 20 %, sans teinte de surface) qui les détache du fond gris. En sombre, l'élévation est nulle : la profondeur vient du seul écart tonal entre le fond ardoise et des cartes plus claires. Le champ de recherche est plat (élévation 0) dans les deux modes ; la barre d'application ne prend une élévation de 1 qu'une fois du contenu défilé dessous.

### Shadow Vocabulary
- **Ombre de carte** (élévation Material 1,5, `shadowColor` #000000 à 20 %) : toutes les cartes en mode clair.
- **Ombre de défilement** (élévation 1 sous la barre) : seulement quand du contenu passe sous la barre d'application.

### Named Rules
**The Flat Field Rule.** Les champs ne portent jamais d'ombre : ils se distinguent par leur remplissage bleu pâle, les cartes par leur blanc et leur ombre.

## Shapes

Des coins doux et réguliers. Rayon de 16 dp pour tout ce qui contient (cartes, bandeaux de statut, champ de recherche, champs de saisie) ; 8 dp pour les petites étiquettes de statut ; pilule complète pour les boutons (forme Material 3 par défaut). Aucune bordure : les champs remplis n'ont pas de trait (`BorderSide.none`), les cartes n'ont pas de contour, seuls des filets de 1 dp séparent les lignes à l'intérieur d'une carte.

## Components

### Buttons
- **Shape:** pilule (rayon complet), hauteur Material 3 de 40 dp.
- **Primary:** bouton plein bleu azur, texte blanc (« Vérifier maintenant », « Réessayer »), avec icône en tête quand l'action en a une ; pendant l'action, l'icône devient un indicateur circulaire de 18 dp et le bouton est désactivé.
- **Text:** bouton texte bleu pour l'action secondaire d'une carte (« Enregistrer »), aligné en fin de ligne.

### Chips
- **Style:** étiquette de statut tonale, rayon 8 dp, padding 4 × 8 dp, texte `label`. Rouge pour « Retiré », ambre pour « Non renouvelé », ardoise tonale pour « En vigueur ».
- **State:** non interactive. « En vigueur » n'apparaît que sur la fiche produit ; dans les listes, un produit en vigueur n'a pas d'étiquette. Annoncée « Statut : … » aux lecteurs d'écran.

### Cards / Containers
- **Corner Style:** 16 dp.
- **Background:** `surface-container-lowest` (blanc ; ardoise claire en sombre).
- **Shadow Strategy:** ombre de carte en clair, aucune en sombre (voir Elevation & Depth).
- **Border:** aucune.
- **Internal Padding:** 16 dp ; marge 16 dp horizontal, 6 dp vertical.
- **Section card:** carte titrée (`title-section`, padding 16/16/16/4) qui regroupe une partie de la fiche, suivie de ses lignes et de 8 dp en bas.

### Inputs / Fields
- **Search field:** rempli bleu pâle, rayon 16 dp, plat, loupe bleue en tête, bouton d'effacement et menu (« À propos ») en fin ; texte `body`, indice en encre secondaire. Focus au lancement.
- **Text field:** même remplissage et même rayon, sans trait, icône bleue en tête, libellé flottant, texte d'aide dessous ; l'erreur s'affiche en texte d'erreur sous le champ.

### Navigation
- Barre d'application blanche, titre centré (`title-bar`), bouton retour par défaut ; sur la fiche, barre épinglée au nom du produit. Pas de barre de navigation inférieure ni de FAB : recherche → fiche → équivalent, en pile.

### Result Row
La ligne de registre : marque en `body-strong` sur une ligne (ellipse), sous-titre « dosage · forme · conditionnement » en chiffres tabulaires sur deux lignes au plus. La colonne de droite est réservée au statut ; un produit en vigueur la laisse vide, sauf s'il est stupéfiant (libellé « Stupéfiant » en rouge `error`, 600). Les lignes sont groupées dans une carte et séparées par des filets en retrait de 16 dp. Toute la ligne est cliquable.

### Status Banner
Sur la fiche d'un produit non en vigueur, juste sous la carte d'identité : carte pleine (sans ombre) dans le conteneur du statut, rayon 16 dp, padding 16 dp, icône en tête (« block » pour retiré, « history » pour non renouvelé), titre `title` (« Retiré le JJ/MM/AAAA », « Décision d'enregistrement non renouvelée ») et détails de retrait en `body-secondary`. Suivi immédiatement de la section « Équivalents en vigueur — même dosage ».

### Field Row
Icône Material bleue de 24 dp en tête (contour, « outlined »), 16 dp d'écart, puis libellé `label` en encre secondaire et valeur `body` dessous (chiffres tabulaires pour les données numériques). Ligne fusionnée pour les lecteurs d'écran, icône exclue.

### States
- **Recherche vide :** icône « manage_search » de 48 dp en encre secondaire, aide « Marque, DCI, code DCI ou laboratoire » centrée.
- **Aucun résultat :** icône « search_off », titre « Aucun produit pour « … » », aide pour vérifier l'orthographe ou chercher par DCI.
- **Produit disparu :** barre vide et phrase `body` indiquant que le produit ne figure plus dans la nomenclature de la version courante.
- **Erreur de démarrage :** icône d'erreur rouge de 48 dp, titre `title-bar`, détail en encre secondaire, bouton plein « Réessayer » ; jamais un chargement sans fin.
- **Préparation :** indicateur circulaire centré et une phrase.
- **Mises à jour :** snackbar inverse ; en arrière-plan, seule une mise à jour installée est signalée ; une vérification manuelle annonce toujours son issue (à jour, attente Wi-Fi, désactivée, échec avec maintien de la nomenclature installée).

## Do's and Don'ts

### Do:
- **Do** montrer le statut avant tout le reste : étiquette dans la colonne de droite des listes, étiquette et bandeau en tête de fiche.
- **Do** regrouper l'information dans des cartes de 16 dp sur le fond gris, avec 16 dp de gouttière.
- **Do** mettre une icône Material bleue de 24 dp devant chaque information de fiche.
- **Do** utiliser les chiffres tabulaires pour dosages, codes et numéros, et empêcher la coupure après « / ».
- **Do** lire chaque couleur dans le thème (`ColorScheme`, `StatusColors`, `FieldColors`) pour que le mode sombre suive.
- **Do** utiliser des espacements directionnels et laisser le texte suivre la taille de police système.
- **Do** citer la version de la nomenclature sous la recherche et en pied de fiche.

### Don't:
- **Don't** utiliser l'ambre ou l'orange ailleurs que pour « non renouvelé ».
- **Don't** mettre autre chose que le statut ou « Stupéfiant » dans la colonne de droite d'une ligne de résultat (liste I / II restent dans la fiche).
- **Don't** reprendre le logo, le nom, les couleurs propres ou toute identité de la CNAS ou d'El Hana.
- **Don't** signaler un statut par la couleur seule, sans libellé.
- **Don't** ajouter d'ombre aux champs, de bordure aux cartes, ni de FAB.
- **Don't** forcer les capitales par le style ou réécrire les libellés de la nomenclature.
