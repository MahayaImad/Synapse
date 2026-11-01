import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:sqlite3/sqlite3.dart';
import 'package:synapse/data/nomenclature_db.dart';
import 'package:synapse/data/search.dart';
import 'package:synapse/data/store.dart';

import 'fixtures.dart';

/// Copie du fichier de test re-étiquetée à une autre version.
File relabel(Directory dir, String version, {String name = 'v.sqlite', String? dropBrand}) {
  final f = copyFixture(dir, name);
  final w = sqlite3.open(f.path);
  w.execute("UPDATE meta SET valeur = ? WHERE cle = 'version'", [version]);
  if (dropBrand != null) {
    w.execute('DELETE FROM produit WHERE marque = ?', [dropBrand]);
    w.execute("INSERT INTO produit_fts(produit_fts) VALUES('rebuild')");
    w.execute("INSERT INTO marque_trgm(marque_trgm) VALUES('rebuild')");
  }
  w.close();
  return f;
}

AssetBytes assetsFrom(File db, String version) => (key) async {
      if (key.endsWith('manifest.json')) {
        return ByteData.sublistView(Uint8List.fromList(utf8.encode(jsonEncode({'version': version}))));
      }
      return ByteData.sublistView(db.readAsBytesSync());
    };

void main() {
  late Directory root, dir;
  setUp(() {
    root = Directory.systemTemp.createTempSync();
    dir = Directory('${root.path}/app')..createSync();
  });
  tearDown(() => root.deleteSync(recursive: true));

  test('premier lancement : copie la base embarquée', () async {
    final s = NomenclatureStore(dir: dir, loadAsset: assetsFrom(File(fixtureDb), '2026-08'));
    await s.init();
    expect(s.meta.version, '2026-08');
    expect(File('${dir.path}/nomenclature.sqlite').existsSync(), isTrue);
    s.dispose();
  });

  test('second lancement : pas de recopie', () async {
    final s = NomenclatureStore(dir: dir, loadAsset: assetsFrom(File(fixtureDb), '2026-08'));
    await s.init();
    s.dispose();
    final installed = File('${dir.path}/nomenclature.sqlite');
    final before = installed.lastModifiedSync();
    await Future<void>.delayed(const Duration(milliseconds: 20));
    final s2 = NomenclatureStore(dir: dir, loadAsset: (k) async => throw StateError('asset relu : $k'));
    await expectLater(s2.init(), throwsStateError); // le manifeste embarqué est lu…
    final s3 = NomenclatureStore(dir: dir, loadAsset: assetsFrom(File(fixtureDb), '2026-08'));
    await s3.init();
    expect(installed.lastModifiedSync(), before); // …mais la base n'est pas recopiée
    s3.dispose();
  });

  test('APK plus récent : recopie', () async {
    final s = NomenclatureStore(dir: dir, loadAsset: assetsFrom(File(fixtureDb), '2026-08'));
    await s.init();
    s.dispose();
    final s2 = NomenclatureStore(dir: dir, loadAsset: assetsFrom(relabel(root, '2026-10'), '2026-10'));
    await s2.init();
    expect(s2.meta.version, '2026-10');
    s2.dispose();
  });

  test('base installée corrompue : recopie depuis l\'APK', () async {
    File('${dir.path}/nomenclature.sqlite').writeAsStringSync('abîmé');
    final s = NomenclatureStore(dir: dir, loadAsset: assetsFrom(File(fixtureDb), '2026-08'));
    await s.init();
    expect(s.meta.version, '2026-08');
    s.dispose();
  });

  test('install : remplace, notifie, et l\'ancienne lecture se termine', () async {
    final s = NomenclatureStore(dir: dir, loadAsset: assetsFrom(File(fixtureDb), '2026-08'));
    await s.init();
    var notified = 0;
    s.addListener(() => notified++);
    final old = s.db;
    expect(search(old, 'doliprane'), isNotEmpty);
    await s.install(relabel(dir, '2026-09', name: 'telecharge.tmp', dropBrand: 'DOLIPRANE'));
    expect(s.meta.version, '2026-09');
    expect(notified, 1);
    expect(search(s.db, 'doliprane').map((p) => p.marque), isNot(contains('DOLIPRANE')));
    expect(File('${dir.path}/telecharge.tmp').existsSync(), isFalse);
    s.dispose();
  });

  test('install d\'un fichier invalide : ancienne base conservée', () async {
    final s = NomenclatureStore(dir: dir, loadAsset: assetsFrom(File(fixtureDb), '2026-08'));
    await s.init();
    final bad = File('${dir.path}/bad.tmp')..writeAsStringSync('rien');
    await expectLater(s.install(bad), throwsA(isA<NomenclatureFormatError>()));
    expect(s.meta.version, '2026-08');
    expect(search(s.db, 'doliprane'), isNotEmpty);
    s.dispose();
  });
}
