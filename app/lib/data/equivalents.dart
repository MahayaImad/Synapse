import 'nomenclature_db.dart';
import 'product.dart';
import 'text.dart';

class DosageGroup {
  const DosageGroup(this.dosage, this.products);

  /// Dosage tel qu'écrit dans la nomenclature (premier produit du groupe) ; vide = dosage non précisé.
  final String dosage;

  bool get isUnknown => dosageKey(dosage).isEmpty;
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
  // Un dosage non précisé n'est jamais « le même » : on ne propose pas de substitution incertaine.
  final same = key.isEmpty ? <Product>[] : [for (final o in others) if (dosageKey(o.dosage) == key) o];
  final groups = <String, List<Product>>{};
  for (final o in others) {
    if (!same.contains(o)) groups.putIfAbsent(dosageKey(o.dosage), () => []).add(o);
  }
  final keys = groups.keys.toList()..sort();
  return Equivalents(same, [for (final k in keys) DosageGroup(groups[k]!.first.dosage, groups[k]!)]);
}
