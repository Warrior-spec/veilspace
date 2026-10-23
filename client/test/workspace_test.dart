import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:veilspace/api.dart';
import 'package:veilspace/workspace.dart';

void main() {
  testWidgets('published document opens sanitized text inside the app', (tester) async {
    final api = ApiClient(client: MockClient((request) async {
      expect(request.headers['Authorization'], 'Bearer sample-token');
      if (request.url.path.endsWith('/preview')) {
        return http.Response(jsonEncode({'text': 'Person-001 studies renewable energy.'}), 200);
      }
      if (request.url.path.endsWith('/usage')) {
        return http.Response('{"requests":1,"reserved_usd":0.006,"daily_limit_usd":1}', 200);
      }
      return http.Response(jsonEncode([{
        'id':'sample', 'name':'research.txt', 'status':'published', 'revision':2,
        'redactions':4, 'cached':0, 'downloadable':1, 'is_owner':true,
        'reason':null, 'uploader':'Demo Member',
      }]), 200);
    }));
    await tester.pumpWidget(MaterialApp(home: WorkspaceFoundation(
      api: api, session: const Session('sample-token','Demo Member','demo@example.com'), onSignedOut: () {},
    )));
    await tester.pumpAndSettle();
    expect(find.text('research.txt'), findsOneWidget);
    await tester.ensureVisible(find.text('Read sanitized document'));
    await tester.tap(find.text('Read sanitized document'));
    await tester.pumpAndSettle();
    expect(find.text('Person-001 studies renewable energy.'), findsOneWidget);
    await tester.tap(find.text('Close'));
    await tester.pumpAndSettle();
    await tester.pumpWidget(const SizedBox());
    api.close();
  });
}
