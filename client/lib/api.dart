import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  final String message;
  const ApiException(this.message);
}

class Session {
  final String token;
  final String name;
  final String email;
  const Session(this.token, this.name, this.email);
}

class ApiClient {
  final http.Client _client;
  ApiClient({http.Client? client}) : _client = client ?? http.Client();
  static const _origin = String.fromEnvironment('VEILSPACE_API_ORIGIN');

  Uri _url(String path) {
    final base = _origin.isNotEmpty
        ? Uri.parse(_origin)
        : kIsWeb
            ? Uri.base
            : Uri.parse('http://91.124.98.60:8787');
    return base.resolve(path);
  }

  Future<Session> authenticate({
    required String email,
    required String password,
    String? name,
  }) async {
    final response = await _client
        .post(
          _url('/api/auth/${name == null ? 'login' : 'register'}'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'email': email,
            'password': password,
            if (name != null) 'display_name': name,
          }),
        )
        .timeout(const Duration(seconds: 20));
    final data =
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw ApiException(
        data['detail'] is String
            ? data['detail'] as String
            : 'Please check your details.',
      );
    }
    final user = data['user'] as Map<String, dynamic>;
    return Session(
      data['access_token'] as String,
      user['display_name'] as String,
      user['email'] as String,
    );
  }

  Future<void> logout(Session session) async {
    final response = await _client.post(
      _url('/api/auth/logout'),
      headers: {'Authorization': 'Bearer ${session.token}'},
    ).timeout(const Duration(seconds: 20));
    if (response.statusCode != 204 && response.statusCode != 401) {
      throw const ApiException('Could not sign out. Please try again.');
    }
  }

  void close() => _client.close();

  Future<dynamic> request(Session session, String path,
      {String method = 'GET', List<int>? bytes}) async {
    final request = http.Request(method, _url('/api/documents$path'));
    request.headers['Authorization'] = 'Bearer ${session.token}';
    if (bytes != null) request.bodyBytes = bytes;
    final response = await http.Response.fromStream(
        await _client.send(request).timeout(const Duration(seconds: 60)));
    final data = response.bodyBytes.isEmpty
        ? null
        : jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode >= 400) {
      throw ApiException(data is Map && data['detail'] is String
          ? data['detail']
          : 'Request failed');
    }
    return data;
  }
}
