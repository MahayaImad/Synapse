import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:sqlite3/sqlite3.dart';
import 'package:synapse/data/manifest.dart';
import 'package:synapse/data/store.dart';
import 'package:synapse/data/update_service.dart';

import 'fixtures.dart';
import 'store_test.dart' show assetsFrom, relabel;

const url = 'https://maj.example.dz/nomenclature/manifest.json';

void main() {
  late Directory root, dir;
  late NomenclatureStore store;
  late List<int> newFile;
  late Map<String, dynamic> manifest;

  setUp(() async {
    root = Directory.systemTemp.createTempSync();
    dir = Directory('${root.path}/app')..createSync();
    store = NomenclatureStore(dir: dir, loadAsset: assetsFrom(File(fixtureDb), '2026-08'));
    await store.init();
    newFile = relabel(root, '2026-09').readAsBytesSync();
    manifest = {
      'version': '2026-09', 'reference_date': '2026-09-30', 'file': 'nomenclature-2026-09.sqlite',
      'size': newFile.length, 'sha256': sha256.convert(newFile).toString(), 'published_at': '2026-10-02T08:00:00+00:00',
    };
  });
  tearDown(() {
    store.dispose();
    root.deleteSync(recursive: true);
  });

  UpdateService service(http.Client client, {String u = url, bool wifi = true, Duration? timeout}) => UpdateService(
        client: client, store: store, manifestUrl: () async => u, onUnmeteredNetwork: () async => wifi,
        now: () => DateTime(2026, 10, 3, 9), timeout: timeout ?? const Duration(seconds: 5));

  MockClient server({Object? manifestBody, int manifestStatus = 200, List<int>? file, int fileStatus = 200}) =>
      MockClient((req) async {
        if (req.url.toString() == url) {
          return http.Response(manifestBody is String ? manifestBody : jsonEncode(manifestBody ?? manifest), manifestStatus);
        }
        if (req.url.toString() == 'https://maj.example.dz/nomenclature/nomenclature-2026-09.sqlite') {
          return http.Response.bytes(file ?? newFile, fileStatus);
        }
        return http.Response('?', 404);
      });

  List<String> leftovers() => dir.listSync().map((e) => e.path.split('/').last).where((n) => n != 'nomenclature.sqlite').toList();

  test('URL vide → désactivé', () async {
    final r = await service(server(), u: '').check();
    expect(r.outcome, UpdateOutcome.disabled);
  });

  test('réseau facturé → attend le Wi-Fi ; vérification manuelle passe outre', () async {
    expect((await service(server(), wifi: false).check()).outcome, UpdateOutcome.waitingForWifi);
    expect((await service(server(), wifi: false).check(userInitiated: true)).outcome, UpdateOutcome.updated);
  });

  test('même version ou plus ancienne → à jour, sans téléchargement', () async {
    for (final v in ['2026-08', '2026-07']) {
      var downloads = 0;
      final c = MockClient((req) async {
        if (req.url.toString() != url) downloads++;
        return http.Response(jsonEncode({...manifest, 'version': v}), 200);
      });
      final r = await service(c).check();
      expect((r.outcome, downloads, store.meta.version), (UpdateOutcome.upToDate, 0, '2026-08'));
    }
  });

  test('version plus récente → installée', () async {
    final s = service(server());
    expect(s.due, isTrue);
    final r = await s.check();
    expect((r.outcome, r.newVersion, store.meta.version), (UpdateOutcome.updated, '2026-09', '2026-09'));
    expect(s.last!.checkedAt, DateTime(2026, 10, 3, 9));
    expect(s.due, isFalse);
    expect(leftovers(), isEmpty);
  });

  final failures = <String, MockClient Function(Map<String, dynamic> m, List<int> f)>{
    'JSON cassé': (m, f) => MockClient((_) async => http.Response('{"version": ', 200)),
    'champ manquant': (m, f) => MockClient((_) async => http.Response(jsonEncode({...m}..remove('sha256')), 200)),
    'mauvais type': (m, f) => MockClient((_) async => http.Response(jsonEncode({...m, 'size': 'grand'}), 200)),
    'HTTP 404 manifeste': (m, f) => MockClient((_) async => http.Response('', 404)),
    'HTTP 500 fichier': (m, f) => MockClient((r) async =>
        r.url.path.endsWith('manifest.json') ? http.Response(jsonEncode(m), 200) : http.Response('', 500)),
    'SHA faux': (m, f) => MockClient((r) async => r.url.path.endsWith('manifest.json')
        ? http.Response(jsonEncode({...m, 'sha256': '0' * 64}), 200) : http.Response.bytes(f, 200)),
    'taille fausse': (m, f) => MockClient((r) async => r.url.path.endsWith('manifest.json')
        ? http.Response(jsonEncode({...m, 'size': f.length + 1}), 200) : http.Response.bytes(f, 200)),
    'fichier tronqué': (m, f) => MockClient((r) async => r.url.path.endsWith('manifest.json')
        ? http.Response(jsonEncode(m), 200) : http.Response.bytes(f.sublist(0, f.length ~/ 2), 200)),
    'meta.version ≠ manifeste': (m, f) => MockClient((r) async => r.url.path.endsWith('manifest.json')
        ? http.Response(jsonEncode({...m, 'version': '2026-10'}), 200) : http.Response.bytes(f, 200)),
  };
  for (final e in failures.entries) {
    test('échec : ${e.key} → base inchangée', () async {
      final r = await service(e.value(manifest, newFile)).check();
      expect(r.outcome, UpdateOutcome.failed, reason: r.error);
      expect(r.error, isNotEmpty);
      expect(store.meta.version, '2026-08');
      expect(leftovers(), isEmpty);
    });
  }

  test('échec : délai dépassé', () async {
    final slow = MockClient((_) async {
      await Future<void>.delayed(const Duration(milliseconds: 300));
      return http.Response(jsonEncode(manifest), 200);
    });
    final r = await service(slow, timeout: const Duration(milliseconds: 50)).check();
    expect((r.outcome, store.meta.version), (UpdateOutcome.failed, '2026-08'));
  });

  MockClient serveFile(List<int> f) => MockClient((r) async => r.url.path.endsWith('manifest.json')
      ? http.Response(jsonEncode({...manifest, 'size': f.length, 'sha256': sha256.convert(f).toString()}), 200)
      : http.Response.bytes(f, 200));

  List<int> corrupted(String sql) {
    final f = relabel(root, '2026-09', name: 'bad.sqlite');
    final w = sqlite3.open(f.path)..execute(sql);
    w.close();
    return f.readAsBytesSync();
  }

  test('échec : ligne au statut inconnu → base inchangée', () async {
    final r = await service(serveFile(corrupted("UPDATE produit SET statut = 'suspendu' WHERE marque = 'DOLIPRANE'"))).check();
    expect((r.outcome, store.meta.version), (UpdateOutcome.failed, '2026-08'));
    expect(r.error, contains('suspendu'));
  });

  test('échec : date de retrait illisible → base inchangée', () async {
    final r = await service(serveFile(corrupted("UPDATE produit SET date_retrait = 'hier' WHERE marque = 'CLAMOXYL'"))).check();
    expect((r.outcome, store.meta.version), (UpdateOutcome.failed, '2026-08'));
  });

  MockClient chunked(Duration gap, {bool stall = false}) => MockClient.streaming((req, _) async {
        if (req.url.path.endsWith('manifest.json')) {
          return http.StreamedResponse(Stream.value(utf8.encode(jsonEncode(manifest))), 200);
        }
        Stream<List<int>> body() async* {
          const n = 8;
          final size = (newFile.length / n).ceil();
          for (var i = 0; i < newFile.length; i += size) {
            await Future<void>.delayed(gap);
            yield newFile.sublist(i, (i + size).clamp(0, newFile.length));
            if (stall && i > 0) await Completer<void>().future; // plus rien n'arrive
          }
        }
        return http.StreamedResponse(body(), 200, contentLength: newFile.length);
      });

  test('connexion lente mais continue : la mise à jour aboutit', () async {
    // 8 morceaux espacés de 40 ms (≈ 320 ms au total) avec un délai d'inactivité de 100 ms.
    final r = await service(chunked(const Duration(milliseconds: 40)), timeout: const Duration(milliseconds: 100)).check();
    expect((r.outcome, store.meta.version), (UpdateOutcome.updated, '2026-09'), reason: r.error);
  });

  test('connexion bloquée en cours de téléchargement : échec', () async {
    final r = await service(chunked(const Duration(milliseconds: 5), stall: true), timeout: const Duration(milliseconds: 100)).check();
    expect((r.outcome, store.meta.version), (UpdateOutcome.failed, '2026-08'));
    expect(leftovers(), isEmpty);
  });

  test('deux vérifications simultanées : une seule exécution', () async {
    var manifestCalls = 0;
    final client = MockClient((req) async {
      if (req.url.path.endsWith('manifest.json')) {
        manifestCalls++;
        return http.Response(jsonEncode(manifest), 200);
      }
      return http.Response.bytes(newFile, 200);
    });
    final s = service(client);
    final results = await Future.wait([s.check(), s.check(userInitiated: true)]);
    expect(results.map((r) => r.outcome), [UpdateOutcome.updated, UpdateOutcome.updated]);
    expect(manifestCalls, 1);
    expect(s.last!.outcome, UpdateOutcome.updated);
    expect(leftovers(), isEmpty);
  });

  test('Manifest.parse', () {
    expect(Manifest.parse(jsonEncode(manifest)).size, newFile.length);
    expect(() => Manifest.parse('[]'), throwsFormatException);
    expect(() => Manifest.parse(jsonEncode({...manifest, 'sha256': 'abc'})), throwsFormatException);
  });
}
