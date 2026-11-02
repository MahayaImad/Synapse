import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:synapse/app.dart';
import 'package:synapse/data/update_service.dart';
import 'package:synapse/ui/search/search_screen.dart';

import '../app_harness.dart';
import 'screen.dart';

void main() {
  testWidgets('mise à jour automatique : snackbar seulement si installée', (tester) async {
    final h = (await tester.runAsync(Harness.create))!;
    addTearDown(h.dispose);
    phone(tester);
    final messenger = GlobalKey<ScaffoldMessengerState>();
    await tester.pumpWidget(h.app(const SearchScreen(), messenger: messenger));
    await tester.pumpAndSettle();
    final at = DateTime(2026, 10, 3);
    notifyUpdate(messenger, UpdateResult(UpdateOutcome.upToDate, at));
    notifyUpdate(messenger, UpdateResult(UpdateOutcome.failed, at, error: 'HTTP 404'));
    await tester.pump();
    expect(find.byType(SnackBar), findsNothing);
    notifyUpdate(messenger, UpdateResult(UpdateOutcome.updated, at, newVersion: '2026-09'));
    await tester.pump();
    expect(find.text('Nomenclature mise à jour : septembre 2026'), findsOneWidget);
  });
}
