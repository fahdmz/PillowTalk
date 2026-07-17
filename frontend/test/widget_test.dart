import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:drowzydiary/widgets/primary_button.dart';

void main() {
  testWidgets('PrimaryButton shows its label and reports taps', (WidgetTester tester) async {
    var tapped = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PrimaryButton(label: 'Log In', onTap: () => tapped = true),
        ),
      ),
    );

    expect(find.text('Log In'), findsOneWidget);

    await tester.tap(find.byType(PrimaryButton));
    expect(tapped, isTrue);
  });
}
