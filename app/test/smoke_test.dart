import 'package:flutter_test/flutter_test.dart';
import 'package:synapse/app.dart';

void main() {
  testWidgets('app démarre', (tester) async {
    await tester.pumpWidget(const SynapseShellPreview());
    expect(find.text('Synapse'), findsOneWidget);
  });
}
