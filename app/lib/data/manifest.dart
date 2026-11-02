import 'dart:convert';

/// manifest.json publié par `synapse-admin publish`.
class Manifest {
  const Manifest({required this.version, required this.referenceDate, required this.file, required this.size,
      required this.sha256, required this.publishedAt});

  static final _version = RegExp(r'^\d{4}-(0[1-9]|1[0-2])$');
  static final _sha = RegExp(r'^[0-9a-f]{64}$');

  static Manifest parse(String body) {
    final Object? json;
    try {
      json = jsonDecode(body);
    } on FormatException catch (e) {
      throw FormatException('Manifeste illisible : ${e.message}');
    }
    if (json is! Map<String, dynamic>) throw const FormatException('Manifeste : objet JSON attendu');
    final map = json;
    T field<T>(String k) {
      final v = map[k];
      if (v is! T) throw FormatException('Manifeste : champ « $k » absent ou invalide');
      return v;
    }

    final version = field<String>('version');
    final sha = field<String>('sha256');
    final file = field<String>('file');
    if (!_version.hasMatch(version)) throw FormatException('Manifeste : version « $version » invalide');
    if (!_sha.hasMatch(sha)) throw const FormatException('Manifeste : sha256 invalide');
    if (file.contains('/') || file.contains('..') || !file.endsWith('.sqlite')) {
      throw FormatException('Manifeste : nom de fichier « $file » refusé');
    }
    final size = field<int>('size');
    if (size <= 0) throw const FormatException('Manifeste : taille invalide');
    return Manifest(
      version: version,
      referenceDate: DateTime.parse(field<String>('reference_date')),
      file: file,
      size: size,
      sha256: sha,
      publishedAt: DateTime.parse(field<String>('published_at')),
    );
  }

  final String version;
  final DateTime referenceDate;
  final String file;
  final int size;
  final String sha256;
  final DateTime publishedAt;
}
