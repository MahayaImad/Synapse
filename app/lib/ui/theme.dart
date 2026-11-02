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
    final tonal = ColorScheme.fromSeed(seedColor: seed, brightness: scheme.brightness, dynamicSchemeVariant: DynamicSchemeVariant.tonalSpot);
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

/// Couleurs des champs remplis (bleu pâle arrondi, à la manière de la référence El Hana).
@immutable
class FieldColors extends ThemeExtension<FieldColors> {
  const FieldColors({required this.fill});

  final Color fill;

  @override
  FieldColors copyWith({Color? fill}) => FieldColors(fill: fill ?? this.fill);

  @override
  FieldColors lerp(FieldColors? other, double t) => other == null ? this : FieldColors(fill: Color.lerp(fill, other.fill, t)!);
}

/// Bleu azur de référence (actions, icônes, en-têtes).
const azure = Color(0xFF4A90E2);

/// Schéma Synapse : bleu azur, fond gris clair et cartes blanches (clair), gris ardoise (sombre).
ColorScheme fallbackScheme(Brightness brightness) {
  final base = ColorScheme.fromSeed(seedColor: azure, brightness: brightness);
  return brightness == Brightness.light
      ? base.copyWith(
          primary: const Color(0xFF2F78C4),
          onPrimary: Colors.white,
          surface: const Color(0xFFF3F5F8),
          surfaceContainerLowest: Colors.white,
          surfaceContainerLow: const Color(0xFFF8FAFC),
          outlineVariant: const Color(0xFFE3E8EF),
        )
      : base.copyWith(
          primary: const Color(0xFF8AB8F0),
          onPrimary: const Color(0xFF0B2E55),
          surface: const Color(0xFF1B1F25),
          surfaceContainerLowest: const Color(0xFF262B33),
          surfaceContainerLow: const Color(0xFF222730),
          onSurface: const Color(0xFFE3E6EB),
          outlineVariant: const Color(0xFF353B45),
        );
}

ThemeData buildTheme(ColorScheme scheme) {
  final light = scheme.brightness == Brightness.light;
  final base = ThemeData(colorScheme: scheme, useMaterial3: true, fontFamily: 'Nunito', scaffoldBackgroundColor: scheme.surface);
  return base.copyWith(
    extensions: [
      StatusColors.forScheme(scheme),
      FieldColors(fill: light ? const Color(0xFFDCE9F8) : const Color(0xFF2C3A4D)),
    ],
    cardTheme: CardThemeData(
      color: scheme.surfaceContainerLowest,
      // Carte blanche à ombre douce (référence El Hana) ; pas de teinte de surface.
      elevation: light ? 1.5 : 0,
      shadowColor: const Color(0x33000000),
      surfaceTintColor: Colors.transparent,
      margin: const EdgeInsetsDirectional.symmetric(horizontal: 16, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    appBarTheme: AppBarTheme(
      centerTitle: true,
      backgroundColor: scheme.surfaceContainerLowest,
      surfaceTintColor: Colors.transparent,
      scrolledUnderElevation: 1,
      titleTextStyle: base.textTheme.titleLarge!.copyWith(color: scheme.onSurface),
    ),
    dividerTheme: DividerThemeData(color: scheme.outlineVariant, space: 1, thickness: 1),
    listTileTheme: ListTileThemeData(minVerticalPadding: 8, iconColor: scheme.primary),
    iconTheme: IconThemeData(color: scheme.primary),
  );
}
