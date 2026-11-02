import 'package:flutter_test/flutter_test.dart';
import 'package:synapse/app.dart';

void main() {
  testWidgets('échec au démarrage : message et bouton Réessayer', (tester) async {
    var retries = 0;
    await tester.pumpWidget(StartupErrorApp(error: 'No space left on device', onRetry: () => retries++));
    expect(find.textContaining('Impossible de préparer la nomenclature'), findsOneWidget);
    expect(find.textContaining('No space left on device'), findsOneWidget);
    await tester.tap(find.text('Réessayer'));
    expect(retries, 1);
  });
}
