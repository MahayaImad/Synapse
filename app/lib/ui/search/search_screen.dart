import 'dart:async';

import 'package:flutter/material.dart';

import '../../data/product.dart';
import '../../data/search.dart';
import '../../data/store.dart';
import '../../l10n/app_localizations.dart';
import '../../services.dart';
import '../about/about_screen.dart';
import '../format.dart';
import '../product/product_screen.dart';
import '../widgets/product_tile.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _controller = TextEditingController();
  Timer? _debounce;
  List<Product> _results = const [];
  String _query = '';
  NomenclatureStore? _store;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final store = Services.of(context).store;
    if (!identical(store, _store)) {
      _store?.removeListener(_rerun);
      _store = store..addListener(_rerun);
    }
  }

  @override
  void dispose() {
    _store?.removeListener(_rerun);
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _rerun() => _run(_query);

  void _onChanged(String q) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 120), () => _run(q));
  }

  void _run(String q) {
    if (!mounted) return;
    setState(() {
      _query = q;
      _results = q.trim().isEmpty ? const [] : search(_store!.db, q);
    });
  }

  void _open(Product p) =>
      Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => ProductScreen(productId: p.id)));

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final version = versionLabel(Services.of(context).store.meta.version);
    return Scaffold(
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 16, 0),
              child: SearchBar(
                controller: _controller,
                autoFocus: true,
                hintText: l.searchHint,
                // Barre plate sur fond tonal, comme les apps Google de référence.
                elevation: const WidgetStatePropertyAll(0),
                backgroundColor: WidgetStatePropertyAll(theme.colorScheme.surfaceContainerHigh),
                leading: const Padding(
                  padding: EdgeInsetsDirectional.only(start: 8),
                  child: Icon(Icons.search),
                ),
                trailing: [
                  if (_query.isNotEmpty)
                    IconButton(
                      tooltip: MaterialLocalizations.of(context).deleteButtonTooltip,
                      icon: const Icon(Icons.close),
                      onPressed: () {
                        _controller.clear();
                        _run('');
                      },
                    ),
                  PopupMenuButton<void>(
                    tooltip: MaterialLocalizations.of(context).showMenuTooltip,
                    itemBuilder: (_) => [
                      PopupMenuItem<void>(
                        onTap: () => Navigator.of(context)
                            .push(MaterialPageRoute<void>(builder: (_) => const AboutScreen())),
                        child: Text(l.about),
                      ),
                    ],
                  ),
                ],
                textInputAction: TextInputAction.search,
                onChanged: _onChanged,
                onSubmitted: _run,
              ),
            ),
            Padding(
              padding: const EdgeInsetsDirectional.fromSTEB(28, 8, 28, 4),
              child: Text(l.nomenclatureVersion(version),
                  style: theme.textTheme.labelMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            ),
            Expanded(child: _body(l, theme, version)),
          ],
        ),
      ),
    );
  }

  Widget _body(AppLocalizations l, ThemeData theme, String version) {
    if (_query.trim().isEmpty) {
      return _Message(icon: Icons.manage_search, title: l.searchEmptyHelp);
    }
    if (_results.isEmpty) {
      return _Message(icon: Icons.search_off, title: l.noResults(_query.trim()), body: l.noResultsHelp(version));
    }
    return ListView.builder(
      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
      itemCount: _results.length,
      itemBuilder: (_, i) => ProductTile(_results[i], onTap: () => _open(_results[i])),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({required this.icon, required this.title, this.body});

  final IconData icon;
  final String title;
  final String? body;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsetsDirectional.fromSTEB(32, 48, 32, 32),
      child: Column(children: [
        Icon(icon, size: 48, color: theme.colorScheme.onSurfaceVariant),
        const SizedBox(height: 16),
        Text(title, textAlign: TextAlign.center, style: theme.textTheme.titleMedium),
        if (body != null) ...[
          const SizedBox(height: 8),
          Text(body!, textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium!.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        ],
      ]),
    );
  }
}
