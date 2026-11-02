import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
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

  test('Manifest.parse', () {
    expect(Manifest.parse(jsonEncode(manifest)).size, newFile.length);
    expect(() => Manifest.parse('[]'), throwsFormatException);
    expect(() => Manifest.parse(jsonEncode({...manifest, 'sha256': 'abc'})), throwsFormatException);
  });
}
