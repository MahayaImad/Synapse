import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';

/// Téléphone 390×844 dp ; thème, échelle de police et luminosité configurables.
void phone(WidgetTester tester, {double textScale = 1.0, Brightness brightness = Brightness.light}) {
  tester.view.physicalSize = const Size(390 * 2, 844 * 2);
  tester.view.devicePixelRatio = 2;
  tester.platformDispatcher.textScaleFactorTestValue = textScale;
  tester.platformDispatcher.platformBrightnessTestValue = brightness;
  FocusManager.instance.highlightStrategy = FocusHighlightStrategy.alwaysTouch; // téléphone tactile
  addTearDown(() {
    tester.view.reset();
    tester.platformDispatcher.clearTextScaleFactorTestValue();
    tester.platformDispatcher.clearPlatformBrightnessTestValue();
  });
}

Future<void> typeQuery(WidgetTester tester, String q) async {
  await tester.enterText(find.byType(TextField), q);
  await tester.pump(const Duration(milliseconds: 200));
  await tester.pumpAndSettle();
}

/// Capture avec les vraies ombres (flutter_test les remplace sinon par un trait noir).
Future<void> golden(WidgetTester tester, Finder finder, String name) async {
  debugDisableShadows = false;
  try {
    tester.binding.scheduleFrame();
    await tester.pumpAndSettle();
    await expectLater(finder, matchesGoldenFile('../goldens/$name.png'));
  } finally {
    debugDisableShadows = true;
  }
}
