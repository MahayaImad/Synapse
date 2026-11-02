import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';

/// À propos et mises à jour (complété à l'étape 11).
class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: Text(AppLocalizations.of(context).about)));
}
