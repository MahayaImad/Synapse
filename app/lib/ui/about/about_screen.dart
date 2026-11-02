import 'package:flutter/material.dart';

import '../../data/update_service.dart';
import '../../l10n/app_localizations.dart';
import '../../services.dart';
import '../format.dart';
import '../theme.dart';

/// Version installée, mises à jour et adresse du manifeste.
class AboutScreen extends StatefulWidget {
  const AboutScreen({super.key});

  @override
  State<AboutScreen> createState() => _AboutScreenState();
}

class _AboutScreenState extends State<AboutScreen> {
  final _url = TextEditingController();
  bool _checking = false;
  bool _initialized = false;
  String? _urlError;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      _url.text = Services.of(context).settings.manifestUrl;
      _initialized = true;
    }
  }

  @override
  void dispose() {
    _url.dispose();
    super.dispose();
  }

  Future<void> _check() async {
    final s = Services.of(context);
    final l = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    setState(() => _checking = true);
    final r = await s.updates.check(userInitiated: true);
    if (!mounted) return;
    setState(() => _checking = false);
    messenger.showSnackBar(SnackBar(content: Text(outcomeMessage(l, r))));
  }

  Future<void> _save() async {
    final s = Services.of(context);
    final l = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    try {
      await s.settings.setManifestUrl(_url.text);
    } on ArgumentError {
      setState(() => _urlError = l.manifestUrlInvalid);
      return;
    }
    if (!mounted) return;
    setState(() => _urlError = null);
    messenger.showSnackBar(SnackBar(content: Text(l.saved)));
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final s = Services.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.about)),
      body: ListenableBuilder(
        listenable: s.store,
        builder: (context, _) {
          final m = s.store.meta;
          final last = s.updates.last;
          final status = s.settings.manifestUrl.isEmpty
              ? l.updateDisabled
              : last == null
                  ? l.neverChecked
                  : '${shortDate(last.checkedAt)} ${two(last.checkedAt.hour)}:${two(last.checkedAt.minute)} — ${outcomeMessage(l, last)}';
          final fill = theme.extension<FieldColors>()!.fill;
          return SingleChildScrollView(
            padding: const EdgeInsetsDirectional.only(top: 8, bottom: 24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              Card(
                child: Padding(
                  padding: const EdgeInsetsDirectional.symmetric(vertical: 8),
                  child: Column(children: [
                    _Row(Icons.inventory_2_outlined, l.aboutVersion, versionLabel(m.version)),
                    _Row(Icons.event_outlined, l.aboutReference, shortDate(m.referenceDate)),
                    _Row(Icons.medication_outlined, l.aboutProducts, '${m.products}'),
                    _Row(Icons.publish_outlined, l.aboutPublished, shortDate(m.publishedAt.toLocal())),
                    _Row(Icons.sync, l.aboutLastCheck, status),
                    Padding(
                      padding: const EdgeInsetsDirectional.fromSTEB(56, 8, 16, 8),
                      child: Align(
                        alignment: AlignmentDirectional.centerStart,
                        child: FilledButton.icon(
                          onPressed: _checking ? null : _check,
                          icon: _checking
                              ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                              : const Icon(Icons.sync),
                          label: Text(l.checkNow),
                        ),
                      ),
                    ),
                  ]),
                ),
              ),
              Card(
                child: Padding(
                  padding: const EdgeInsetsDirectional.fromSTEB(16, 16, 16, 8),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                    TextField(
                      key: const Key('manifest-url'),
                      controller: _url,
                      keyboardType: TextInputType.url,
                      autocorrect: false,
                      decoration: InputDecoration(
                        labelText: l.manifestUrl,
                        helperText: l.manifestUrlHelp,
                        errorText: _urlError,
                        filled: true,
                        fillColor: fill,
                        prefixIcon: Icon(Icons.link, color: theme.colorScheme.primary),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
                      ),
                      onSubmitted: (_) => _save(),
                    ),
                    Align(
                      alignment: AlignmentDirectional.centerEnd,
                      child: TextButton(onPressed: _save, child: Text(l.save)),
                    ),
                  ]),
                ),
              ),
              Padding(
                padding: const EdgeInsetsDirectional.fromSTEB(24, 12, 24, 0),
                child: Text(l.disclaimer, style: theme.textTheme.bodyMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              ),
            ]),
          );
        },
      ),
    );
  }
}

String outcomeMessage(AppLocalizations l, UpdateResult r) => switch (r.outcome) {
      UpdateOutcome.updated => l.updateDone(versionLabel(r.newVersion ?? '')),
      UpdateOutcome.upToDate => l.upToDate,
      UpdateOutcome.disabled => l.updateDisabled,
      UpdateOutcome.waitingForWifi => l.waitingForWifi,
      UpdateOutcome.failed => l.updateFailed(r.error ?? '?'),
    };

class _Row extends StatelessWidget {
  const _Row(this.icon, this.label, this.value);

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 16, 8),
      child: MergeSemantics(
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          ExcludeSemantics(child: Icon(icon, color: theme.colorScheme.primary)),
          const SizedBox(width: 16),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(label, style: theme.textTheme.labelMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              const SizedBox(height: 2),
              Text(value, style: theme.textTheme.bodyLarge),
            ]),
          ),
        ]),
      ),
    );
  }
}
