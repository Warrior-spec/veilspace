import 'package:flutter/material.dart';

import 'api.dart';
import 'auth_screen.dart';

void main() => runApp(const VeilSpaceApp());

class VeilSpaceApp extends StatefulWidget {
  final ApiClient? api;
  const VeilSpaceApp({super.key, this.api});

  @override
  State<VeilSpaceApp> createState() => _VeilSpaceAppState();
}

class _VeilSpaceAppState extends State<VeilSpaceApp> {
  late final ApiClient api;
  Session? session;

  @override
  void initState() {
    super.initState();
    api = widget.api ?? ApiClient();
  }

  @override
  void dispose() {
    api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VeilSpace',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF146C60)),
        useMaterial3: true,
      ),
      home: session == null
          ? AuthScreen(
              api: api,
              onAuthenticated: (value) => setState(() => session = value),
            )
          : WorkspaceFoundation(
              api: api,
              session: session!,
              onSignedOut: () => setState(() => session = null),
            ),
    );
  }
}

class WorkspaceFoundation extends StatefulWidget {
  final ApiClient api;
  final Session session;
  final VoidCallback onSignedOut;
  const WorkspaceFoundation({
    super.key,
    required this.api,
    required this.session,
    required this.onSignedOut,
  });

  @override
  State<WorkspaceFoundation> createState() => _WorkspaceFoundationState();
}

class _WorkspaceFoundationState extends State<WorkspaceFoundation> {
  int selected = 0;
  bool signingOut = false;
  static const labels = ['My Files', 'Shared Files', 'Pending'];

  Future<void> signOut() async {
    setState(() => signingOut = true);
    try {
      await widget.api.logout(widget.session);
      if (mounted) widget.onSignedOut();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not sign out. Please try again.'),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => signingOut = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('VeilSpace'),
        actions: [
          IconButton(
            onPressed: signingOut ? null : signOut,
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  labels[selected],
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 12),
                Text(widget.session.email),
                const SizedBox(height: 24),
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(20),
                    child: Text('No files yet.'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: selected,
        onDestinationSelected: (value) => setState(() => selected = value),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.folder_outlined),
            label: 'My Files',
          ),
          NavigationDestination(
            icon: Icon(Icons.people_outline),
            label: 'Shared Files',
          ),
          NavigationDestination(
            icon: Icon(Icons.hourglass_empty),
            label: 'Pending',
          ),
        ],
      ),
    );
  }
}
