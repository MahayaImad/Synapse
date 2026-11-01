/// Normalisations de texte partagées avec le backend (backend/src/synapse_admin/search.py).
library;

const _accents = {
  'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A', 'Ç': 'C', 'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
  'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I', 'Ñ': 'N', 'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O', 'Ù': 'U',
  'Ú': 'U', 'Û': 'U', 'Ü': 'U', 'Ý': 'Y', 'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a', 'ç': 'c',
  'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i', 'ñ': 'n', 'ò': 'o', 'ó': 'o',
  'ô': 'o', 'õ': 'o', 'ö': 'o', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u', 'ý': 'y', 'ÿ': 'y',
};

/// Retire les accents latins (équivalent de la décomposition NFKD utilisée côté backend).
String stripAccents(String text) {
  final b = StringBuffer();
  for (final r in text.runes) {
    final c = String.fromCharCode(r);
    b.write(_accents[c] ?? c);
  }
  return b.toString();
}

final _elision = RegExp(r"\b[LDJCMNST]['’]");
final _token = RegExp(r'[A-Z0-9]+');
final _nonAlnum = RegExp(r'[^A-Z0-9]');

const maxTokens = 8;

/// Jetons de recherche : sans accents, en majuscules, élisions françaises retirées.
List<String> searchTokens(String query) {
  final text = stripAccents(query).toUpperCase().replaceAll(_elision, ' ');
  return _token.allMatches(text).map((m) => m.group(0)!).take(maxTokens).toList();
}

Set<String> trigrams(String text) {
  final t = stripAccents(text).toUpperCase().replaceAll(_nonAlnum, '');
  return {for (var i = 0; i + 3 <= t.length; i++) t.substring(i, i + 3)};
}

/// Dosage comparable : seuls les espaces sont neutralisés (une virgule ou un point peut changer la valeur).
String dosageKey(String dosage) => dosage.replaceAll(RegExp(r'\s+'), '');
