import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sqlite3/sqlite3.dart';
import 'package:synapse/data/nomenclature_db.dart';
import 'package:synapse/data/search.dart';
import 'package:synapse/data/text.dart';

import 'fixtures.dart';

void main() {
  group('texte', () {
    test('accents', () => expect(stripAccents('PARACÉTAMOL àéèêëîïôöùûüç'), 'PARACETAMOL aeeeeiioouuuc'));
    test('jetons', () {
      expect(searchTokens("l'alcool 90°"), ['ALCOOL', '90']);
      expect(searchTokens(''), isEmpty);
      expect(searchTokens('"*-'), isEmpty);
      expect(searchTokens('a b c d e f g h i j'), hasLength(8));
    });
    test('trigrammes', () => expect(trigrams('Dolip'), {'DOL', 'OLI', 'LIP'}));
    test('clé de dosage', () => expect(dosageKey(' 10 MG '), '10MG'));
  });

  test('parité avec le backend', () {
    final db = NomenclatureDb.open(fixtureDb);
    addTearDown(db.close);
    final failures = <String>[];
    for (final c in loadCases('search_cases.json')) {
      final got = search(db, c['query'] as String, limit: c['limit'] as int).map((p) => p.id).toList();
      final want = (c['ids'] as List).cast<String>();
      if (got.join(',') != want.join(',')) failures.add('«${c['query']}» limit ${c['limit']}: $got != $want');
    }
    expect(failures, isEmpty, reason: failures.join('\n'));
  });

  test('moins de 300 ms sur 9 500 produits', () {
    final dir = Directory.systemTemp.createTempSync();
    addTearDown(() => dir.deleteSync(recursive: true));
    final f = copyFixture(dir);
    final w = sqlite3.open(f.path);
    final syll = ['CE', 'TI', 'RI', 'PEX', 'DO', 'LI', 'PRA', 'NE', 'AMO', 'XI', 'CIL', 'ZO', 'LAN', 'MET', 'FOR', 'MINE'];
    final stmt = w.prepare("INSERT INTO produit (id, marque, dci, code_dci, forme, dosage, conditionnement, liste, statut, labo, pays, hopital, officine, n_enregistrement) VALUES (?, ?, ?, ?, 'COMPRIME', ?, 'B/30', 'II', ?, 'LABO', 'ALGERIE', 1, 1, ?)");
    final brands = <String>[];
    for (var i = 0; i < 9460; i++) {
      final b = List.generate(2 + i % 3, (k) => syll[(i * 7 + k * 5) % syll.length]).join();
      brands.add(b);
      stmt.execute(['syn-$i', b, 'DCI ${b.substring(0, 4)}', '0${i % 9} A ${i % 999}', '${i % 1000}MG',
        ['en_vigueur', 'en_vigueur', 'retire', 'non_renouvele'][i % 4], '$i/01 A 001/20']);
    }
    stmt.close();
    w.execute("INSERT INTO produit_fts(produit_fts) VALUES('rebuild')");
    w.execute("INSERT INTO marque_trgm(marque_trgm) VALUES('rebuild')");
    w.close();
    final db = NomenclatureDb.open(f.path);
    addTearDown(db.close);
    final queries = [for (var i = 0; i < 40; i++) brands[i * 211].substring(0, (3 + i % 4).clamp(1, brands[i * 211].length)), 'cetripex', 'doliprn', 'zz',
      'amoxicilin', 'a', 'metformine 500', 'x', 'pex', 'ne', 'lan'];
    var worst = Duration.zero;
    for (final q in queries) {
      final sw = Stopwatch()..start();
      search(db, q);
      if (sw.elapsed > worst) worst = sw.elapsed;
    }
    expect(worst, lessThan(const Duration(milliseconds: 300)), reason: 'pire : $worst');
  });
}
