import 'dart:convert';

import 'package:http/http.dart' as http;

import 'auth_service.dart';
import 'env.dart';

class ApiException implements Exception {
  ApiException(this.statusCode, this.body);

  final int statusCode;
  final String body;

  @override
  String toString() => 'ApiException($statusCode): $body';
}

/// Every call to the FastAPI backend goes through here so the
/// Authorization header and base URL are handled in exactly one place —
/// this is the "middleman" between AppState and the network.
class ApiClient {
  ApiClient(this._auth);

  final AuthService _auth;

  Map<String, String> get _headers {
    final token = _auth.accessToken;
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Uri _uri(String path, [Map<String, String>? query]) {
    final clean = query?.map((k, v) => MapEntry(k, v));
    return Uri.parse('${Env.apiBaseUrl}$path').replace(queryParameters: clean);
  }

  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    final res = await http.get(_uri(path, query), headers: _headers);
    return _decode(res);
  }

  Future<dynamic> post(String path, {Object? body}) async {
    final res = await http.post(_uri(path), headers: _headers, body: body == null ? null : jsonEncode(body));
    return _decode(res);
  }

  Future<dynamic> patch(String path, {Object? body}) async {
    final res = await http.patch(_uri(path), headers: _headers, body: body == null ? null : jsonEncode(body));
    return _decode(res);
  }

  Future<void> delete(String path) async {
    final res = await http.delete(_uri(path), headers: _headers);
    if (res.statusCode >= 400) throw ApiException(res.statusCode, res.body);
  }

  dynamic _decode(http.Response res) {
    if (res.statusCode >= 400) throw ApiException(res.statusCode, res.body);
    if (res.body.isEmpty) return null;
    return jsonDecode(res.body);
  }
}
