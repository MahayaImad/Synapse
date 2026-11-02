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

  test('conteneurs de statut de même ton (clairs en thème clair)', () {
    final theme = buildTheme(fallbackScheme(Brightness.light));
    final w = theme.extension<StatusColors>()!;
    expect(w.warningContainer.computeLuminance(), greaterThan(0.5));
    expect((w.warningContainer.computeLuminance() - theme.colorScheme.errorContainer.computeLuminance()).abs(), lessThan(0.25));
  });

  test('pas de coupure après « / »', () => expect(noBreakAfterSlash('B/10'), 'B/\u206010'));

  group('direction El Hana', () {
    double hue(Color c) => HSLColor.fromColor(c).hue;

    test('bleu azur pour les actions, lisible', () {
      for (final b in Brightness.values) {
        final s = buildTheme(fallbackScheme(b)).colorScheme;
        expect(hue(s.primary), inInclusiveRange(200, 225), reason: '$b');
        expect(HSLColor.fromColor(s.primary).saturation, greaterThan(0.45), reason: '$b');
        expect(contrast(s.onPrimary, s.primary), greaterThanOrEqualTo(4.5), reason: '$b');
        expect(contrast(s.primary, s.surface), greaterThanOrEqualTo(3.0), reason: '$b icônes');
      }
    });

    test('clair : fond gris clair, cartes blanches, champs bleu pâle', () {
      final t = buildTheme(fallbackScheme(Brightness.light));
      final s = t.colorScheme;
      expect(s.surface.computeLuminance(), inInclusiveRange(0.82, 0.94)); // gris, pas blanc
      expect(s.surfaceContainerLowest, const Color(0xFFFFFFFF));
      expect(t.cardTheme.color, s.surfaceContainerLowest);
      final fill = t.extension<FieldColors>()!.fill;
      expect(hue(fill), inInclusiveRange(200, 225));
      expect(fill.computeLuminance(), greaterThan(0.6));
      expect(contrast(s.onSurfaceVariant, fill), greaterThanOrEqualTo(4.5));
    });

    test('sombre : gris ardoise, cartes plus claires que le fond', () {
      final s = buildTheme(fallbackScheme(Brightness.dark)).colorScheme;
      expect(s.surface.computeLuminance(), lessThan(0.03));
      expect(s.surfaceContainerLowest.computeLuminance(), greaterThan(s.surface.computeLuminance()));
      expect(contrast(s.onSurface, s.surfaceContainerLowest), greaterThanOrEqualTo(4.5));
      expect(contrast(s.onSurfaceVariant, s.surfaceContainerLowest), greaterThanOrEqualTo(4.5));
    });

    test('séparateurs et bords gris-bleu neutres (pas de lavande)', () {
      final t = buildTheme(fallbackScheme(Brightness.light));
      expect(t.dividerTheme.color, const Color(0xFFE3E8EF));
      expect(t.colorScheme.outlineVariant, const Color(0xFFE3E8EF));
      expect(t.cardTheme.elevation, greaterThan(0)); // ombre douce, pas de bordure
      expect((t.cardTheme.shape! as RoundedRectangleBorder).side, BorderSide.none);
    });

    test('police arrondie Nunito', () {
      expect(buildTheme(fallbackScheme(Brightness.light)).textTheme.bodyLarge!.fontFamily, 'Nunito');
    });

    test('aucun orange décoratif : seul « non renouvelé » est ambre', () {
      final s = buildTheme(fallbackScheme(Brightness.light)).colorScheme;
      for (final c in [s.primary, s.secondary, s.tertiary]) {
        expect(hue(c), isNot(inInclusiveRange(20, 60)));
      }
    });
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
    expect(Settings.validBuildUrl('http://maj.dz/m.json'), '');
    expect(Settings.validBuildUrl('https://maj.dz/m.json'), 'https://maj.dz/m.json');
  });
}

