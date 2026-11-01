import 'package:flutter/material.dart';

/// Coquille minimale ; remplacée par SynapseApp à l'étape 8.
class SynapseShellPreview extends StatelessWidget {
  const SynapseShellPreview({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Synapse',
      theme: ThemeData(useMaterial3: true),
      home: Scaffold(appBar: AppBar(title: const Text('Synapse'))),
    );
  }
}
