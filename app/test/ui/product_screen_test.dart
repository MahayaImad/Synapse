import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:synapse/ui/product/product_screen.dart';
import 'package:synapse/ui/widgets/product_tile.dart';

import '../app_harness.dart';
import '../data/fixtures.dart';
import '../data/store_test.dart' show relabel;
import 'screen.dart';

void main() {
  late Harness h;
  setUp(() async => h = await Harness.create());
  tearDown(() => h.dispose());

  String idOf(String marque, String dosage) =>
      h.store.db.raw.select('select id from produit where marque = ? and dosage = ?', [marque, dosage]).first['id'] as String;

  Future<void> open(WidgetTester tester, String id) async {
    await tester.pumpWidget(h.app(ProductScreen(productId: id)));
    await tester.pumpAndSettle();
  }


  testWidgets('produit en vigueur : pas de bandeau, équivalents conformes', (tester) async {
    phone(tester);
    final id = idOf('CETIRIPEX', '10MG');
    await open(tester, id);
    expect(find.byKey(const Key('status-banner')), findsNothing);
    final c = loadCases('equivalents_cases.json').firstWhere((c) => c['id'] == id);
    final same = tester.widgetList<ProductTile>(find.descendant(of: find.byKey(const Key('same-dosage'), skipOffstage: false), matching: find.byType(ProductTile, skipOffstage: false), skipOffstage: false));
    expect(same.map((t) => t.product.id).toList(), c['same_dosage']);
    final others = tester.widgetList<ProductTile>(find.descendant(of: find.byKey(const Key('other-dosages'), skipOffstage: false), matching: find.byType(ProductTile, skipOffstage: false), skipOffstage: false));
    expect(others.map((t) => t.product.id).toList(), [for (final g in c['other_dosages'] as List) ...(g['ids'] as List)]);
    expect(find.text('Source : nomenclature nationale des produits pharmaceutiques, version août 2026.', skipOffstage: false), findsOneWidget);
  });

  testWidgets('produit retiré : bandeau puis équivalents en vigueur avant les informations', (tester) async {
    phone(tester);
    await open(tester, idOf('CETIRIZINE MYLAN', '10MG'));
    expect(find.text('Retiré le 31/03/2024'), findsOneWidget);
    expect(find.text('RETRAIT PAR LE DETENTEUR POUR MOTIF COMMERCIAL'), findsOneWidget);
    final banner = tester.getTopLeft(find.byKey(const Key('status-banner'))).dy;
    final active = tester.getTopLeft(find.text('Équivalents en vigueur — même dosage')).dy;
    final info = tester.getTopLeft(find.text('Informations')).dy;
    expect(banner < active && active < info, isTrue);
    final tiles = tester.widgetList<ProductTile>(find.descendant(of: find.byKey(const Key('active-equivalents')), matching: find.byType(ProductTile, skipOffstage: false), skipOffstage: false));
    expect(tiles.map((t) => t.product.marque), containsAll(['CETIRIPEX', 'ZYTREX', 'HISTARIZINE']));
  });

  testWidgets('retiré sans équivalent en vigueur', (tester) async {
    phone(tester);
    await open(tester, idOf('CLAMOXYL', '1G'));
    expect(find.text('Aucun équivalent en vigueur de même dosage dans la nomenclature.'), findsOneWidget);
  });

  testWidgets('abrogation sans date, non renouvelé', (tester) async {
    phone(tester);
    await open(tester, idOf('PARALGAN', '1G'));
    expect(find.text('Retiré de la nomenclature'), findsOneWidget);
    expect(find.textContaining('ABROGATION'), findsOneWidget);
    await open(tester, idOf('ARTIZ', '10MG'));
    expect(find.text("Décision d'enregistrement non renouvelée"), findsOneWidget);
  });

  testWidgets('informations : origine, type, disponibilité, stupéfiant', (tester) async {
    phone(tester);
    await open(tester, idOf('NOVOSEVEN', '4,8MG'));
    expect(find.text('Importé', skipOffstage: false), findsOneWidget);
    expect(find.text('Biologique', skipOffstage: false), findsOneWidget);
    expect(find.text('NOVO NORDISK — DANEMARK', skipOffstage: false), findsOneWidget);
    await open(tester, idOf('CODOLIPRANE', '500MG/30MG'));
    expect(find.text('Stupéfiant', skipOffstage: false), findsWidgets);
    expect(find.text('Fabriqué localement', skipOffstage: false), findsOneWidget);
    expect(find.text('Hôpital et officine', skipOffstage: false), findsOneWidget);
  });

  testWidgets('conditionnement très long affiché en entier, police ×2 sans débordement', (tester) async {
    phone(tester, textScale: 2.0);
    await open(tester, idOf('COAGIL-VII', '4,8MG'));
    final full = h.store.db.productById(idOf('COAGIL-VII', '4,8MG'))!.conditionnement;
    final t = tester.widget<Text>(find.byKey(const Key('field-packaging'), skipOffstage: false));
    expect((t.data!.replaceAll('⁠', ''), t.maxLines), (full, null));
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -3000));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets('produit absent après une mise à jour', (tester) async {
    phone(tester);
    final id = idOf('DOLIPRANE', '1G');
    await open(tester, id);
    await tester.runAsync(() => h.store.install(relabel(h.dir, '2026-09', name: 'maj.tmp', dropBrand: 'DOLIPRANE')));
    await tester.pumpAndSettle();
    expect(find.text('Ce produit ne figure plus dans la nomenclature septembre 2026.'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('retour système', (tester) async {
    phone(tester);
    await tester.pumpWidget(h.app(Builder(builder: (c) => Scaffold(body: Center(child: TextButton(
        onPressed: () => Navigator.of(c).push(MaterialPageRoute<void>(builder: (_) => ProductScreen(productId: idOf('ZYTREX', '10MG')))),
        child: const Text('ouvrir')))))));
    await tester.tap(find.text('ouvrir'));
    await tester.pumpAndSettle();
    expect(find.byType(ProductScreen), findsOneWidget);
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.byType(ProductScreen), findsNothing);
  });

  for (final (name, marque, dosage, b) in [
    ('product_active_light', 'CETIRIPEX', '10MG', Brightness.light),
    ('product_retired_light', 'CETIRIZINE MYLAN', '10MG', Brightness.light),
    ('product_retired_dark', 'CETIRIZINE MYLAN', '10MG', Brightness.dark),
  ]) {
    testWidgets('golden $name', (tester) async {
      phone(tester, brightness: b);
      await open(tester, idOf(marque, dosage));
      await golden(tester, find.byType(ProductScreen), name);
    });
  }
}

