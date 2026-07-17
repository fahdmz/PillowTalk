import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'env.dart';

/// Deep-link scheme the app registers on Android/iOS for the OAuth redirect
/// to land back in — must also be added to the redirect URL allow-list for
/// the Google provider in the Supabase dashboard (Authentication > URL
/// Configuration), and the corresponding native platform config:
/// an `<intent-filter>` in AndroidManifest.xml and a URL scheme in Info.plist.
const _oauthRedirectUrl = 'com.drowzydiary.drowzydiary://login-callback';

/// Thin wrapper around Supabase Auth — this is the *only* place in the app
/// that should touch `Supabase.instance.client.auth` directly. Login/signup
/// are handled entirely client-side; the backend never sees passwords, it
/// only ever verifies the access token this service hands out.
class AuthService {
  AuthService(this._client);

  final SupabaseClient _client;

  static Future<void> initialize() {
    return Supabase.initialize(
      url: Env.supabaseUrl,
      anonKey: Env.supabaseAnonKey,
    );
  }

  factory AuthService.instance() => AuthService(Supabase.instance.client);

  Session? get currentSession => _client.auth.currentSession;
  String? get accessToken => currentSession?.accessToken;
  User? get currentUser => _client.auth.currentUser;
  bool get isSignedIn => currentSession != null;

  /// Fires on sign-in, sign-out, and token refresh — Supabase persists the
  /// session locally so this also fires once on app start if a session is
  /// still valid from a previous launch (sessions last ~30 days).
  Stream<AuthState> get onAuthStateChange => _client.auth.onAuthStateChange;

  Future<AuthResponse> signIn({required String email, required String password}) {
    return _client.auth.signInWithPassword(email: email, password: password);
  }

  Future<AuthResponse> signUp({
    required String email,
    required String password,
    required String fullName,
  }) {
    return _client.auth.signUp(
      email: email,
      password: password,
      data: {'full_name': fullName},
    );
  }

  /// Opens the system browser for Google sign-in/signup. Supabase creates
  /// the user automatically on first sign-in, so this one call covers both
  /// login and signup — there's no separate "Google signup". Completion
  /// arrives later via [onAuthStateChange], not this future.
  ///
  /// On web, `redirectTo` must be an exact match (or match a wildcard
  /// pattern) in the Supabase dashboard's Authentication > URL Configuration
  /// > Redirect URLs list — otherwise Supabase falls back to the dashboard's
  /// static Site URL, which silently breaks the moment the app runs on a
  /// different port than that setting expects (`ERR_CONNECTION_REFUSED`).
  /// Using `Uri.base.origin` here means it always matches wherever this
  /// page actually is, instead of depending on a dashboard value staying in
  /// sync with `--web-port`.
  Future<bool> signInWithGoogle() {
    return _client.auth.signInWithOAuth(
      OAuthProvider.google,
      redirectTo: kIsWeb ? Uri.base.origin : _oauthRedirectUrl,
    );
  }

  Future<void> signOut() => _client.auth.signOut();
}
