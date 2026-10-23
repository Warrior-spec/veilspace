import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:veilspace/api.dart';
import 'package:veilspace/main.dart';

http.Response sessionResponse(int status) => http.Response(
  jsonEncode({
    'access_token': 'test-session',
    'user': {'display_name': 'Demo Member', 'email': 'member@example.com'},
  }),
  status,
);

http.Response? workspaceResponse(http.Request request) {
  if (request.method != 'GET') return null;
  if (request.url.path.endsWith('/usage')) {
    return http.Response('{"requests":0,"reserved_usd":0,"daily_limit_usd":1}', 200);
  }
  return http.Response('[]', 200);
}

void main() {
  testWidgets('sign in and revoke the current session on sign out', (
    tester,
  ) async {
    final api = ApiClient(
      client: MockClient((request) async {
        final workspace = workspaceResponse(request);
        if (workspace != null) return workspace;
        if (request.url.path.endsWith('/logout')) {
          expect(request.headers['Authorization'], 'Bearer test-session');
          return http.Response('', 204);
        }
        expect(request.url.path, '/api/auth/login');
        expect(jsonDecode(request.body)['email'], 'member@example.com');
        return sessionResponse(200);
      }),
    );
    await tester.pumpWidget(VeilSpaceApp(api: api));
    await tester.enterText(
      find.byType(TextFormField).at(0),
      'member@example.com',
    );
    await tester.enterText(
      find.byType(TextFormField).at(1),
      'DocumentDemo2026!',
    );
    await tester.ensureVisible(find.text('Sign in'));
    await tester.tap(find.text('Sign in'));
    await tester.pumpAndSettle();
    expect(find.text('member@example.com'), findsOneWidget);
    await tester.tap(find.byTooltip('Sign out'));
    await tester.pumpAndSettle();
    expect(find.text('Welcome back'), findsOneWidget);
  });

  testWidgets('server errors leave the user on the login screen', (
    tester,
  ) async {
    final api = ApiClient(
      client: MockClient(
        (request) async => http.Response(
          jsonEncode({'detail': 'Invalid email or password'}),
          401,
        ),
      ),
    );
    await tester.pumpWidget(VeilSpaceApp(api: api));
    await tester.enterText(
      find.byType(TextFormField).at(0),
      'member@example.com',
    );
    await tester.enterText(find.byType(TextFormField).at(1), 'wrong');
    await tester.ensureVisible(find.text('Sign in'));
    await tester.tap(find.text('Sign in'));
    await tester.pumpAndSettle();
    expect(find.text('Invalid email or password'), findsOneWidget);
    expect(find.text('Welcome back'), findsOneWidget);
  });

  testWidgets('registration submits the name and opens the workspace', (
    tester,
  ) async {
    final api = ApiClient(
      client: MockClient((request) async {
        final workspace = workspaceResponse(request);
        if (workspace != null) return workspace;
        expect(request.url.path, '/api/auth/register');
        expect(jsonDecode(request.body)['display_name'], 'Demo Member');
        return sessionResponse(201);
      }),
    );
    await tester.pumpWidget(VeilSpaceApp(api: api));
    await tester.tap(find.text('Create an account'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).at(0), 'Demo Member');
    await tester.enterText(
      find.byType(TextFormField).at(1),
      'member@example.com',
    );
    await tester.enterText(
      find.byType(TextFormField).at(2),
      'DocumentDemo2026!',
    );
    await tester.ensureVisible(find.text('Create account'));
    await tester.tap(find.text('Create account'));
    await tester.pumpAndSettle();
    expect(find.text('member@example.com'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });
}
