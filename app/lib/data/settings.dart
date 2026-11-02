import 'package:shared_preferences/shared_preferences.dart';

/// Réglages locaux (adresse du manifeste pendant le pilote).
class Settings {
  Settings._(this._prefs);

  /// Valeur fixée au build : --dart-define=SYNAPSE_MANIFEST_URL=https://…
  static const buildManifestUrl = String.fromEnvironment('SYNAPSE_MANIFEST_URL');
  static const _key = 'manifest_url';

  static Future<Settings> load() async => Settings._(await SharedPreferences.getInstance());

  final SharedPreferences _prefs;

  String get manifestUrl => _prefs.getString(_key) ?? buildManifestUrl;

  /// Vide = mises à jour désactivées. Seules les adresses https sont acceptées.
  Future<void> setManifestUrl(String url) async {
    final u = url.trim();
    if (u.isNotEmpty) {
      final uri = Uri.tryParse(u);
      if (uri == null || uri.scheme != 'https' || uri.host.isEmpty) {
        throw ArgumentError.value(url, 'url', 'adresse https attendue');
      }
    }
    await _prefs.setString(_key, u);
  }
}
