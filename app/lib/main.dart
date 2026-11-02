import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dynamic_color/dynamic_color.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

import 'app.dart';
import 'data/settings.dart';
import 'data/store.dart';
import 'data/update_service.dart';
import 'ui/home.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const PreparingApp());
  final dir = await getApplicationSupportDirectory();
  final store = NomenclatureStore(dir: dir, loadAsset: rootBundle.load);
  await store.init();
  final settings = await Settings.load();
  final updates = UpdateService(
    client: http.Client(),
    store: store,
    manifestUrl: () async => settings.manifestUrl,
    onUnmeteredNetwork: () async => (await Connectivity().checkConnectivity()).contains(ConnectivityResult.wifi),
  );
  final messenger = GlobalKey<ScaffoldMessengerState>();
  Color? seed;
  try {
    final palette = await DynamicColorPlugin.getCorePalette();
    if (palette != null) seed = Color(palette.primary.get(40));
  } catch (_) {
    seed = null; // pas de couleurs dynamiques : schéma statique
  }
  runApp(SynapseApp(store: store, updates: updates, settings: settings, messengerKey: messenger, dynamicSeed: seed,
      home: const HomeScreen()));
  Future<void> tick() async {
    if (updates.due) await updates.check();
  }

  unawaited(tick());
  Timer.periodic(const Duration(hours: 1), (_) => tick());
}
