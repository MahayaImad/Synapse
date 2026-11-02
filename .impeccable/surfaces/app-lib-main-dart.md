---
version: 1
slug: "app-lib-main-dart"
primary_target: "app/lib/main.dart"
related_targets: []
---

# Surface : app Android — recherche et fiche produit

Mode : Operate. Utilisateur : pharmacien ou assistant au comptoir, téléphone tenu d'une main. Tâche : retrouver le produit exact d'une ordonnance, lire son statut, trouver un équivalent substituable. Fréquence : des dizaines de fois par jour, par recherches de quelques secondes.

## Direction contract

THESIS: Une app de service public algérienne familière au pharmacien, dans la lignée d'El Hana (référence fournie par l'utilisateur), où le statut réglementaire (retiré, non renouvelé, en vigueur) reste l'information la plus visible de chaque ligne et de chaque fiche. Refuse le « dashboard santé » coloré et toute ressemblance d'identité avec la CNAS.

OWN-WORLD: Bleu azur (#4A90E2 et ses tons) pour actions, icônes, en-têtes ; fond gris clair, cartes blanches arrondies (16 dp) à ombre douce qui regroupent les informations ; champs remplis bleu pâle arrondis avec icône en tête ; icône Material devant chaque information de la fiche ; Nunito (arrondie) pour tout le texte, chiffres tabulaires ; sombre : gris ardoise, cartes plus claires, même bleu éclairci. Statuts : erreur = retiré, ambre = non renouvelé, tonal neutre = en vigueur ; aucun orange décoratif.

STORY: Le pharmacien tape quelques lettres dans le champ bleu pâle, voit dans une carte blanche marque, dosage, forme et statut, ouvre la fiche : statut d'abord, et s'il est retiré, équivalents en vigueur de même dosage juste en dessous.

FIRST VIEWPORT: Champ de recherche rempli bleu pâle, arrondi, icône loupe, en haut (focus au lancement) ; version de la nomenclature dessous ; résultats dans une carte blanche sur fond gris, une ligne par présentation, chip de statut à droite pour tout produit non en vigueur ; pas de FAB.

FORM: direction fixée par l'utilisateur (référence El Hana) — prime sur le tirage ; seed:fe769b877b18a4ee (dernier tirage avant la décision de l'utilisateur).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
