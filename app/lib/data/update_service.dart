import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:sqlite3/sqlite3.dart';

import 'manifest.dart';
import 'nomenclature_db.dart';
import 'product.dart';
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
    this.timeout = const Duration(seconds: 30), // délai d'inactivité (aucun octet reçu), pas une durée totale
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

  Future<UpdateResult>? _inFlight;

  /// Une seule vérification à la fois : un second appel pendant la première reçoit le même résultat.
  Future<UpdateResult> check({bool userInitiated = false}) =>
      _inFlight ??= _checkAndRecord(userInitiated).whenComplete(() => _inFlight = null);

  Future<UpdateResult> _checkAndRecord(bool userInitiated) async {
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
      final body = BytesBuilder(copy: false);
      await _download(Uri.parse(url), (chunk) => body.add(chunk), maxBytes: 64 * 1024);
      final manifest = Manifest.parse(utf8.decode(body.takeBytes(), allowMalformed: true));
      if (manifest.version.compareTo(store.meta.version) <= 0) return UpdateResult(UpdateOutcome.upToDate, _now());
      tmp = File('${store.dir.path}/telechargement-${DateTime.now().microsecondsSinceEpoch}.tmp');
      final sink = tmp.openWrite();
      final digest = _DigestSink();
      final hasher = sha256.startChunkedConversion(digest);
      var received = 0;
      try {
        await _download(Uri.parse(url).resolve(manifest.file), (chunk) {
          received += chunk.length;
          if (received > manifest.size) throw StateError('fichier plus grand que les ${manifest.size} octets annoncés');
          sink.add(chunk);
          hasher.add(chunk);
        });
      } finally {
        await sink.close();
      }
      hasher.close();
      if (received != manifest.size) throw StateError('taille $received octets, ${manifest.size} attendus');
      if (digest.value.toString() != manifest.sha256) throw StateError('empreinte SHA-256 différente');
      _verify(tmp, manifest.version);
      await store.install(tmp);
      return UpdateResult(UpdateOutcome.updated, _now(), newVersion: manifest.version);
    } catch (e) {
      return UpdateResult(UpdateOutcome.failed, _now(), error: _describe(e));
    } finally {
      if (tmp != null && tmp.existsSync()) tmp.deleteSync();
    }
  }

  /// Télécharge par morceaux ; échoue si aucun octet n'arrive pendant [timeout] (et non au bout d'une durée totale).
  Future<void> _download(Uri uri, void Function(List<int>) onChunk, {int? maxBytes}) async {
    final response = await client.send(http.Request('GET', uri)).timeout(timeout);
    if (response.statusCode != 200) {
      unawaited(response.stream.drain<void>().catchError((_) {}));
      throw StateError('HTTP ${response.statusCode} sur ${uri.path}');
    }
    var total = 0;
    final done = Completer<void>();
    late final StreamSubscription<List<int>> sub;
    Timer? idle;
    void fail(Object e) {
      idle?.cancel();
      unawaited(sub.cancel().catchError((_) {})); // ne pas attendre : un flux bloqué peut ne jamais se terminer
      if (!done.isCompleted) done.completeError(e);
    }

    void arm() {
      idle?.cancel();
      idle = Timer(timeout, () => fail(StateError('aucune donnée reçue pendant ${timeout.inSeconds} s')));
    }

    sub = response.stream.listen(
      (chunk) {
        arm();
        total += chunk.length;
        try {
          if (maxBytes != null && total > maxBytes) throw StateError('réponse trop volumineuse');
          onChunk(chunk);
        } catch (e) {
          fail(e);
        }
      },
      onError: fail,
      onDone: () {
        idle?.cancel();
        if (!done.isCompleted) done.complete();
      },
      cancelOnError: true,
    );
    arm();
    return done.future;
  }

  void _verify(File f, String version) {
    final db = NomenclatureDb.open(f.path);
    try {
      if (db.meta.version != version) throw StateError('le fichier contient ${db.meta.version}, $version annoncée');
      final check = db.raw.select('PRAGMA integrity_check').first.values.first;
      if (check != 'ok') throw StateError('intégrité : $check');
      // Chaque ligne doit être lisible par l'app : une valeur inattendue (statut inconnu, date illisible…)
      // rendrait la recherche inutilisable après installation.
      for (final row in db.raw.select('SELECT * FROM produit')) {
        try {
          Product.fromRow(row);
        } on Object catch (e) {
          throw StateError('produit ${row['id']} illisible : ${e is FormatException ? e.message : e}');
        }
      }
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

class _DigestSink implements Sink<Digest> {
  late Digest value;

  @override
  void add(Digest data) => value = data;

  @override
  void close() {}
}
