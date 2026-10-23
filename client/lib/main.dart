import 'package:flutter/material.dart';

void main() => runApp(const VeilSpaceApp());

class VeilSpaceApp extends StatelessWidget {
  const VeilSpaceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VeilSpace',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF146C60)),
        useMaterial3: true,
      ),
      home: const WorkspaceFoundation(),
    );
  }
}

class WorkspaceFoundation extends StatefulWidget {
  const WorkspaceFoundation({super.key});

  @override
  State<WorkspaceFoundation> createState() => _WorkspaceFoundationState();
}

class _WorkspaceFoundationState extends State<WorkspaceFoundation> {
  int selected = 0;
  static const labels = ['My Files', 'Shared Files', 'Pending'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('VeilSpace')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(labels[selected], style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 12),
                const Text('Your shared workspace starts here.'),
                const SizedBox(height: 24),
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(20),
                    child: Text(
                      'Project foundation: login, uploads, and document processing '
                      'will be connected in the next milestones.',
                    ),
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
          NavigationDestination(icon: Icon(Icons.folder_outlined), label: 'My Files'),
          NavigationDestination(icon: Icon(Icons.people_outline), label: 'Shared Files'),
          NavigationDestination(icon: Icon(Icons.hourglass_empty), label: 'Pending'),
        ],
      ),
    );
  }
}
