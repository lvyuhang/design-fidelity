import 'package:flutter/material.dart';

class SettingsCaseAssets {
  static const chevron = 'assets/lanhu/settings_case/chevron.png';
  static const back = 'assets/lanhu/complaint_empty/back.png';
  static const reference = 'assets/reference/settings-case.png';
  static const all = <String>[chevron, back];
}

class SettingsCasePage extends StatelessWidget {
  const SettingsCasePage({this.onBack, this.onItemTap, super.key});

  final VoidCallback? onBack;
  final ValueChanged<String>? onItemTap;
  static const designSize = Size(375, 1039);

  @override
  Widget build(BuildContext context) => SizedBox(
        key: const ValueKey('settings-case-canvas'),
        width: designSize.width,
        height: designSize.height,
        child: ColoredBox(
          color: const Color(0xFFFFFEFA),
          child: Stack(children: [
            const Positioned(left: 21, top: 14.33, child: _Clock()),
            const Positioned(
              left: 294,
              top: 17,
              width: 67,
              height: 12,
              child: CustomPaint(painter: _StatusIconsPainter()),
            ),
            Positioned(
              left: 16,
              top: 55,
              width: 22,
              height: 22,
              child: GestureDetector(
                key: const ValueKey('settings-case-back'),
                onTap: onBack,
                child: const Image(
                  image: AssetImage(SettingsCaseAssets.back),
                  fit: BoxFit.fill,
                  filterQuality: FilterQuality.high,
                ),
              ),
            ),
            const Positioned(
              left: 0,
              right: 0,
              top: 55,
              height: 22,
              child: Text('设置',
                  key: ValueKey('settings-case-title'),
                  textScaler: TextScaler.noScaling,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'PingFangSCFull',
                    fontSize: 16,
                    height: 22 / 16,
                    fontWeight: FontWeight.w500,
                    color: Color(0xFF22242A),
                  )),
            ),
            Positioned(
              left: 16,
              top: 94,
              child: _SettingsGroup(
                height: 100,
                rows: const [
                  _SettingData('账号管理'),
                  _SettingData('黑名单'),
                ],
                onTap: onItemTap,
              ),
            ),
            Positioned(
              left: 16,
              top: 202,
              child: _SettingsGroup(
                height: 100,
                rows: const [
                  _SettingData('通知设置'),
                  _SettingData('系统权限设置'),
                ],
                onTap: onItemTap,
              ),
            ),
            Positioned(
              left: 16,
              top: 310,
              child: _SettingsGroup(
                height: 150,
                rows: const [
                  _SettingData('美颜设置'),
                  _SettingData('美妆设置'),
                  _SettingData('视频帧率', trailing: '30 fps'),
                ],
                onTap: onItemTap,
              ),
            ),
            Positioned(
              left: 16,
              top: 468,
              child: _SettingsGroup(
                height: 100,
                rows: const [
                  _SettingData('清除聊天记录'),
                  _SettingData('清除缓存', trailing: '128 MB'),
                ],
                onTap: onItemTap,
              ),
            ),
            Positioned(
              left: 16,
              top: 576,
              child: _SettingsGroup(
                height: 352,
                rows: const [
                  _SettingData('个人信息浏览与导出'),
                  _SettingData('收集个人信息清单'),
                  _SettingData('与第三方共享信息清单'),
                  _SettingData('青少年模式', trailing: '未开启'),
                  _SettingData('关于我们', trailing: 'v2.0.0'),
                  _SettingData('投诉'),
                  _SettingData('处罚信息'),
                ],
                onTap: onItemTap,
              ),
            ),
            Positioned(
              left: 16,
              top: 939,
              width: 343,
              height: 50,
              child: GestureDetector(
                key: const ValueKey('settings-case-logout'),
                onTap: () => onItemTap?.call('退出登录'),
                child: const _FrostedCard(
                  radius: 18,
                  child: Center(
                    child: Text('退出登录',
                        textScaler: TextScaler.noScaling,
                        style: TextStyle(
                          fontFamily: 'PingFangSCFull',
                          fontSize: 14,
                          height: 20 / 14,
                          color: Color(0xFF22242A),
                        )),
                  ),
                ),
              ),
            ),
            const Positioned(
              left: 121,
              top: 1026,
              width: 134,
              height: 5,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.all(Radius.circular(100)),
                ),
              ),
            ),
          ]),
        ),
      );
}

class SettingsCasePreviewPage extends StatelessWidget {
  const SettingsCasePreviewPage({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: const Color(0xFFF2F3F5),
        body: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Column(children: [
            const Text('设置 · Skill 2.18.4 独立案例',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
            const SizedBox(height: 14),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: const Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _PreviewPanel(label: '蓝湖原稿', child: _ReferenceImage()),
                  SizedBox(width: 24),
                  _PreviewPanel(label: 'Flutter', child: SettingsCasePage()),
                ],
              ),
            ),
          ]),
        ),
      );
}

class _ReferenceImage extends StatelessWidget {
  const _ReferenceImage();
  @override
  Widget build(BuildContext context) => const Image(
        image: AssetImage(SettingsCaseAssets.reference),
        width: 375,
        height: 1039,
        fit: BoxFit.fill,
        filterQuality: FilterQuality.high,
      );
}

class _PreviewPanel extends StatelessWidget {
  const _PreviewPanel({required this.label, required this.child});
  final String label;
  final Widget child;
  @override
  Widget build(BuildContext context) => Column(children: [
        Text(label,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        DecoratedBox(
          decoration:
              BoxDecoration(border: Border.all(color: const Color(0xFFCBD1D9))),
          child: child,
        ),
      ]);
}

class _SettingData {
  const _SettingData(this.label, {this.trailing});
  final String label;
  final String? trailing;
}

class _SettingsGroup extends StatelessWidget {
  const _SettingsGroup({required this.height, required this.rows, this.onTap});
  final double height;
  final List<_SettingData> rows;
  final ValueChanged<String>? onTap;

  @override
  Widget build(BuildContext context) {
    final rowHeight = (height - (rows.length - 1)) / rows.length;
    return SizedBox(
      width: 343,
      height: height,
      child: _FrostedCard(
        radius: 18,
        child: Column(
          children: [
            for (var index = 0; index < rows.length; index++) ...[
              SizedBox(
                height: rowHeight,
                child: GestureDetector(
                  key: ValueKey('settings-row-${rows[index].label}'),
                  behavior: HitTestBehavior.opaque,
                  onTap: () => onTap?.call(rows[index].label),
                  child: Padding(
                    padding: const EdgeInsets.only(left: 21, right: 20),
                    child: Row(children: [
                      Expanded(
                        child: Text(rows[index].label,
                            textScaler: TextScaler.noScaling,
                            style: const TextStyle(
                              fontFamily: 'PingFangSCFull',
                              fontSize: 14,
                              height: 20 / 14,
                              color: Color(0xFF22242A),
                            )),
                      ),
                      if (rows[index].trailing != null) ...[
                        Text(rows[index].trailing!,
                            textScaler: TextScaler.noScaling,
                            style: const TextStyle(
                              fontFamily: 'PingFangSCFull',
                              fontSize: 13,
                              height: 18 / 13,
                              color: Color(0xFF686B77),
                            )),
                        const SizedBox(width: 8),
                      ],
                      const SizedBox(
                        width: 7,
                        height: 12,
                        child: Image(
                          image: AssetImage(SettingsCaseAssets.chevron),
                          fit: BoxFit.fill,
                          filterQuality: FilterQuality.high,
                        ),
                      ),
                    ]),
                  ),
                ),
              ),
              if (index != rows.length - 1)
                const SizedBox(
                  width: 302,
                  height: 1,
                  child: ColoredBox(color: Color(0x80EAEBF0)),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _FrostedCard extends StatelessWidget {
  const _FrostedCard({required this.radius, required this.child});
  final double radius;
  final Widget child;
  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xF2FFFFFF), Color(0xA6FFFFFF)],
          ),
          border: Border.all(color: Colors.white, width: 1),
          borderRadius: BorderRadius.circular(radius),
          boxShadow: const [
            BoxShadow(color: Color(0x1FE8C77B), blurRadius: 16),
          ],
        ),
        child: ClipRRect(
            borderRadius: BorderRadius.circular(radius), child: child),
      );
}

class _Clock extends StatelessWidget {
  const _Clock();
  @override
  Widget build(BuildContext context) => const SizedBox(
        width: 54,
        height: 18,
        child: Text('9:41',
            textScaler: TextScaler.noScaling,
            style: TextStyle(
              fontFamily: 'PingFangSCFull',
              fontSize: 15,
              height: 18 / 15,
              letterSpacing: -.3,
              color: Colors.black,
            )),
      );
}

class _StatusIconsPainter extends CustomPainter {
  const _StatusIconsPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final black = Paint()..color = Colors.black;
    for (var i = 0; i < 4; i++) {
      final h = 4.5 + i * 2.1;
      canvas.drawRRect(
          RRect.fromRectAndRadius(
              Rect.fromLTWH(i * 5.1, 12 - h, 3.2, h), const Radius.circular(1)),
          black);
    }
    final wifi = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(const Rect.fromLTWH(23, 0, 18, 14), 3.65, 2.15, false, wifi);
    canvas.drawArc(const Rect.fromLTWH(27, 4, 10, 8), 3.65, 2.15, false, wifi);
    canvas.drawCircle(const Offset(32, 10.4), 1.25, black);
    final outline = Paint()
      ..color = const Color(0x59000000)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(44, 0, 22, 11.3), const Radius.circular(2)),
        outline);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(46, 2, 18, 7.3), const Radius.circular(1)),
        black);
    canvas.drawRRect(
        RRect.fromRectAndRadius(
            const Rect.fromLTWH(66.4, 3.7, 1.3, 4), const Radius.circular(.7)),
        outline);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
