import 'dart:async';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// Charge Roboto et les icônes Material pour des captures (goldens) lisibles.
Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  TestWidgetsFlutterBinding.ensureInitialized();
  Future<void> load(String family, List<String> files) async {
    final loader = FontLoader(family);
    for (final f in files) {
      loader.addFont(Future.value(ByteData.sublistView(File('test/fonts/$f').readAsBytesSync())));
    }
    await loader.load();
  }

  await load('Roboto', ['Roboto-Regular.ttf', 'Roboto-Medium.ttf', 'Roboto-Bold.ttf']);
  await load('MaterialIcons', ['MaterialIcons-Regular.otf']);
  final nunito = FontLoader('Nunito');
  for (final f in ['Nunito-Regular.ttf', 'Nunito-SemiBold.ttf', 'Nunito-Bold.ttf']) {
    nunito.addFont(Future.value(ByteData.sublistView(File('assets/fonts/$f').readAsBytesSync())));
  }
  await nunito.load();
  await testMain();
}
