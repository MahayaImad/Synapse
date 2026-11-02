import 'dart:convert';
import 'dart:io';

const fixtureDb = 'test/fixtures/nomenclature-test.sqlite';

List<Map<String, dynamic>> loadCases(String name) =>
    (jsonDecode(File('test/fixtures/$name').readAsStringSync()) as List).cast<Map<String, dynamic>>();

/// Copie le fichier de test dans un dossier temporaire (pour les tests qui le modifient).
File copyFixture(Directory dir, [String name = 'copie.sqlite']) =>
    File(fixtureDb).copySync('${dir.path}/$name');
