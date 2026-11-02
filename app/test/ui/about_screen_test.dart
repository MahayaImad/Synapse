import 'dart:convert';

import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:synapse/ui/about/about_screen.dart';

import '../app_harness.dart';
import '../data/store_test.dart' show relabel;
import 'screen.dart';

const url = 'https://maj.example.dz/manifest.json';

void main() {
  late Harness h;
  tearDown(() => h.dispose());

  Future<void> open(WidgetTester tester, {http.Client? client, String manifestUrl = ''}) async {
    h = (await tester.runAsync(() => Harness.create(client: client, manifestUrl: manifestUrl)))!;
    phone(tester);
    await tester.pumpWidget(h.app(const AboutScreen()));
    await tester.pumpAndSettle();
  }

  Future<void> tapAndWait(WidgetTester tester, Finder f) async {
    await tester.ensureVisible(f);
    await tester.tap(f);
    await tester.pump();
    // E/S réelles (fichiers, SQLite) : alterner attente réelle et images jusqu'à la fin de la vérification.
    for (var i = 0; i < 40 && find.byType(CircularProgressIndicator).evaluate().isNotEmpty; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 50)));
      await tester.pump(const Duration(milliseconds: 50));
    }
    await tester.pump(const Duration(milliseconds: 500));
  }

  testWidgets('informations de version et mention', (tester) async {
    await open(tester);
    expect(find.text('août 2026 (2026-08)'), findsOneWidget);
    expect(find.text('31/08/2026'), findsOneWidget);
    expect(find.text('43'), findsOneWidget);
    expect(find.textContaining('La décision reste au pharmacien', skipOffstage: false), findsOneWidget);
  });

  testWidgets('URL vide : mises à jour désactivées', (tester) async {
    await open(tester);
    expect(find.text('Mises à jour désactivées : aucune adresse de manifeste.'), findsOneWidget);
  });

  testWidgets('vérifier maintenant : mise à jour installée', (tester) async {
    late List<int> file;
    final client = MockClient((req) async {
      if (req.url.toString() == url) {
        return http.Response(jsonEncode({
          'version': '2026-09', 'reference_date': '2026-09-30', 'file': 'n.sqlite', 'size': file.length,
          'sha256': sha256.convert(file).toString(), 'published_at': '2026-10-02T08:00:00+00:00',
        }), 200);
      }
      return http.Response.bytes(file, 200);
    });
    await open(tester, client: client, manifestUrl: url);
    file = (await tester.runAsync(() async => relabel(h.dir, '2026-09', name: 'src.sqlite').readAsBytesSync()))!;
    await tapAndWait(tester, find.text('Vérifier maintenant'));
    expect(find.text('Nomenclature mise à jour : septembre 2026'), findsWidgets);
    expect(find.text('septembre 2026 (2026-09)'), findsOneWidget);
  });

  testWidgets('vérifier maintenant : échec, version inchangée', (tester) async {
    await open(tester, client: MockClient((_) async => http.Response('', 404)), manifestUrl: url);
    await tapAndWait(tester, find.text('Vérifier maintenant'));
    expect(find.textContaining('Échec de la mise à jour'), findsWidgets);
    expect(find.text('août 2026 (2026-08)'), findsOneWidget);
  });

  testWidgets('adresse du manifeste : https seulement', (tester) async {
    await open(tester);
    final field = find.byKey(const Key('manifest-url'));
    await tester.ensureVisible(field);
    await tester.enterText(field, 'http://non-securise.dz/m.json');
    await tapAndWait(tester, find.text('Enregistrer'));
    expect(find.text('Adresse https:// attendue'), findsOneWidget);
    expect(h.settings.manifestUrl, '');
    await tester.enterText(field, url);
    await tapAndWait(tester, find.text('Enregistrer'));
    expect(h.settings.manifestUrl, url);
    expect(find.text('Adresse enregistrée'), findsOneWidget);
  });

  testWidgets('golden about', (tester) async {
    await open(tester, manifestUrl: url);
    await golden(tester, find.byType(AboutScreen), 'about_light');
  });
}
