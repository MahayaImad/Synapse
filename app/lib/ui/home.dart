import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';

/// Écran d'accueil provisoire, remplacé par l'écran de recherche (étape 9).
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: Text(AppLocalizations.of(context).appTitle)));
}
