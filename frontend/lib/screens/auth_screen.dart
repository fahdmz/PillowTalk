import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../state/app_state.dart';
import '../widgets/crescent_moon_icon.dart';
import '../widgets/primary_button.dart';
import '../widgets/segmented_toggle.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _fullNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _fullNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit(AppState app, bool isSignup) {
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    if (email.isEmpty || password.isEmpty) return;
    if (isSignup) {
      app.signUp(email: email, password: password, fullName: _fullNameController.text.trim());
    } else {
      app.logIn(email: email, password: password);
    }
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final t = app.t;
    final isSignup = app.authMode == AuthMode.signup;

    return Container(
      color: Colors.black,
      padding: const EdgeInsets.fromLTRB(28, 64, 28, 40),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Column(
            children: [
              CrescentMoonIcon(color: Color(0xFF6B5484), size: 34),
              SizedBox(height: 10),
            ],
          ),
          Center(
            child: Text(
              'DrowzyDiary',
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                color: Color(0xFFEDE7E2),
                letterSpacing: 0.3,
              ),
            ),
          ),
          const SizedBox(height: 4),
          Center(
            child: Text(
              t.tagline,
              style: const TextStyle(fontSize: 13, color: Color(0x80EDE7E2), letterSpacing: 0.2),
            ),
          ),
          const SizedBox(height: 40),
          SegmentedToggle(
            activeColor: const Color(0xFF392A48),
            activeTextColor: const Color(0xFFEDE7E2),
            inactiveTextColor: const Color(0x8CEDE7E2),
            options: [
              SegmentOption(
                label: t.logIn,
                selected: !isSignup,
                onTap: () => app.setAuthMode(AuthMode.login),
              ),
              SegmentOption(
                label: t.signUp,
                selected: isSignup,
                onTap: () => app.setAuthMode(AuthMode.signup),
              ),
            ],
          ),
          const SizedBox(height: 30),
          Column(
            children: [
              if (isSignup) ...[
                _AuthField(placeholder: t.fullName, controller: _fullNameController),
                const SizedBox(height: 14),
              ],
              _AuthField(
                placeholder: t.email,
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 14),
              _AuthField(placeholder: t.password, controller: _passwordController, obscureText: true),
            ],
          ),
          if (app.authError != null) ...[
            const SizedBox(height: 14),
            Text(
              app.authError!,
              style: const TextStyle(fontSize: 12.5, color: Color(0xFFE88C77)),
            ),
          ],
          const SizedBox(height: 26),
          PrimaryButton(
            label: app.isAuthLoading
                ? '…'
                : (isSignup ? t.createAccount : t.logIn),
            onTap: app.isAuthLoading ? () {} : () => _submit(app, isSignup),
          ),
          const Spacer(),
          Center(
            child: Text(
              t.footer,
              style: const TextStyle(fontSize: 12, color: Color(0x4DEDE7E2)),
            ),
          ),
        ],
      ),
    );
  }
}

class _AuthField extends StatelessWidget {
  const _AuthField({
    required this.placeholder,
    required this.controller,
    this.obscureText = false,
    this.keyboardType,
  });

  final String placeholder;
  final TextEditingController controller;
  final bool obscureText;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      style: const TextStyle(fontSize: 15, color: Color(0xFFEDE7E2)),
      decoration: InputDecoration(
        hintText: placeholder,
        hintStyle: const TextStyle(color: Color(0x80EDE7E2)),
        filled: true,
        fillColor: const Color(0x0DFFFFFF),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0x14FFFFFF)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0x14FFFFFF)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0x33FFFFFF)),
        ),
      ),
    );
  }
}
