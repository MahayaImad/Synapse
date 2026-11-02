import 'package:flutter/material.dart';

import '../../services.dart';

/// Fiche produit (complétée à l'étape 10).
class ProductScreen extends StatelessWidget {
  const ProductScreen({super.key, required this.productId});

  final String productId;

  @override
  Widget build(BuildContext context) {
    final p = Services.of(context).store.db.productById(productId);
    return Scaffold(appBar: AppBar(title: Text(p?.marque ?? '')));
  }
}
