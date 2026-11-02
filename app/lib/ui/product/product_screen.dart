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
          return Scaffold(
            appBar: AppBar(),
            body: Padding(
              padding: const EdgeInsetsDirectional.all(24),
              child: Text(l.productGone(version), style: Theme.of(context).textTheme.bodyLarge),
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
    List<Widget> tiles(Iterable<Product> ps) => [for (final e in ps) ProductTile(e, onTap: () => _open(context, e))];

    return Scaffold(
      appBar: AppBar(),
      body: SingleChildScrollView(
        padding: const EdgeInsetsDirectional.only(bottom: 24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Padding(
            padding: const EdgeInsetsDirectional.fromSTEB(16, 0, 16, 16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(p.marque, style: theme.textTheme.headlineSmall),
              const SizedBox(height: 4),
              Text(noBreakAfterSlash('${p.dosage} · ${p.forme}'),
                  style: theme.textTheme.bodyLarge!.copyWith(color: theme.colorScheme.onSurfaceVariant, fontFeatures: tabular)),
            ]),
          ),
          if (!active) ...[
            _StatusBanner(p),
            _Header(l.activeEquivalents),
            Column(
              key: const Key('active-equivalents'),
              children: shownOnTop.isEmpty ? [_Note(l.noActiveEquivalent)] : tiles(shownOnTop),
            ),
          ],
          _Header(l.information),
          _Field(l.fieldDci, p.dci),
          _Field(l.fieldCodeDci, p.codeDci, numeric: true),
          _Field(l.fieldPackaging, p.conditionnement, valueKey: const Key('field-packaging'), numeric: true),
          _Field(l.fieldListe, listeLabel(l, p.liste) ?? l.unclassified),
          if (_type(l, p.type) case final t?) _Field(l.fieldType, t),
          if (_origin(l, p.origine) case final o?) _Field(l.fieldOrigin, o),
          _Field(l.fieldLab, p.pays.isEmpty ? p.labo : '${p.labo} — ${p.pays}'),
          if (_availability(l, p) case final a?) _Field(l.fieldAvailability, a),
          _Field(l.fieldRegistration, p.nEnregistrement, numeric: true),
          if (equivalents.isEmpty)
            ...[_Header(l.sameDosage), _Note(l.noEquivalent)]
          else ...[
            if (sameRest.isNotEmpty || active) _Header(l.sameDosage),
            Column(
              key: const Key('same-dosage'),
              children: active && sameRest.isEmpty ? [_Note(l.noEquivalent)] : tiles(sameRest),
            ),
            if (equivalents.otherDosages.isNotEmpty) _Header(l.otherDosages),
            Column(
              key: const Key('other-dosages'),
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (final g in equivalents.otherDosages) ...[
                  Padding(
                    padding: const EdgeInsetsDirectional.fromSTEB(16, 12, 16, 0),
                    child: Text(noBreakAfterSlash(g.dosage),
                        style: theme.textTheme.labelLarge!.copyWith(color: theme.colorScheme.onSurfaceVariant, fontFeatures: tabular)),
                  ),
                  ...tiles(g.products),
                ],
              ],
            ),
          ],
          Padding(
            padding: const EdgeInsetsDirectional.fromSTEB(16, 24, 16, 0),
            child: Text(l.sourceFooter(version),
                style: theme.textTheme.bodySmall!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          ),
        ]),
      ),
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
      padding: const EdgeInsetsDirectional.fromSTEB(16, 0, 16, 8),
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

class _Header extends StatelessWidget {
  const _Header(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(16, 24, 16, 8),
      child: Semantics(
        header: true,
        child: Text(text, style: theme.textTheme.titleSmall!.copyWith(color: theme.colorScheme.primary)),
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field(this.label, this.value, {this.valueKey, this.numeric = false});

  final String label;
  final String value;
  final Key? valueKey;
  final bool numeric;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(16, 6, 16, 6),
      child: MergeSemantics(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: theme.textTheme.labelMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          const SizedBox(height: 2),
          Text(noBreakAfterSlash(value), key: valueKey,
              style: theme.textTheme.bodyLarge!.copyWith(fontFeatures: numeric ? tabular : null)),
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
