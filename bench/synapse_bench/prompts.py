"""Consignes communes à tous les moteurs (même texte pour une comparaison équitable)."""

LECTURE = """Tu lis une ordonnance algérienne photographiée (en français, imprimée ou manuscrite).
Transcris chaque ligne de médicament prescrite, dans l'ordre, sans rien inventer.

Pour chaque ligne :
- texte_brut : la ligne telle qu'écrite ;
- nom_lu, dosage_lu, forme_lue : ce qui est écrit, sans corriger vers un nom que tu connais ;
- posologie : uniquement ce qui est écrit. dose_par_prise est un nombre lu (jamais calculé ni déduit) ;
  frequence au format « N/j », « N/sem » ou « si besoin » ; duree au format « N j », « N sem » ou « N mois » ;
  un champ non écrit vaut null ;
- lisibilite : « claire », « douteuse » ou « illisible ». Si tu hésites sur un mot, mets « douteuse ».

age et poids : seulement s'ils sont écrits, sinon null.
Ignore toute zone masquée (rectangles noirs) et ne transcris jamais de nom de personne."""

LECTURE_TEXTE = """Voici la transcription brute d'une ordonnance algérienne (OCR local, les noms de personnes ont été retirés).
""" + LECTURE.split("\n", 1)[1]

CHOIX = """Une ligne d'ordonnance a été lue. Choisis le produit de la nomenclature qui lui correspond,
UNIQUEMENT parmi la liste fournie, en comparant marque, dosage et forme.
Si aucun candidat ne correspond sans doute possible (marque, dosage ou forme incertains ou absents de la liste),
réponds « incertain ». Ne devine jamais : une erreur est plus grave qu'un « incertain ».
Réponds avec la référence (ex. « p3 ») ou « incertain », et une raison courte."""

OCR = """Transcris fidèlement tout le texte de cette ordonnance, ligne par ligne, sans rien corriger.
Ignore les zones masquées (rectangles noirs)."""
