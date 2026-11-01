import 'nomenclature_db.dart';
import 'product.dart';
import 'text.dart';

class DosageGroup {
  const DosageGroup(this.dosage, this.products);

  /// Dosage tel qu'écrit dans la nomenclature (premier produit du groupe).
  final String dosage;
  final List<Product> products;
}

/// Produits de même code DCI (même molécule, même forme), hors le produit lui-même.
class Equivalents {
  const Equivalents(this.sameDosage, this.otherDosages);

  final List<Product> sameDosage;
  final List<DosageGroup> otherDosages;

  List<Product> get activeSameDosage => [for (final p in sameDosage) if (p.statut == ProductStatus.enVigueur) p];

  bool get isEmpty => sameDosage.isEmpty && otherDosages.isEmpty;
}

int _order(Product a, Product b) {
  final r = a.statut.rank.compareTo(b.statut.rank);
  if (r != 0) return r;
  final m = a.marque.compareTo(b.marque);
  return m != 0 ? m : a.id.compareTo(b.id);
}

Equivalents equivalentsOf(NomenclatureDb db, Product p) {
  final others = [
    for (final r in db.raw.select('SELECT * FROM produit WHERE code_dci = ? AND id != ?', [p.codeDci, p.id]))
      Product.fromRow(r)
  ]..sort(_order);
  final key = dosageKey(p.dosage);
  final same = [for (final o in others) if (dosageKey(o.dosage) == key) o];
  final groups = <String, List<Product>>{};
  for (final o in others) {
    final k = dosageKey(o.dosage);
    if (k != key) groups.putIfAbsent(k, () => []).add(o);
  }
  final keys = groups.keys.toList()..sort();
  return Equivalents(same, [for (final k in keys) DosageGroup(groups[k]!.first.dosage, groups[k]!)]);
}
