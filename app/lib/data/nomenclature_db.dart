import 'package:sqlite3/sqlite3.dart';

import 'product.dart';

class NomenclatureFormatError implements Exception {
  NomenclatureFormatError(this.message);

  final String message;

  @override
  String toString() => 'NomenclatureFormatError: $message';
}

/// Fichier de nomenclature publié, ouvert en lecture seule.
class NomenclatureDb {
  NomenclatureDb._(this.raw, this.path, this.meta);

  static NomenclatureDb open(String path) {
    final Database db;
    try {
      db = sqlite3.open(path, mode: OpenMode.readOnly);
    } on SqliteException catch (e) {
      throw NomenclatureFormatError('Ouverture impossible : ${e.message}');
    }
    try {
      final tables = db.select("SELECT name FROM sqlite_master WHERE type IN ('table','view')").map((r) => r['name']).toSet();
      if (!tables.containsAll({'produit', 'meta', 'produit_fts', 'marque_trgm'})) {
        throw NomenclatureFormatError('Tables de nomenclature absentes');
      }
      final m = {for (final r in db.select('SELECT cle, valeur FROM meta')) r['cle'] as String: r['valeur'] as String};
      final meta = NomenclatureMeta(
        version: m['version'] ?? (throw NomenclatureFormatError('meta.version absent')),
        referenceDate: DateTime.parse(m['reference_date'] ?? (throw NomenclatureFormatError('meta.reference_date absent'))),
        products: int.parse(m['products'] ?? '0'),
        publishedAt: DateTime.parse(m['published_at'] ?? (throw NomenclatureFormatError('meta.published_at absent'))),
      );
      return NomenclatureDb._(db, path, meta);
    } on SqliteException catch (e) {
      db.dispose();
      throw NomenclatureFormatError('Fichier illisible : ${e.message}');
    } on FormatException catch (e) {
      db.dispose();
      throw NomenclatureFormatError('Métadonnées invalides : ${e.message}');
    } on NomenclatureFormatError {
      db.dispose();
      rethrow;
    }
  }

  final Database raw;
  final String path;
  final NomenclatureMeta meta;

  Product? productById(String id) {
    final rows = raw.select('SELECT * FROM produit WHERE id = ?', [id]);
    return rows.isEmpty ? null : Product.fromRow(rows.first);
  }

  void close() => raw.dispose();
}
