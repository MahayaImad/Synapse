import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:sqlite3/sqlite3.dart';

import 'nomenclature_db.dart';
import 'product.dart';

typedef AssetBytes = Future<ByteData> Function(String key);

/// Détient la nomenclature courante et la remplace d'un coup lors d'une mise à jour.
///
/// Les écrans relisent toujours [db] (jamais une référence gardée) et se reconstruisent
/// à chaque notification.
class NomenclatureStore extends ChangeNotifier {
  NomenclatureStore({
    required this.dir,
    required this.loadAsset,
    this.embeddedKey = 'assets/nomenclature/nomenclature.sqlite',
    this.embeddedManifestKey = 'assets/nomenclature/manifest.json',
  });

  final Directory dir;
  final AssetBytes loadAsset;
  final String embeddedKey;
  final String embeddedManifestKey;

  NomenclatureDb? _db;

  File get installedFile => File('${dir.path}/nomenclature.sqlite');

  NomenclatureDb get db => _db ?? (throw StateError('NomenclatureStore.init() non appelé'));

  NomenclatureMeta get meta => db.meta;

  bool get isReady => _db != null;

  Future<void> init() async {
    final embeddedVersion = await _embeddedVersion();
    NomenclatureDb? current;
    if (installedFile.existsSync()) {
      try {
        current = NomenclatureDb.open(installedFile.path);
        if (current.raw.select('PRAGMA quick_check').first.values.first != 'ok') {
          current.close();
          current = null; // pages abîmées : on repart de la base embarquée
        }
      } on NomenclatureFormatError {
        current = null; // fichier abîmé : on repart de la base embarquée
      } on SqliteException {
        current?.close();
        current = null;
      }
    }
    if (current != null && current.meta.version.compareTo(embeddedVersion) >= 0) {
      _db = current;
      notifyListeners();
      return;
    }
    // Copie de la base embarquée ; en cas d'échec, l'ancienne base installée (encore ouverte) reste utilisée.
    final tmp = File('${dir.path}/embarquee.tmp');
    try {
      final bytes = await loadAsset(embeddedKey);
      await tmp.writeAsBytes(bytes.buffer.asUint8List(bytes.offsetInBytes, bytes.lengthInBytes), flush: true);
      if (current != null) {
        _db = current;
        current = null;
      }
      await install(tmp, notify: false);
    } catch (_) {
      if (tmp.existsSync()) tmp.deleteSync();
      if (current == null && _db == null) rethrow;
      _db ??= current; // base plus ancienne mais valide
    }
    notifyListeners();
  }

  Future<String> _embeddedVersion() async {
    final b = await loadAsset(embeddedManifestKey);
    final json = jsonDecode(utf8.decode(b.buffer.asUint8List(b.offsetInBytes, b.lengthInBytes)));
    return (json as Map<String, dynamic>)['version'] as String;
  }

  /// Installe un fichier déjà téléchargé et vérifié (même dossier que [dir]).
  /// Lève [NomenclatureFormatError] sans rien changer si le fichier n'est pas une nomenclature.
  Future<void> install(File verified, {bool notify = true}) async {
    try {
      NomenclatureDb.open(verified.path).close(); // validation avant tout remplacement
    } on NomenclatureFormatError {
      if (verified.existsSync()) verified.deleteSync();
      rethrow;
    }
    final old = _db;
    verified.renameSync(installedFile.path); // atomique sur un même système de fichiers
    _db = NomenclatureDb.open(installedFile.path);
    old?.close(); // l'ancien fichier reste lisible jusqu'ici (inode encore ouvert)
    if (notify) notifyListeners();
  }

  @override
  void dispose() {
    _db?.close();
    _db = null;
    super.dispose();
  }
}
