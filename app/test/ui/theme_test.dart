import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:synapse/data/settings.dart';
import 'package:synapse/ui/format.dart';
import 'package:synapse/ui/theme.dart';

double contrast(Color a, Color b) {
  final la = a.computeLuminance(), lb = b.computeLuminance();
  return (max(la, lb) + 0.05) / (min(la, lb) + 0.05);
}

void main() {
  for (final b in Brightness.values) {
    test('contrastes du schéma de repli ($b)', () {
      final theme = buildTheme(fallbackScheme(b));
      final s = theme.colorScheme, w = theme.extension<StatusColors>()!;
      expect(contrast(s.onSurface, s.surface), greaterThanOrEqualTo(4.5));
      expect(contrast(s.onSurfaceVariant, s.surface), greaterThanOrEqualTo(4.5));
      expect(contrast(s.onErrorContainer, s.errorContainer), greaterThanOrEqualTo(4.5));
      expect(contrast(w.onWarningContainer, w.warningContainer), greaterThanOrEqualTo(4.5));
      expect(theme.useMaterial3, isTrue);
    });
  }

  test('couleur d\'avertissement harmonisée avec un schéma dynamique', () {
    for (final b in Brightness.values) {
      final w = buildTheme(schemeFor(b, const Color(0xFF6750A4))).extension<StatusColors>()!;
      expect(contrast(w.onWarningContainer, w.warningContainer), greaterThanOrEqualTo(4.5));
    }
  });

  test('libellé de version', () {
    expect(versionLabel('2026-08'), 'août 2026');
    expect(versionLabel('2027-02'), 'février 2027');
    expect(versionLabel('n/a'), 'n/a');
  });

  test('réglages : URL du manifeste', () async {
    SharedPreferences.setMockInitialValues({});
    final s = await Settings.load();
    expect(s.manifestUrl, Settings.buildManifestUrl);
    await s.setManifestUrl('https://maj.example.dz/manifest.json');
    expect((await Settings.load()).manifestUrl, 'https://maj.example.dz/manifest.json');
    expect(() => s.setManifestUrl('http://non-securise.dz/m.json'), throwsArgumentError);
    await s.setManifestUrl('');
    expect((await Settings.load()).manifestUrl, '');
  });
}
