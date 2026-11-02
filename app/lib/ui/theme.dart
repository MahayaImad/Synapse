import 'package:flutter/material.dart';
import 'package:material_color_utilities/material_color_utilities.dart';

/// Couleur d'avertissement (« non renouvelé »), harmonisée avec le schéma courant.
@immutable
class StatusColors extends ThemeExtension<StatusColors> {
  const StatusColors({required this.warning, required this.onWarning, required this.warningContainer,
      required this.onWarningContainer});

  static const _amber = Color(0xFFB8860B);

  factory StatusColors.forScheme(ColorScheme scheme) {
    final seed = Color(Blend.harmonize(_amber.toARGB32(), scheme.primary.toARGB32()));
    final tonal = ColorScheme.fromSeed(seedColor: seed, brightness: scheme.brightness, dynamicSchemeVariant: DynamicSchemeVariant.fidelity);
    return StatusColors(
      warning: tonal.primary,
      onWarning: tonal.onPrimary,
      warningContainer: tonal.primaryContainer,
      onWarningContainer: tonal.onPrimaryContainer,
    );
  }

  final Color warning;
  final Color onWarning;
  final Color warningContainer;
  final Color onWarningContainer;

  @override
  StatusColors copyWith({Color? warning, Color? onWarning, Color? warningContainer, Color? onWarningContainer}) =>
      StatusColors(
        warning: warning ?? this.warning,
        onWarning: onWarning ?? this.onWarning,
        warningContainer: warningContainer ?? this.warningContainer,
        onWarningContainer: onWarningContainer ?? this.onWarningContainer,
      );

  @override
  StatusColors lerp(StatusColors? other, double t) => other == null
      ? this
      : StatusColors(
          warning: Color.lerp(warning, other.warning, t)!,
          onWarning: Color.lerp(onWarning, other.onWarning, t)!,
          warningContainer: Color.lerp(warningContainer, other.warningContainer, t)!,
          onWarningContainer: Color.lerp(onWarningContainer, other.onWarningContainer, t)!,
        );
}

/// Schéma Material : dérivé de la couleur système quand le téléphone en fournit une, sinon statique.
ColorScheme schemeFor(Brightness brightness, Color? dynamicSeed) => dynamicSeed == null
    ? fallbackScheme(brightness)
    : ColorScheme.fromSeed(seedColor: dynamicSeed, brightness: brightness);

/// Schéma statique quand le téléphone ne fournit pas de couleurs dynamiques (avant Android 12).
ColorScheme fallbackScheme(Brightness brightness) =>
    ColorScheme.fromSeed(seedColor: const Color(0xFF2E5D7A), brightness: brightness);

ThemeData buildTheme(ColorScheme scheme) {
  final base = ThemeData(colorScheme: scheme, useMaterial3: true);
  return base.copyWith(
    extensions: [StatusColors.forScheme(scheme)],
    listTileTheme: const ListTileThemeData(minVerticalPadding: 8),
  );
}
