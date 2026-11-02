/// Normalisations de texte partagées avec le backend (backend/src/synapse_admin/search.py).
library;

import 'accents.g.dart';

/// Retire les accents et formes de compatibilité, comme la normalisation NFKD du backend
/// (table générée : accents.g.dart).
String stripAccents(String text) {
  final b = StringBuffer();
  for (final r in text.runes) {
    b.write(accentTable[r] ?? String.fromCharCode(r));
  }
  return b.toString();
}

/// Majuscules comme Python : « ß » devient « SS ».
String upper(String text) => text.toUpperCase().replaceAll('ß', 'SS');

// Frontière de mot Unicode (comme \b en Python) : une lettre grecque ou accentuée précédente compte comme lettre.
final _elision = RegExp(r"(?<![\p{L}\p{N}_])[LDJCMNST]['’]", unicode: true);
final _token = RegExp(r'[A-Z0-9]+');
final _nonAlnum = RegExp(r'[^A-Z0-9]');

const maxTokens = 8;

/// Jetons de recherche : sans accents, en majuscules, élisions françaises retirées.
List<String> searchTokens(String query) {
  final text = upper(stripAccents(query)).replaceAll(_elision, ' ');
  return _token.allMatches(text).map((m) => m.group(0)!).take(maxTokens).toList();
}

Set<String> trigrams(String text) {
  final t = upper(stripAccents(text)).replaceAll(_nonAlnum, '');
  return {for (var i = 0; i + 3 <= t.length; i++) t.substring(i, i + 3)};
}

/// Dosage comparable : seuls les espaces sont neutralisés (une virgule ou un point peut changer la valeur).
String dosageKey(String dosage) => dosage.replaceAll(RegExp(r'\s+'), '');
