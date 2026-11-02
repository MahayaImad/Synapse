import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sqlite3/sqlite3.dart';
import 'package:synapse/data/nomenclature_db.dart';
import 'package:synapse/data/product.dart';

import 'fixtures.dart';

void main() {
  late NomenclatureDb db;
  setUp(() => db = NomenclatureDb.open(fixtureDb));
  tearDown(() => db.close());

  test('meta', () {
    expect(db.meta.version, '2026-08');
    expect(db.meta.referenceDate, DateTime(2026, 8, 31));
    expect(db.meta.products, 43);
    expect(db.meta.publishedAt, DateTime.utc(2026, 9, 1));
  });

  test('produit par identifiant', () {
    final eq = loadCases('equivalents_cases.json');
    final retiredId = eq.firstWhere((c) => c['statut'] == 'retire')['id'] as String;
    final p = db.productById(retiredId)!;
    expect(p.marque, 'CETIRIZINE MYLAN');
    expect(p.statut, ProductStatus.retire);
    expect(p.dateRetrait, DateTime(2024, 3, 31));
    expect(p.motifRetrait, 'RETRAIT PAR LE DETENTEUR POUR MOTIF COMMERCIAL');
    expect(p.codeDci, '01 A 003');
    expect(p.hopital, isTrue);
    expect(p.officine, isTrue);
  });

  test('type de retrait et origine', () {
    final paralgan = db.raw.select("select id from produit where marque='PARALGAN'").first['id'] as String;
    final p = db.productById(paralgan)!;
    expect((p.dateRetrait, p.typeRetrait), (null, 'ABROGATION'));
    final nov = db.raw.select("select id from produit where marque='NOVOSEVEN'").first['id'] as String;
    expect(db.productById(nov)!.origine, 'importe');
  });

  test('identifiant inconnu', () => expect(db.productById('nope'), isNull));

  test('rang des statuts', () {
    expect(ProductStatus.fromDb('en_vigueur').rank, 0);
    expect(ProductStatus.fromDb('non_renouvele').rank, 1);
    expect(ProductStatus.fromDb('retire').rank, 2);
  });

  test('lecture seule', () {
    expect(() => db.raw.execute("delete from produit"), throwsA(isA<SqliteException>()));
  });

  test('fichier invalide', () {
    final dir = Directory.systemTemp.createTempSync();
    final f = File('${dir.path}/x.sqlite')..writeAsStringSync('pas une base');
    expect(() => NomenclatureDb.open(f.path), throwsA(isA<NomenclatureFormatError>()));
    final empty = sqlite3.open('${dir.path}/vide.sqlite')..execute('create table t(a)');
    empty.close();
    expect(() => NomenclatureDb.open('${dir.path}/vide.sqlite'), throwsA(isA<NomenclatureFormatError>()));
  });
}
