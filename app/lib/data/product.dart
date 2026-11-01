import 'package:sqlite3/sqlite3.dart';

/// Statut réglementaire d'un produit dans la nomenclature.
enum ProductStatus {
  enVigueur('en_vigueur', 0),
  nonRenouvele('non_renouvele', 1),
  retire('retire', 2);

  const ProductStatus(this.dbValue, this.rank);

  final String dbValue;

  /// Ordre d'affichage : en vigueur, puis non renouvelé, puis retiré.
  final int rank;

  static ProductStatus fromDb(String value) =>
      values.firstWhere((s) => s.dbValue == value, orElse: () => throw FormatException('Statut inconnu : $value'));
}

/// Une présentation de la nomenclature, telle que publiée par synapse-admin.
class Product {
  const Product({
    required this.id,
    required this.marque,
    required this.dci,
    required this.codeDci,
    required this.forme,
    required this.dosage,
    required this.conditionnement,
    required this.liste,
    required this.statut,
    required this.origine,
    required this.dateRetrait,
    required this.typeRetrait,
    required this.motifRetrait,
    required this.labo,
    required this.pays,
    required this.type,
    required this.hopital,
    required this.officine,
    required this.nEnregistrement,
  });

  factory Product.fromRow(Row r) => Product(
        id: r['id'] as String,
        marque: r['marque'] as String,
        dci: r['dci'] as String,
        codeDci: r['code_dci'] as String,
        forme: r['forme'] as String,
        dosage: r['dosage'] as String,
        conditionnement: r['conditionnement'] as String,
        liste: r['liste'] as String?,
        statut: ProductStatus.fromDb(r['statut'] as String),
        origine: r['origine'] as String?,
        dateRetrait: _date(r['date_retrait'] as String?),
        typeRetrait: r['type_retrait'] as String?,
        motifRetrait: r['motif_retrait'] as String?,
        labo: r['labo'] as String,
        pays: r['pays'] as String,
        type: r['type'] as String?,
        hopital: (r['hopital'] as int) != 0,
        officine: (r['officine'] as int) != 0,
        nEnregistrement: r['n_enregistrement'] as String,
      );

  final String id;
  final String marque;
  final String dci;
  final String codeDci;
  final String forme;
  final String dosage;
  final String conditionnement;

  /// `I`, `II`, `STUPEFIANT` ou null (non classé).
  final String? liste;
  final ProductStatus statut;

  /// `fabrique_localement`, `importe` ou null.
  final String? origine;
  final DateTime? dateRetrait;

  /// `RETRAIT`, `ABROGATION` ou null.
  final String? typeRetrait;
  final String? motifRetrait;
  final String labo;
  final String pays;

  /// `GE` (générique), `RE` (référence), `BIO` ou null.
  final String? type;
  final bool hopital;
  final bool officine;
  final String nEnregistrement;

  static DateTime? _date(String? iso) => iso == null ? null : DateTime.parse(iso);

  @override
  bool operator ==(Object other) => other is Product && other.id == id;

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() => 'Product($marque $dosage $forme, ${statut.dbValue})';
}

class NomenclatureMeta {
  const NomenclatureMeta({required this.version, required this.referenceDate, required this.products, required this.publishedAt});

  /// Libellé AAAA-MM, comparable par ordre lexicographique.
  final String version;
  final DateTime referenceDate;
  final int products;
  final DateTime publishedAt;
}
