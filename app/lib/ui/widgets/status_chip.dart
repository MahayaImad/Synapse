import 'package:flutter/material.dart';

import '../../data/product.dart';
import '../../l10n/app_localizations.dart';
import '../theme.dart';

/// Statut réglementaire en étiquette tonale ; rien pour un produit en vigueur.
class StatusChip extends StatelessWidget {
  const StatusChip(this.status, {super.key});

  final ProductStatus status;

  @override
  Widget build(BuildContext context) {
    if (status == ProductStatus.enVigueur) return const SizedBox.shrink();
    final l = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;
    final warn = Theme.of(context).extension<StatusColors>()!;
    final (label, bg, fg) = switch (status) {
      ProductStatus.retire => (l.statusRetire, scheme.errorContainer, scheme.onErrorContainer),
      _ => (l.statusNonRenouvele, warn.warningContainer, warn.onWarningContainer),
    };
    return Semantics(
      label: 'Statut : $label',
      excludeSemantics: true,
      child: DecoratedBox(
        decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8)),
        child: Padding(
          padding: const EdgeInsetsDirectional.symmetric(horizontal: 8, vertical: 4),
          child: Text(label, style: Theme.of(context).textTheme.labelMedium!.copyWith(color: fg)),
        ),
      ),
    );
  }
}

String? listeLabel(AppLocalizations l, String? liste) => switch (liste) {
      'I' => l.listeI,
      'II' => l.listeII,
      'STUPEFIANT' => l.stupefiant,
      _ => null,
    };
