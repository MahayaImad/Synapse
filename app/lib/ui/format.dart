const _months = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre',
  'novembre', 'décembre'];

/// « 2026-08 » → « août 2026 » (libellé de version de nomenclature).
String versionLabel(String version) {
  final m = RegExp(r'^(\d{4})-(\d{2})$').firstMatch(version);
  final month = m == null ? 0 : int.parse(m.group(2)!);
  if (month < 1 || month > 12) return version;
  return '${_months[month - 1]} ${m!.group(1)}';
}

String two(int n) => n.toString().padLeft(2, '0');

/// Date au format JJ/MM/AAAA.
String shortDate(DateTime d) => '${two(d.day)}/${two(d.month)}/${d.year}';

/// Empêche les coupures de ligne juste après « / » (« B/10 », « 5MG/ML ») : U+2060 (WORD JOINER).
String noBreakAfterSlash(String s) => s.replaceAll('/', '/\u2060');
