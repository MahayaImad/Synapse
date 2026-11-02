import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:sqlite3/sqlite3.dart';

import 'manifest.dart';
import 'nomenclature_db.dart';
import 'store.dart';

enum UpdateOutcome { upToDate, updated, disabled, waitingForWifi, failed }

class UpdateResult {
  const UpdateResult(this.outcome, this.checkedAt, {this.newVersion, this.error});

  final UpdateOutcome outcome;
  final DateTime checkedAt;
  final String? newVersion;
  final String? error;
}

/// Vérifie le manifeste et installe une nomenclature plus récente, vérifiée de bout en bout.
/// Tout échec laisse la base installée intacte.
class UpdateService {
  UpdateService({
    required this.client,
    required this.store,
    required this.manifestUrl,
    required this.onUnmeteredNetwork,
    DateTime Function()? now,
    this.timeout = const Duration(seconds: 30),
    this.interval = const Duration(hours: 24),
  }) : _now = now ?? DateTime.now;

  final http.Client client;
  final NomenclatureStore store;
  final Future<String> Function() manifestUrl;
  final Future<bool> Function() onUnmeteredNetwork;
  final Duration timeout;
  final Duration interval;
  final DateTime Function() _now;

  UpdateResult? _last;
  DateTime? _lastAttempt;

  /// Dernier résultat, quel qu'il soit.
  UpdateResult? get last => _last;

  /// Vrai si aucune vérification n'a réellement interrogé le serveur depuis [interval]
  /// (« désactivé » et « en attente du Wi-Fi » ne comptent pas : on réessaie au prochain passage).
  bool get due => _lastAttempt == null || _now().difference(_lastAttempt!) >= interval;

  Future<UpdateResult> check({bool userInitiated = false}) async {
    final result = await _check(userInitiated);
    _last = result;
    if (result.outcome != UpdateOutcome.waitingForWifi && result.outcome != UpdateOutcome.disabled) {
      _lastAttempt = result.checkedAt;
    }
    return result;
  }

  Future<UpdateResult> _check(bool userInitiated) async {
    final url = (await manifestUrl()).trim();
    if (url.isEmpty) return UpdateResult(UpdateOutcome.disabled, _now());
    if (!userInitiated && !await onUnmeteredNetwork()) return UpdateResult(UpdateOutcome.waitingForWifi, _now());
    File? tmp;
    try {
      final m = await _get(Uri.parse(url));
      final manifest = Manifest.parse(String.fromCharCodes(m));
      if (manifest.version.compareTo(store.meta.version) <= 0) return UpdateResult(UpdateOutcome.upToDate, _now());
      final bytes = await _get(Uri.parse(url).resolve(manifest.file));
      if (bytes.length != manifest.size) {
        throw StateError('taille ${bytes.length} octets, ${manifest.size} attendus');
      }
      if (sha256.convert(bytes).toString() != manifest.sha256) throw StateError('empreinte SHA-256 différente');
      tmp = File('${store.dir.path}/telechargement.tmp');
      await tmp.writeAsBytes(bytes, flush: true);
      _verify(tmp, manifest.version);
      await store.install(tmp);
      return UpdateResult(UpdateOutcome.updated, _now(), newVersion: manifest.version);
    } catch (e) {
      return UpdateResult(UpdateOutcome.failed, _now(), error: _describe(e));
    } finally {
      if (tmp != null && tmp.existsSync()) tmp.deleteSync();
    }
  }

  Future<List<int>> _get(Uri uri) async {
    final r = await client.get(uri).timeout(timeout);
    if (r.statusCode != 200) throw StateError('HTTP ${r.statusCode} sur ${uri.path}');
    return r.bodyBytes;
  }

  void _verify(File f, String version) {
    final db = NomenclatureDb.open(f.path);
    try {
      if (db.meta.version != version) throw StateError('le fichier contient ${db.meta.version}, $version annoncée');
      final check = db.raw.select('PRAGMA integrity_check').first.values.first;
      if (check != 'ok') throw StateError('intégrité : $check');
    } on SqliteException catch (e) {
      throw StateError('intégrité : ${e.message}');
    } finally {
      db.close();
    }
  }

  static String _describe(Object e) => switch (e) {
        StateError(:final message) => message,
        FormatException(:final message) => message,
        NomenclatureFormatError(:final message) => message,
        _ => e.toString(),
      };
}
