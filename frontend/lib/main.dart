import 'package:flutter/material.dart';

import 'app.dart';
import 'services/auth_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AuthService.initialize();
  runApp(const DrowzyDiaryApp());
}
