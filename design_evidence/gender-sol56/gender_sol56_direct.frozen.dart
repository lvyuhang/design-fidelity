import 'package:flutter/material.dart';

class Sol56GenderSelection extends StatelessWidget {
  const Sol56GenderSelection({
    super.key,
    this.femaleSelected = false,
    this.onSelect,
  });

  final bool femaleSelected;
  final ValueChanged<String>? onSelect;

  static const _maleAsset =
      'assets/lanhu/gender_none/assets/a25cff5f9aabb90c8c6f286be1a49d34401850108d0459495065cdf59093df43.png';
  static const _femaleAsset =
      'assets/lanhu/gender_none/assets/d2855e7611728cfc07b1476da674344d477abedc8d9fbc67f9087bba0c093a49.png';
  static const _selectedFemaleAsset =
      'assets/lanhu/gender_female/assets/eacdc3db8eff06ddcc26f3a404612bc55bc07315ac2ef98900c27fabedff1272.png';
  static const _selectedBadgeAsset =
      'assets/lanhu/gender_female/assets/946fd6e0fb04feeae95ea8730b2c3eb280c50393cc9848ac36ac39e1282fec1f.png';
  static const _warningAsset =
      'assets/lanhu/gender_female/assets/10416d514d09343fe90359c1170c63f1b6a2a75432844bdc11e568ac56157832.png';

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 375,
      height: 350,
      child: ClipRect(
        child: Stack(
          children: [
            const Positioned.fill(child: _GenderBackground()),
            const Positioned(
              left: 27,
              top: 1,
              width: 180,
              height: 42,
              child: Text(
                '选择你的性别',
                maxLines: 1,
                style: TextStyle(
                  color: Color(0xFF18181B),
                  fontFamily: 'SourcePingFang',
                  fontSize: 30,
                  fontWeight: FontWeight.w600,
                  height: 1.4,
                ),
              ),
            ),
            const Positioned(
              left: 30,
              top: 45,
              width: 168,
              height: 17,
              child: Text(
                '用于为你推荐更合适的互动内容',
                maxLines: 1,
                style: TextStyle(
                  color: Color(0xFF9A9AA2),
                  fontFamily: 'SourcePingFang',
                  fontSize: 12,
                  fontWeight: FontWeight.w400,
                  height: 17 / 12,
                ),
              ),
            ),
            Positioned(
              left: 30,
              top: 113,
              child: _GenderCard(
                label: '男生',
                asset: _maleAsset,
                selected: false,
                onTap: () => onSelect?.call('male'),
              ),
            ),
            Positioned(
              left: 206,
              top: 113,
              child: _GenderCard(
                label: '女生',
                asset: femaleSelected ? _selectedFemaleAsset : _femaleAsset,
                selected: femaleSelected,
                onTap: () => onSelect?.call('female'),
              ),
            ),
            if (femaleSelected) const _SelectionWarning(),
          ],
        ),
      ),
    );
  }
}

class _GenderBackground extends StatelessWidget {
  const _GenderBackground();

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        const Positioned.fill(
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Color(0xFFFFFDF9),
                  Color(0xFFFFFBF2),
                  Color(0xFFFFFFFF),
                ],
                stops: [0, 0.5574737762, 1],
              ),
            ),
          ),
        ),
        Positioned(
          left: 143.1297709924,
          top: -231.8802816901,
          width: 314.8854961832,
          height: 314.8943661972,
          child: DecoratedBox(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: [
                  const Color(0xFFF2CD74).withValues(alpha: 0.1176),
                  const Color(0xFFFFF1D8).withValues(alpha: 0.0546),
                  Colors.transparent,
                ],
                stops: const [0, 0.56, 1],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _GenderCard extends StatelessWidget {
  const _GenderCard({
    required this.label,
    required this.asset,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final String asset;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: SizedBox(
        width: 134,
        height: 168,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Positioned(
              left: 0,
              top: 4,
              child: Container(
                width: 134,
                height: 164,
                decoration: BoxDecoration(
                  color: selected
                      ? const Color(0xFFFFF9EC)
                      : const Color(0xFFFFFDF9).withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(22),
                  border: Border.all(
                    color: selected
                        ? const Color(0xFFDDAA5A)
                        : const Color(0xFFEEDCC4),
                    width: 1,
                  ),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x1AD89B47),
                      offset: Offset(0, 6),
                      blurRadius: 12,
                    ),
                  ],
                ),
              ),
            ),
            Positioned(
              left: 35,
              top: 50,
              width: 64,
              height: 64,
              child: Image.asset(asset, fit: BoxFit.fill),
            ),
            Positioned(
              left: 53,
              top: 127,
              width: 28,
              height: 22,
              child: Text(
                label,
                maxLines: 1,
                style: const TextStyle(
                  color: Color(0xFF171718),
                  fontFamily: 'SourcePingFang',
                  fontSize: 14,
                  fontWeight: FontWeight.w400,
                  height: 22 / 14,
                ),
              ),
            ),
            if (selected)
              Positioned(
                left: 109,
                top: 0,
                width: 25,
                height: 25,
                child: Image.asset(
                  Sol56GenderSelection._selectedBadgeAsset,
                  fit: BoxFit.fill,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _SelectionWarning extends StatelessWidget {
  const _SelectionWarning();

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: 33,
      top: 297,
      width: 307,
      height: 36,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0xFFFEEFE9),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFFF9CBC3), width: 1),
        ),
        child: Stack(
          children: [
            Positioned(
              left: 13,
              top: 5,
              width: 26,
              height: 26,
              child: Image.asset(
                Sol56GenderSelection._warningAsset,
                fit: BoxFit.fill,
              ),
            ),
            const Positioned(
              left: 47,
              top: 9,
              width: 156,
              height: 18,
              child: Text(
                '选择性别提交后将不可修改',
                maxLines: 1,
                style: TextStyle(
                  color: Color(0xFFD12C29),
                  fontFamily: 'SourcePingFang',
                  fontSize: 13,
                  fontWeight: FontWeight.w400,
                  height: 18 / 13,
                ),
              ),
            ),
            const Positioned(
              left: 265,
              top: 5,
              width: 30,
              height: 31,
              child: CustomPaint(painter: _WarningShieldPainter()),
            ),
          ],
        ),
      ),
    );
  }
}

class _WarningShieldPainter extends CustomPainter {
  const _WarningShieldPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final outline = Paint()
      ..color = const Color(0xFFF6C1BE).withValues(alpha: 0.28)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    final shield = Path()
      ..moveTo(size.width / 2, 1.5)
      ..cubicTo(11, 5, 7, 6.5, 2.5, 7.5)
      ..cubicTo(2.8, 18.5, 5.8, 26, size.width / 2, 29.5)
      ..cubicTo(24.2, 26, 27.2, 18.5, 27.5, 7.5)
      ..cubicTo(23, 6.5, 19, 5, size.width / 2, 1.5);
    canvas.drawPath(shield, outline);

    final check = Path()
      ..moveTo(8, 16)
      ..lineTo(13, 21)
      ..lineTo(22, 12);
    canvas.drawPath(check, outline..strokeWidth = 2.5);
  }

  @override
  bool shouldRepaint(covariant _WarningShieldPainter oldDelegate) => false;
}
