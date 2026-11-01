import 'nomenclature_db.dart';
import 'product.dart';
import 'text.dart';

/// Portage de backend/src/synapse_admin/search.py — toute modification se fait des deux côtés,
/// et test/fixtures/search_cases.json (généré par le backend) garantit la parité.
const trigramCandidates = 400;
const trigramMinSimilarity = 0.5; // coefficient de Dice sur les trigrammes

const _order = "CASE p.statut WHEN 'en_vigueur' THEN 0 WHEN 'non_renouvele' THEN 1 ELSE 2 END";

List<Product> search(NomenclatureDb db, String query, {int limit = 20}) {
  final tokens = searchTokens(query);
  if (tokens.isEmpty) return const [];
  final fts = tokens.map((t) => '"$t"*').join(' ');
  final rows = db.raw.select(
    'SELECT p.*, bm25(produit_fts) AS score FROM produit_fts JOIN produit p ON p.rowid = produit_fts.rowid '
    'WHERE produit_fts MATCH ? ORDER BY $_order, score LIMIT ?',
    [fts, limit],
  );
  final hits = [for (final r in rows) Product.fromRow(r)];
  final compact = tokens.join();
  if (hits.length < limit && compact.length >= 4) {
    hits.addAll(_fuzzy(db, compact, limit - hits.length, {for (final h in hits) h.id}));
  }
  return hits;
}

/// Fautes de frappe : candidats partageant des trigrammes avec la requête, triés par similarité puis statut.
List<Product> _fuzzy(NomenclatureDb db, String compact, int limit, Set<String> seen) {
  final grams = trigrams(compact).toList()..sort();
  if (grams.isEmpty) return const [];
  final rows = db.raw.select(
    'SELECT p.* FROM marque_trgm JOIN produit p ON p.rowid = marque_trgm.rowid WHERE marque_trgm MATCH ? '
    'ORDER BY bm25(marque_trgm) LIMIT ?',
    [grams.map((g) => '"$g"').join(' OR '), trigramCandidates],
  );
  final q = grams.toSet();
  final scored = <(double, int, int, Product)>[];
  var i = 0;
  for (final r in rows) {
    final p = Product.fromRow(r);
    final index = i++;
    if (seen.contains(p.id)) continue;
    final g = trigrams(p.marque);
    final sim = g.isEmpty ? 0.0 : 2 * q.intersection(g).length / (q.length + g.length);
    if (sim >= trigramMinSimilarity) scored.add((sim, p.statut.rank, index, p));
  }
  // Tri stable comme en Python : similarité décroissante, puis statut, puis ordre bm25.
  scored.sort((a, b) {
    final s = b.$1.compareTo(a.$1);
    if (s != 0) return s;
    final r = a.$2.compareTo(b.$2);
    return r != 0 ? r : a.$3.compareTo(b.$3);
  });
  return [for (final s in scored.take(limit)) s.$4];
}
