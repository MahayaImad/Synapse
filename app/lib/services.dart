import 'package:flutter/widgets.dart';

import 'data/settings.dart';
import 'data/store.dart';
import 'data/update_service.dart';

/// Dépendances de l'app, accessibles depuis tous les écrans.
class Services extends InheritedWidget {
  const Services({super.key, required this.store, required this.updates, required this.settings, required super.child});

  final NomenclatureStore store;
  final UpdateService updates;
  final Settings settings;

  static Services of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<Services>() ?? (throw StateError('Services absent'));

  @override
  bool updateShouldNotify(Services old) =>
      old.store != store || old.updates != updates || old.settings != settings;
}
