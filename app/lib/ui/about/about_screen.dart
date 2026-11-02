import 'package:flutter/material.dart';

import '../../data/update_service.dart';
import '../../l10n/app_localizations.dart';
import '../../services.dart';
import '../format.dart';

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
          return SingleChildScrollView(
            padding: const EdgeInsetsDirectional.only(bottom: 24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              _Row(l.aboutVersion, '${versionLabel(m.version)} (${m.version})'),
              _Row(l.aboutReference, shortDate(m.referenceDate)),
              _Row(l.aboutProducts, '${m.products}'),
              _Row(l.aboutPublished, shortDate(m.publishedAt.toLocal())),
              _Row(l.aboutLastCheck, status),
              Padding(
                padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 16, 8),
                child: Align(
                  alignment: AlignmentDirectional.centerStart,
                  child: FilledButton.tonalIcon(
                    onPressed: _checking ? null : _check,
                    icon: _checking
                        ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.sync),
                    label: Text(l.checkNow),
                  ),
                ),
              ),
              const Divider(height: 32),
              Padding(
                padding: const EdgeInsetsDirectional.fromSTEB(16, 0, 16, 0),
                child: TextField(
                  key: const Key('manifest-url'),
                  controller: _url,
                  keyboardType: TextInputType.url,
                  autocorrect: false,
                  decoration: InputDecoration(
                    labelText: l.manifestUrl,
                    helperText: l.manifestUrlHelp,
                    errorText: _urlError,
                    border: const OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => _save(),
                ),
              ),
              Padding(
                padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 16, 0),
                child: Align(
                  alignment: AlignmentDirectional.centerEnd,
                  child: TextButton(onPressed: _save, child: Text(l.save)),
                ),
              ),
              const Divider(height: 32),
              Padding(
                padding: const EdgeInsetsDirectional.symmetric(horizontal: 16),
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
  const _Row(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 16, 8),
      child: MergeSemantics(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: theme.textTheme.labelMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          const SizedBox(height: 2),
          Text(value, style: theme.textTheme.bodyLarge),
        ]),
      ),
    );
  }
}
