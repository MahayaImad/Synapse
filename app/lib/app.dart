import 'package:flutter/material.dart';

import 'data/settings.dart';
import 'data/store.dart';
import 'data/update_service.dart';
import 'ui/format.dart';
import 'l10n/app_localizations.dart';
import 'services.dart';
import 'ui/theme.dart';

class SynapseApp extends StatelessWidget {
  const SynapseApp({super.key, required this.store, required this.updates, required this.settings, required this.home,
      this.messengerKey});

  final NomenclatureStore store;
  final UpdateService updates;
  final Settings settings;
  final Widget home;
  final GlobalKey<ScaffoldMessengerState>? messengerKey;

  @override
  Widget build(BuildContext context) {
    return Services(
      store: store,
      updates: updates,
      settings: settings,
      child: MaterialApp(
        onGenerateTitle: (c) => AppLocalizations.of(c).appTitle,
        debugShowCheckedModeBanner: false,
        scaffoldMessengerKey: messengerKey,
        theme: buildTheme(fallbackScheme(Brightness.light)),
        darkTheme: buildTheme(fallbackScheme(Brightness.dark)),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('fr'),
        home: home,
      ),
    );
  }
}

/// Écran affiché pendant la copie initiale de la nomenclature embarquée.
class PreparingApp extends StatelessWidget {
  const PreparingApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        theme: buildTheme(fallbackScheme(Brightness.light)),
        darkTheme: buildTheme(fallbackScheme(Brightness.dark)),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('fr'),
        home: Builder(
          builder: (c) => Scaffold(
            body: Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const CircularProgressIndicator(),
                const SizedBox(height: 16),
                Text(AppLocalizations.of(c).preparing),
              ]),
            ),
          ),
        ),
      );
}

/// Signale discrètement une mise à jour installée en arrière-plan (rien pour les autres issues).
void notifyUpdate(GlobalKey<ScaffoldMessengerState> messenger, UpdateResult r) {
  if (r.outcome != UpdateOutcome.updated) return;
  final l = lookupAppLocalizations(const Locale('fr'));
  messenger.currentState?.showSnackBar(SnackBar(content: Text(l.updateDone(versionLabel(r.newVersion ?? '')))));
}

/// Démarrage impossible (stockage plein, fichier illisible) : message et nouvel essai, jamais un chargement sans fin.
class StartupErrorApp extends StatelessWidget {
  const StartupErrorApp({super.key, required this.error, required this.onRetry});

  final String error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => MaterialApp(
        theme: buildTheme(fallbackScheme(Brightness.light)),
        darkTheme: buildTheme(fallbackScheme(Brightness.dark)),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('fr'),
        home: Builder(
          builder: (c) {
            final l = AppLocalizations.of(c);
            final theme = Theme.of(c);
            return Scaffold(
              body: SafeArea(
                child: Padding(
                  padding: const EdgeInsetsDirectional.all(24),
                  child: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
                    const SizedBox(height: 16),
                    Text(l.startupFailed, style: theme.textTheme.titleLarge),
                    const SizedBox(height: 8),
                    Text(error, style: theme.textTheme.bodyMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                    const SizedBox(height: 24),
                    FilledButton(onPressed: onRetry, child: Text(l.retry)),
                  ]),
                ),
              ),
            );
          },
        ),
      );
}
