import 'package:flutter_test/flutter_test.dart';
import 'package:synapse/ui/home.dart';

import 'app_harness.dart';

void main() {
  testWidgets('app démarre', (tester) async {
    final h = await tester.runAsync(Harness.create);
    addTearDown(h!.dispose);
    await tester.pumpWidget(h.app(const HomeScreen()));
    expect(find.text('Synapse'), findsOneWidget);
  });
}
