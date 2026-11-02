import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:synapse/ui/product/product_screen.dart';
import 'package:synapse/ui/search/search_screen.dart';
import 'package:synapse/ui/widgets/product_tile.dart';

import '../app_harness.dart';
import 'screen.dart';

void main() {
  late Harness h;
  setUp(() async => h = await Harness.create());
  tearDown(() => h.dispose());

  Future<void> open(WidgetTester tester) async {
    await tester.pumpWidget(h.app(const SearchScreen()));
    await tester.pumpAndSettle();
  }

  testWidgets('champ vide : aide et version', (tester) async {
    phone(tester);
    await open(tester);
    expect(find.text('Marque, DCI, code DCI ou laboratoire'), findsOneWidget);
    expect(find.text('Nomenclature août 2026'), findsOneWidget);
    final field = tester.widget<TextField>(find.byType(TextField));
    expect(field.autofocus, isTrue);
  });

  testWidgets('recherche par préfixe', (tester) async {
    phone(tester);
    await open(tester);
    await typeQuery(tester, 'cetiri');
    final first = tester.widget<ProductTile>(find.byType(ProductTile).first);
    expect(first.product.marque, 'CETIRIPEX');
  });

  testWidgets('statuts visibles sur la ligne', (tester) async {
    phone(tester);
    await open(tester);
    await typeQuery(tester, 'cetirizine');
    expect(find.text('Retiré'), findsOneWidget);
    expect(find.text('Non renouvelé'), findsOneWidget);
    expect(find.bySemanticsLabel(RegExp('Statut : Retiré')), findsOneWidget);
  });

  testWidgets('aucun résultat', (tester) async {
    phone(tester);
    await open(tester);
    await typeQuery(tester, 'zzzz');
    expect(find.text('Aucun produit pour « zzzz »'), findsOneWidget);
    expect(find.textContaining('août 2026'), findsWidgets);
  });

  testWidgets('ouvre la fiche', (tester) async {
    phone(tester);
    await open(tester);
    await typeQuery(tester, 'zytrex enfant');
    await tester.tap(find.byType(ProductTile).first);
    await tester.pumpAndSettle();
    expect(find.byType(ProductScreen), findsOneWidget);
  });

  testWidgets('police ×2 : pas de débordement', (tester) async {
    phone(tester, textScale: 2.0);
    await open(tester);
    await typeQuery(tester, 'eptacog');
    await typeQuery(tester, 'cetirizine');
    expect(tester.takeException(), isNull);
  });

  testWidgets('conditionnement très long : 2 lignes au plus', (tester) async {
    phone(tester);
    await open(tester);
    await typeQuery(tester, 'coagil');
    final subtitle = tester.widget<Text>(find.descendant(of: find.byType(ProductTile).first, matching: find.byKey(const Key('subtitle'))));
    expect((subtitle.maxLines, subtitle.overflow), (2, TextOverflow.ellipsis));
    expect(find.byType(ProductTile).first.evaluate().first.size!.height, lessThan(110));
  });

  testWidgets('cibles tactiles ≥ 48 dp', (tester) async {
    phone(tester);
    await open(tester);
    await typeQuery(tester, 'doliprane');
    // La barre de recherche entière (56 dp) reçoit le tap ; le guide Flutter mesure à tort son champ interne.
    for (final f in [find.byType(SearchBar), find.byType(IconButton), find.byType(PopupMenuButton<void>), find.byType(ProductTile)]) {
      for (final e in f.evaluate()) {
        final size = e.size!;
        expect(size.height >= 48 && size.width >= 48, isTrue, reason: '${e.widget.runtimeType} $size');
      }
    }
    await expectLater(tester, meetsGuideline(textContrastGuideline));
  });

  testWidgets('golden empty', (tester) async {
    phone(tester);
    await open(tester);
    await golden(tester, find.byType(SearchScreen), 'search_empty_light');
  });

  testWidgets('golden no results', (tester) async {
    phone(tester);
    await open(tester);
    await typeQuery(tester, 'zzzz');
    await golden(tester, find.byType(SearchScreen), 'search_noresults_light');
  });

  for (final (name, scale, b) in [('light', 1.0, Brightness.light), ('dark', 1.0, Brightness.dark), ('font130', 1.3, Brightness.light)]) {
    testWidgets('golden $name', (tester) async {
      phone(tester, textScale: scale, brightness: b);
      await open(tester);
      await typeQuery(tester, 'cetirizine');
      await golden(tester, find.byType(SearchScreen), 'search_$name');
    });
  }
}
