import 'dart:io';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:synapse/app.dart';
import 'package:synapse/data/settings.dart';
import 'package:synapse/data/store.dart';
import 'package:synapse/data/update_service.dart';

import 'data/store_test.dart' show assetsFrom;

/// Dépendances réelles sur le fichier de test, réseau simulé.
class Harness {
  Harness._(this.dir, this.store, this.settings, this.updates);

  final Directory dir;
  final NomenclatureStore store;
  final Settings settings;
  final UpdateService updates;

  static Future<Harness> create({http.Client? client, String manifestUrl = ''}) async {
    final dir = Directory.systemTemp.createTempSync();
    final store = NomenclatureStore(dir: dir, loadAsset: assetsFrom(File('test/fixtures/nomenclature-test.sqlite'), '2026-08'));
    await store.init();
    SharedPreferences.setMockInitialValues(manifestUrl.isEmpty ? {} : {'manifest_url': manifestUrl});
    final settings = await Settings.load();
    final updates = UpdateService(
      client: client ?? MockClient((_) async => http.Response('', 404)),
      store: store,
      manifestUrl: () async => settings.manifestUrl,
      onUnmeteredNetwork: () async => true,
    );
    return Harness._(dir, store, settings, updates);
  }

  Widget app(Widget home, {GlobalKey<ScaffoldMessengerState>? messenger}) =>
      SynapseApp(store: store, updates: updates, settings: settings, home: home, messengerKey: messenger);

  void dispose() {
    store.dispose();
    dir.deleteSync(recursive: true);
  }
}
