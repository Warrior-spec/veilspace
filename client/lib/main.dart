import 'package:flutter/material.dart';

import 'api.dart';
import 'auth_screen.dart';
import 'workspace.dart';

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


