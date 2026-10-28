import 'package:flutter/widgets.dart';

enum SystemChromeKind { statusBar, homeIndicator }

/// Reserves the space of OS-drawn chrome (status bar, home indicator) that
/// appears in the design mock-up but is never painted by the app.
///
/// On a device it uses the real safe-area inset; in the fidelity harness
/// (no padding) it falls back to the source height so the rest of the page
/// keeps its source coordinates. The gate excludes these regions.
class SystemChromeSlot extends StatelessWidget {
  const SystemChromeSlot({
    super.key,
    required this.kind,
    required this.sourceHeight,
  });

  final SystemChromeKind kind;
  final double sourceHeight;

  @override
  Widget build(BuildContext context) {
    final padding = MediaQuery.maybePaddingOf(context) ?? EdgeInsets.zero;
    final inset =
        kind == SystemChromeKind.statusBar ? padding.top : padding.bottom;
    return SizedBox(height: inset > 0 ? inset : sourceHeight);
  }
}
