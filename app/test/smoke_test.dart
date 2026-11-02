import 'package:flutter_test/flutter_test.dart';
import 'package:synapse/ui/search/search_screen.dart';

import 'app_harness.dart';

void main() {
  testWidgets('app démarre', (tester) async {
    final h = await tester.runAsync(Harness.create);
    addTearDown(h!.dispose);
    await tester.pumpWidget(h.app(const SearchScreen()));
    await tester.pumpAndSettle();
    expect(find.byType(SearchScreen), findsOneWidget);
  });
}
