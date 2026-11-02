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
      this.messengerKey, this.dynamicSeed});

  final NomenclatureStore store;
  final UpdateService updates;
  final Settings settings;
  final Widget home;
  final GlobalKey<ScaffoldMessengerState>? messengerKey;

  /// Couleur principale du thème système (Material You, Android 12+), sinon null.
  final Color? dynamicSeed;

  @override
  Widget build(BuildContext context) {
    return Services(
      store: store,
      updates: updates,
      settings: settings,
      child: MaterialApp(
        onGenerateTitle: (c) => AppLocalizations.of(c).appTitle,
        scaffoldMessengerKey: messengerKey,
        theme: buildTheme(schemeFor(Brightness.light, dynamicSeed)),
        darkTheme: buildTheme(schemeFor(Brightness.dark, dynamicSeed)),
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
