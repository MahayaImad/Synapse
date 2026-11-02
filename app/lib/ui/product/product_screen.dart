import 'package:flutter/material.dart';

import '../../data/equivalents.dart';
import '../../data/product.dart';
import '../../l10n/app_localizations.dart';
import '../../services.dart';
import '../format.dart';
import '../theme.dart';
import '../widgets/product_tile.dart';
import '../widgets/status_chip.dart';

/// Fiche produit : statut d'abord, puis équivalents en vigueur (si besoin), informations et équivalents.
class ProductScreen extends StatelessWidget {
  const ProductScreen({super.key, required this.productId});

  final String productId;

  @override
  Widget build(BuildContext context) {
    final store = Services.of(context).store;
    return ListenableBuilder(
      listenable: store,
      builder: (context, _) {
        final l = AppLocalizations.of(context);
        final db = store.db;
        final p = db.productById(productId);
        final version = versionLabel(db.meta.version);
        if (p == null) {
          final theme = Theme.of(context);
          return Scaffold(
            appBar: AppBar(),
            body: SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(32, 48, 32, 32),
              child: Column(children: [
                Icon(Icons.inventory_2_outlined, size: 48, color: theme.colorScheme.onSurfaceVariant),
                const SizedBox(height: 16),
                Text(l.productGoneTitle, textAlign: TextAlign.center, style: theme.textTheme.titleMedium),
                const SizedBox(height: 8),
                Text(l.productGone(version), textAlign: TextAlign.center,
                    style: theme.textTheme.bodyMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              ]),
            ),
          );
        }
        return _Sheet(product: p, equivalents: equivalentsOf(db, p), version: version);
      },
    );
  }
}

class _Sheet extends StatelessWidget {
  const _Sheet({required this.product, required this.equivalents, required this.version});

  final Product product;
  final Equivalents equivalents;
  final String version;

  void _open(BuildContext context, Product p) =>
      Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => ProductScreen(productId: p.id)));

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final p = product;
    final active = p.statut == ProductStatus.enVigueur;
    final shownOnTop = active ? const <Product>[] : equivalents.activeSameDosage;
    final sameRest = [for (final e in equivalents.sameDosage) if (!shownOnTop.contains(e)) e];
    // Lignes séparées comme dans la liste de résultats.
    List<Widget> tiles(Iterable<Product> ps) => [
          for (final (i, e) in ps.indexed) ...[
            if (i > 0) const Divider(height: 1, indent: 16, endIndent: 16),
            ProductTile(e, onTap: () => _open(context, e)),
          ],
        ];

    return Scaffold(
      body: CustomScrollView(slivers: [
        // Titre centré, toujours visible : le nom du produit reste en haut pendant la lecture de la fiche.
        SliverAppBar(pinned: true, title: Text(p.marque, maxLines: 1, overflow: TextOverflow.ellipsis)),
        SliverPadding(
          padding: const EdgeInsetsDirectional.only(bottom: 24),
          sliver: SliverToBoxAdapter(child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsetsDirectional.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(p.marque, style: theme.textTheme.headlineSmall!.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 4),
                Text(noBreakAfterSlash('${p.dosage} · ${p.forme}'),
                    style: theme.textTheme.bodyLarge!.copyWith(color: theme.colorScheme.onSurfaceVariant, fontFeatures: tabular)),
                const SizedBox(height: 12),
                StatusChip(p.statut, showActive: true),
              ]),
            ),
          ),
          if (!active) ...[
            _StatusBanner(p),
            _Section(title: l.activeEquivalents, children: [
              Column(
                key: const Key('active-equivalents'),
                children: shownOnTop.isEmpty ? [_Note(l.noActiveEquivalent)] : tiles(shownOnTop),
              ),
            ]),
          ],
          _Section(title: l.information, children: [
            _Field(Icons.science_outlined, l.fieldDci, p.dci),
            _Field(Icons.tag, l.fieldCodeDci, p.codeDci, numeric: true),
            _Field(Icons.inventory_2_outlined, l.fieldPackaging, p.conditionnement,
                valueKey: const Key('field-packaging'), numeric: true),
            _Field(Icons.policy_outlined, l.fieldListe, listeLabel(l, p.liste) ?? l.unclassified),
            if (_type(l, p.type) case final t?) _Field(Icons.category_outlined, l.fieldType, t),
            if (_origin(l, p.origine) case final o?) _Field(Icons.factory_outlined, l.fieldOrigin, o),
            _Field(Icons.business_outlined, l.fieldLab, p.pays.isEmpty ? p.labo : '${p.labo} — ${p.pays}'),
            if (_availability(l, p) case final a?) _Field(Icons.local_pharmacy_outlined, l.fieldAvailability, a),
            _Field(Icons.badge_outlined, l.fieldRegistration, p.nEnregistrement, numeric: true),
          ]),
          if (equivalents.isEmpty)
            _Section(title: l.sameDosage, children: [_Note(l.noEquivalent)])
          else ...[
            if (sameRest.isNotEmpty || active)
              _Section(title: l.sameDosage, children: [
                Column(
                  key: const Key('same-dosage'),
                  children: active && sameRest.isEmpty ? [_Note(l.noEquivalent)] : tiles(sameRest),
                ),
              ])
            else
              const SizedBox.shrink(key: Key('same-dosage')),
            if (equivalents.otherDosages.isNotEmpty)
              _Section(title: l.otherDosages, children: [
                Column(
                  key: const Key('other-dosages'),
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    for (final g in equivalents.otherDosages) ...[
                      Padding(
                        padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 16, 0),
                        child: Text(g.isUnknown ? l.dosageUnknown : noBreakAfterSlash(g.dosage),
                            style: theme.textTheme.labelLarge!.copyWith(color: theme.colorScheme.onSurfaceVariant, fontFeatures: tabular)),
                      ),
                      ...tiles(g.products),
                    ],
                  ],
                ),
              ]),
          ],
          Padding(
            padding: const EdgeInsetsDirectional.fromSTEB(24, 12, 24, 0),
            child: Text(l.sourceFooter(version),
                style: theme.textTheme.bodySmall!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          ),
          ])),
        ),
      ]),
    );
  }

  static String? _type(AppLocalizations l, String? t) => switch (t) {
        'GE' => l.typeGE,
        'RE' => l.typeRE,
        'BIO' => l.typeBIO,
        _ => null,
      };

  static String? _origin(AppLocalizations l, String? o) => switch (o) {
        'fabrique_localement' => l.originLocal,
        'importe' => l.originImported,
        _ => null,
      };

  static String? _availability(AppLocalizations l, Product p) => switch ((p.hopital, p.officine)) {
        (true, true) => l.availBoth,
        (true, false) => l.availHospital,
        (false, true) => l.availPharmacy,
        _ => null,
      };
}

class _StatusBanner extends StatelessWidget {
  const _StatusBanner(this.p);

  final Product p;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final retired = p.statut == ProductStatus.retire;
    final warn = theme.extension<StatusColors>()!;
    final bg = retired ? theme.colorScheme.errorContainer : warn.warningContainer;
    final fg = retired ? theme.colorScheme.onErrorContainer : warn.onWarningContainer;
    final title = !retired
        ? l.notRenewed
        : p.dateRetrait != null
            ? l.retiredOn(shortDate(p.dateRetrait!))
            : l.retiredUndated;
    final details = [
      if (p.typeRetrait != null) p.typeRetrait!,
      if (p.motifRetrait != null) p.motifRetrait!,
    ];
    return Padding(
      key: const Key('status-banner'),
      padding: const EdgeInsetsDirectional.fromSTEB(16, 6, 16, 6),
      child: Card.filled(
        margin: EdgeInsets.zero,
        color: bg,
        child: Padding(
          padding: const EdgeInsetsDirectional.all(16),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Icon(retired ? Icons.block : Icons.history, color: fg),
            const SizedBox(width: 16),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(title, style: theme.textTheme.titleMedium!.copyWith(color: fg)),
                for (final d in details) ...[
                  const SizedBox(height: 4),
                  Text(d, style: theme.textTheme.bodyMedium!.copyWith(color: fg)),
                ],
              ]),
            ),
          ]),
        ),
      ),
    );
  }
}

/// Carte blanche titrée qui regroupe une partie de la fiche.
class _Section extends StatelessWidget {
  const _Section({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Padding(
          padding: const EdgeInsetsDirectional.fromSTEB(16, 16, 16, 4),
          child: Semantics(
            header: true,
            child: Text(title,
                style: theme.textTheme.titleLarge!.copyWith(color: theme.colorScheme.onSurface, fontWeight: FontWeight.w600)),
          ),
        ),
        ...children,
        const SizedBox(height: 8),
      ]),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field(this.icon, this.label, this.value, {this.valueKey, this.numeric = false});

  final IconData icon;
  final String label;
  final String value;
  final Key? valueKey;
  final bool numeric;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 16, 8),
      child: MergeSemantics(
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          ExcludeSemantics(child: Icon(icon, size: 24, color: theme.colorScheme.primary)),
          const SizedBox(width: 16),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(label, style: theme.textTheme.labelMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              const SizedBox(height: 2),
              Text(noBreakAfterSlash(value), key: valueKey,
                  style: theme.textTheme.bodyLarge!.copyWith(fontFeatures: numeric ? tabular : null)),
            ]),
          ),
        ]),
      ),
    );
  }
}

class _Note extends StatelessWidget {
  const _Note(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(16, 4, 16, 4),
      child: Text(text, style: theme.textTheme.bodyMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
    );
  }
}
