import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:synapse/data/equivalents.dart';
import 'package:synapse/data/nomenclature_db.dart';
import 'package:synapse/data/search.dart';

void main() {
  const asset = 'assets/nomenclature/nomenclature.sqlite';

  test('la nomenclature embarquée correspond à son manifeste', () {
    final m = jsonDecode(File('assets/nomenclature/manifest.json').readAsStringSync()) as Map<String, dynamic>;
    final bytes = File(asset).readAsBytesSync();
    expect((bytes.length, sha256.convert(bytes).toString()), (m['size'], m['sha256']));
    final db = NomenclatureDb.open(asset);
    addTearDown(db.close);
    expect(db.meta.version, m['version']);
    expect(db.meta.products, greaterThan(9000));
  });

  test('recherche réelle < 300 ms', () {
    final db = NomenclatureDb.open(asset);
    addTearDown(db.close);
    for (final q in ['doliprane', 'augmentin 1g', 'amoxicilline', 'clamoxyl', 'cetripex', 'l\'alcool', 'glucophage 850']) {
      final sw = Stopwatch()..start();
      final hits = search(db, q);
      expect(sw.elapsedMilliseconds, lessThan(300), reason: q);
      expect(hits, isNotEmpty, reason: q);
      equivalentsOf(db, hits.first);
    }
  });
}
