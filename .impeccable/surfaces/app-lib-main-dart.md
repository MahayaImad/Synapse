---
version: 1
slug: "app-lib-main-dart"
primary_target: "app/lib/main.dart"
related_targets: []
---

# Surface : app Android — recherche et fiche produit

Mode : Operate. Utilisateur : pharmacien ou assistant au comptoir, téléphone tenu d'une main. Tâche : retrouver le produit exact d'une ordonnance, lire son statut, trouver un équivalent substituable. Fréquence : des dizaines de fois par jour, par recherches de quelques secondes.

## Direction contract

THESIS: Material 3 standard au niveau de finition des apps Google ; le statut réglementaire (retiré, non renouvelé) est l'information la plus visible de chaque ligne et de chaque fiche. Refuse le « dashboard santé » coloré et les cartes décoratives.

OWN-WORLD: Couleurs dynamiques du téléphone (Material You), repli sur un schéma statique neutre ; rôles de couleur seulement ; erreur = retiré, couleur d'avertissement harmonisée = non renouvelé ; Roboto, échelle de type Material, chiffres tabulaires pour dosages et numéros ; listes Material denses, chips de statut tonales.

STORY: Le pharmacien tape quelques lettres, voit tout de suite marque, dosage, forme et statut, ouvre la fiche, et s'il est retiré, voit d'emblée les équivalents en vigueur de même dosage.

FIRST VIEWPORT: Barre de recherche Material en haut (focus au lancement, clavier ouvert), version de la nomenclature en sous-titre ; liste de résultats en dessous, une ligne par présentation, chip de statut à droite pour tout produit non en vigueur ; pas de FAB.

FORM: canon Material 3 (sortie permanente choisie par l'utilisateur après deux tirages ; 7 références officinales écartées) ; seed: none (canon).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
