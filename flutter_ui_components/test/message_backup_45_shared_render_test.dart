import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:juxing_components/experiments/message_backup_45_page.dart';
import 'support/fidelity_render_harness.dart';

void main() {
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);
  testWidgets('shared harness preserves the frozen message page',
      (tester) async {
    final locale = Platform.environment['FIDELITY_LEGACY_LOCALE'] == '1'
        ? const Locale('en', 'US')
        : const Locale('zh', 'CN');
    await captureFidelityPage(tester,
        page: const MessageBackup45Page(),
        size: MessageBackup45Page.designSize,
        scale: 4,
        locale: locale,
        imageAssets: MessageBackup45Assets.all,
        output: fidelityOutputPath('FIDELITY_OUTPUT'));
    expect(find.byType(MissingDesignAsset), findsNWidgets(11));
    expect(
        MediaQuery.textScalerOf(
            tester.element(find.byType(MessageBackup45Page))),
        TextScaler.noScaling);
    expect(
        Localizations.localeOf(
            tester.element(find.byType(MessageBackup45Page))),
        locale);
  });
}
