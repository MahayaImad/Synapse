import 'package:flutter_test/flutter_test.dart';
import 'package:synapse/data/equivalents.dart';
import 'package:synapse/data/nomenclature_db.dart';
import 'package:synapse/data/product.dart';

import 'fixtures.dart';

void main() {
  late NomenclatureDb db;
  setUp(() => db = NomenclatureDb.open(fixtureDb));
  tearDown(() => db.close());

  test('parité avec le backend', () {
    for (final c in loadCases('equivalents_cases.json')) {
      final e = equivalentsOf(db, db.productById(c['id'] as String)!);
      expect(e.sameDosage.map((p) => p.id).toList(), c['same_dosage'], reason: '${c['id']} même dosage');
      expect(e.activeSameDosage.map((p) => p.id).toList(), c['active_same_dosage'], reason: '${c['id']} actifs');
      expect([for (final g in e.otherDosages) {'dosage': g.dosage, 'ids': g.products.map((p) => p.id).toList()}],
          c['other_dosages'], reason: '${c['id']} autres dosages');
    }
  });

  Product byBrand(String marque, String dosage) => db.productById(
      db.raw.select('select id from produit where marque = ? and dosage = ?', [marque, dosage]).first['id'] as String)!;

  test('produit retiré : équivalents en vigueur de même dosage', () {
    final e = equivalentsOf(db, byBrand('CETIRIZINE MYLAN', '10MG'));
    expect(e.activeSameDosage, isNotEmpty);
    expect(e.activeSameDosage.every((p) => p.statut == ProductStatus.enVigueur), isTrue);
    expect(e.activeSameDosage.map((p) => p.marque), contains('HISTARIZINE')); // « 10 MG » = « 10MG »
  });

  test('retiré sans équivalent en vigueur de même dosage', () {
    final e = equivalentsOf(db, byBrand('CLAMOXYL', '1G'));
    expect(e.activeSameDosage, isEmpty);
    expect(e.otherDosages.map((g) => g.dosage), contains('500MG'));
  });

  test('dosage non précisé : jamais proposé comme même dosage', () {
    final e = equivalentsOf(db, byBrand('POLIVIT', ''));
    expect(e.sameDosage, isEmpty);
    expect(e.activeSameDosage, isEmpty);
    expect(e.otherDosages.first.isUnknown, isTrue);
    expect(e.otherDosages.first.products.map((p) => p.marque), ['VITAM']);
  });

  test('produit sans équivalent', () {
    expect(equivalentsOf(db, byBrand('ALCOOL CHIRURGICAL 90°', '90°')).isEmpty, isTrue);
  });
}
