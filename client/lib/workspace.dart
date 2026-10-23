import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:file_selector/file_selector.dart';
import 'api.dart';
import 'folder_watch.dart';

class WorkspaceFoundation extends StatefulWidget {
  final ApiClient api;
  final Session session;
  final VoidCallback onSignedOut;
  const WorkspaceFoundation({super.key, required this.api, required this.session, required this.onSignedOut});
  @override
  State<WorkspaceFoundation> createState() => _WorkspaceFoundationState();
}

class _WorkspaceFoundationState extends State<WorkspaceFoundation> {
  final watcher = FolderWatch();
  Timer? timer;
  List<Map<String, dynamic>> own = [], shared = [];
  Map<String, dynamic> usage = {};
  int selected = 0;
  bool uploading = false, signingOut = false, loading = true, refreshing = false;
  String? error, folder;
  bool get desktop => !kIsWeb && defaultTargetPlatform == TargetPlatform.windows;

  @override
  void initState() {
    super.initState();
    refresh();
    timer = Timer.periodic(const Duration(seconds: 4), (_) => refresh());
  }

  @override
  void dispose() {
    timer?.cancel();
    watcher.stop();
    super.dispose();
  }

  Future<void> refresh() async {
    if (refreshing) return;
    refreshing = true;
    try {
      final values = await Future.wait([
        widget.api.request(widget.session, ''),
        widget.api.request(widget.session, '/shared'),
        widget.api.request(widget.session, '/usage'),
      ]);
      if (mounted) {
        setState(() {
          own = List<Map<String, dynamic>>.from(values[0]);
          shared = List<Map<String, dynamic>>.from(values[1]);
          usage = Map<String, dynamic>.from(values[2]);
          error = null;
          loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() { error = message(e); loading = false; });
    } finally { refreshing = false; }
  }

  String message(Object e) => e is ApiException ? e.message : 'Cannot reach the server. Please try again.';
  void notify(String value) {
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(value)));
  }

  Future<void> send(String name, List<int> bytes, [String? source]) async {
    final query = Uri(queryParameters: {'filename': name, if (source != null) 'source_id': source}).query;
    await widget.api.request(widget.session, '?$query', method: 'POST', bytes: bytes);
  }

  Future<void> upload() async {
    try {
      final files = await openFiles(acceptedTypeGroups: [const XTypeGroup(label: 'Documents', extensions: ['pdf', 'docx', 'txt'])]);
      if (files.isEmpty || !mounted) return;
      setState(() => uploading = true);
      for (final file in files) {
        if (await file.length() > 10485760) { notify('${file.name}: maximum size is 10 MB'); continue; }
        await send(file.name, await file.readAsBytes());
      }
      notify('Files received. Checking privacy before sharing.');
      await refresh();
    } catch (e) { notify(message(e)); }
    finally { if (mounted) setState(() => uploading = false); }
  }

  Future<void> chooseFolder() async {
    try {
      final path = await getDirectoryPath();
      if (path == null || !mounted) return;
      setState(() => folder = path);
      await watcher.start(path, (name, bytes, source) async {
        await send(name, bytes, source);
        await refresh();
      }, notify);
    } catch (e) { notify(message(e)); }
  }

  Future<void> action(Map<String, dynamic> file, String operation) async {
    try {
      if (operation == 'preview') {
        final data = await widget.api.request(widget.session, '/${file['id']}/preview');
        if (!mounted) return;
        await showDialog<void>(context: context, builder: (context) => AlertDialog(
          title: const Text('Published document'),
          content: SizedBox(width: 700, child: SingleChildScrollView(child: SelectableText(data['text'] as String))),
          actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close'))],
        ));
      } else {
        if (operation == 'delete') {
          final confirmed = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
            title: const Text('Delete this document?'),
            content: const Text('All revisions will be removed from the workspace.'),
            actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')), FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete'))],
          ));
          if (confirmed != true) return;
        }
        await widget.api.request(widget.session, '/${file['id']}${operation == 'retry' ? '/retry' : ''}', method: operation == 'retry' ? 'POST' : 'DELETE');
        await refresh();
      }
    } catch (e) { notify(message(e)); }
  }

  Future<void> signOut() async {
    setState(() => signingOut = true);
    watcher.stop();
    try {
      await widget.api.logout(widget.session);
      if (mounted) widget.onSignedOut();
    } catch (e) { notify(message(e)); }
    finally { if (mounted) setState(() => signingOut = false); }
  }

  @override
  Widget build(BuildContext context) {
    final pending = own.where((file) => file['status'] != 'published').toList();
    final files = selected == 0 ? own : selected == 1 ? shared : pending;
    return Scaffold(
      appBar: AppBar(title: const Text('VeilSpace'), actions: [
        IconButton(onPressed: refresh, tooltip: 'Refresh', icon: const Icon(Icons.refresh)),
        IconButton(onPressed: signingOut ? null : signOut, tooltip: 'Sign out', icon: const Icon(Icons.logout)),
      ]),
      body: Center(child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 1050), child: Column(children: [
        Padding(padding: const EdgeInsets.fromLTRB(20, 16, 20, 8), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(['My Files', 'Shared Files', 'Pending'][selected], style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 4),
          Text(widget.session.email),
          const SizedBox(height: 16),
          Wrap(spacing: 10, runSpacing: 10, children: [
            Chip(avatar: const Icon(Icons.folder_outlined, size: 18), label: Text('${own.length} uploaded')),
            Chip(avatar: const Icon(Icons.verified_user_outlined, size: 18), label: Text('${shared.length} shared')),
            Chip(avatar: const Icon(Icons.hourglass_empty, size: 18), label: Text('${pending.length} awaiting publication')),
          ]),
          const SizedBox(height: 12),
          Wrap(spacing: 10, runSpacing: 8, children: [
            FilledButton.icon(onPressed: uploading ? null : upload, icon: const Icon(Icons.upload_file), label: Text(uploading ? 'Uploading...' : 'Upload documents')),
            if (desktop) OutlinedButton.icon(onPressed: chooseFolder, icon: const Icon(Icons.drive_folder_upload), label: Text(folder == null ? 'Watch a folder' : 'Change watched folder')),
            if (folder != null) TextButton(onPressed: () { watcher.stop(); setState(() => folder = null); }, child: const Text('Stop watching')),
          ]),
          if (folder != null) Padding(padding: const EdgeInsets.only(top: 10), child: Text('Watching: $folder\nKeep this app open for automatic uploads.', style: Theme.of(context).textTheme.bodySmall)),
          const SizedBox(height: 10),
          Text('DOCX, PDF, TXT · 10 MB per file · Only sanitized documents are shared', style: Theme.of(context).textTheme.bodySmall),
          if (usage.isNotEmpty) Text('Today: ${usage['requests']} AI requests · \$${(usage['reserved_usd'] as num).toStringAsFixed(3)} reserved / \$${usage['daily_limit_usd']}', style: Theme.of(context).textTheme.bodySmall),
        ])),
        if (error != null) Padding(padding: const EdgeInsets.all(12), child: Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
        Expanded(child: loading ? const Center(child: CircularProgressIndicator()) : files.isEmpty ? const Center(child: Text('No files here yet.')) : RefreshIndicator(onRefresh: refresh, child: ListView.builder(
          padding: const EdgeInsets.all(16), itemCount: files.length, itemBuilder: (context, index) {
            final file = files[index];
            final published = file['status'] == 'published';
            final available = file['downloadable'] == 1;
            return Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [Icon(published ? Icons.verified_user : Icons.lock_outline), const SizedBox(width: 10), Expanded(child: Text(file['name'] as String, style: Theme.of(context).textTheme.titleMedium)),
                if (file['is_owner'] == true) PopupMenuButton<String>(onSelected: (value) => action(file, value), itemBuilder: (_) => [
                  if (file['status'] == 'pending') const PopupMenuItem(value: 'retry', child: Text('Retry processing')),
                  const PopupMenuItem(value: 'delete', child: Text('Delete')),
                ]),
              ]),
              const SizedBox(height: 8),
              Text('${file['status']} · Revision ${file['revision']} · ${file['redactions']} redactions${file['cached'] == 1 ? ' · Cached' : ''}'),
              if (selected == 1) Text('Shared by ${file['uploader']}'),
              if (file['reason'] != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(file['reason'] as String)),
              if (available) TextButton.icon(onPressed: () => action(file, 'preview'), icon: const Icon(Icons.article_outlined), label: Text(published ? 'Read sanitized document' : 'Read previous published revision')),
            ])));
          },
        ))),
      ]))),
      bottomNavigationBar: NavigationBar(selectedIndex: selected, onDestinationSelected: (value) => setState(() => selected = value), destinations: const [
        NavigationDestination(icon: Icon(Icons.folder_outlined), label: 'My Files'),
        NavigationDestination(icon: Icon(Icons.people_outline), label: 'Shared Files'),
        NavigationDestination(icon: Icon(Icons.hourglass_empty), label: 'Pending'),
      ]),
    );
  }
}
