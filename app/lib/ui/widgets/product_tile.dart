import 'package:flutter/material.dart';

import '../../data/product.dart';
import '../../l10n/app_localizations.dart';
import '../format.dart';
import 'status_chip.dart';

const tabular = [FontFeature.tabularFigures()];

/// Une présentation : marque, puis dosage · forme · conditionnement ; statut ou liste à droite.
class ProductTile extends StatelessWidget {
  const ProductTile(this.product, {super.key, this.onTap});

  final Product product;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final p = product;
    // Colonne de droite réservée au statut ; seule exception : le stupéfiant (liste I / II dans la fiche).
    final Widget? trailing = p.statut != ProductStatus.enVigueur
        ? StatusChip(p.statut)
        : p.liste == 'STUPEFIANT'
            ? Text(l.stupefiant,
                style: theme.textTheme.labelMedium!.copyWith(color: theme.colorScheme.error, fontWeight: FontWeight.w600))
            : null;
    return ListTile(
      onTap: onTap,
      title: Text(p.marque, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text(
        noBreakAfterSlash('${p.dosage} · ${p.forme} · ${p.conditionnement}'),
        key: const Key('subtitle'),
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(fontFeatures: tabular),
      ),
      trailing: trailing,
    );
  }
}
