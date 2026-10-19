import 'package:flutter/material.dart';

/// First-pass implementation from the MCP response for snapshot
/// 4a82a245a06e7de77a4320e533934570. Kept frozen before visual comparison.
/// No calibrated renderer, generated shape specs or screenshot-based offsets.
class DirectAppealCard extends StatelessWidget {
  const DirectAppealCard({
    this.title = '处罚原因文案',
    this.result = '账号禁止登录 7天',
    this.duration = 'N小时',
    this.penaltyId = 'PN202607290126',
    this.onAppeal,
    super.key,
  });
  final String title, result, duration, penaltyId;
  final VoidCallback? onAppeal;
  static const shieldAsset =
      'assets/lanhu/appeal/assets/3c01e52ce3c5fd7658e2bb85964bf19046d219e3f4f0a6e2e1562aefded0f5b4.png';

  // All positions below are source bounds relative to card origin (16,352).
  Widget _text(String value, Rect bounds, double size, double line, Color color,
          {FontWeight weight = FontWeight.w400,
          TextAlign align = TextAlign.center}) =>
      Positioned.fromRect(
        rect: bounds,
        child: Text(value,
            textAlign: align,
            softWrap: false,
            overflow: TextOverflow.visible,
            textScaler: TextScaler.noScaling,
            style: TextStyle(
                inherit: false,
                fontFamily: 'SourcePingFang',
                fontSize: size,
                height: line / size,
                fontWeight: weight,
                letterSpacing: 0,
                color: color,
                decoration: TextDecoration.none,
                leadingDistribution: TextLeadingDistribution.even)),
      );

  @override
  Widget build(BuildContext context) => SizedBox(
        width: 343,
        height: 116,
        child: DecoratedBox(
            // Raw normalized gradient endpoints mapped into Flutter Alignment.
            decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFFFCF4EE), width: 1),
                gradient: const LinearGradient(
                    begin: Alignment(-0.8827897235751152, -1),
                    end: Alignment(0.7825027704238892, 1.079352617263794),
                    colors: [Color(0xFFFFFCF8), Color(0xFFFFF9F4)])),
            child: Stack(clipBehavior: Clip.none, children: [
              // Designer-exported PNG is used as exported, without another opacity pass.
              Positioned(
                  left: 262,
                  top: 8,
                  width: 68,
                  height: 79,
                  child: Image.asset(shieldAsset,
                      fit: BoxFit.fill, filterQuality: FilterQuality.high)),
              _text(title, const Rect.fromLTWH(14, 11, 84, 20), 14, 20,
                  const Color(0xFF22242A),
                  weight: FontWeight.w600),
              const Positioned(
                  left: 15,
                  top: 38,
                  width: 312.999533172703,
                  height: 1,
                  child: Divider(
                      height: 1, thickness: .5, color: Color(0xFFEAEBF0))),
              _text('处罚结果', const Rect.fromLTWH(15, 47, 44, 16), 11, 16,
                  const Color(0xFFA6AAB5)),
              _text('处罚时长', const Rect.fromLTWH(15, 68, 44, 16), 11, 16,
                  const Color(0xFFA6AAB5)),
              _text('处罚编号', const Rect.fromLTWH(15, 88, 44, 16), 11, 16,
                  const Color(0xFFA6AAB5)),
              _text(result, const Rect.fromLTWH(87, 46, 96, 17), 12, 17,
                  const Color(0xFFD9443A)),
              _text(duration, const Rect.fromLTWH(87, 67, 34, 17), 12, 17,
                  const Color(0xFF686B77)),
              _text(penaltyId, const Rect.fromLTWH(87, 87, 100, 17), 12, 17,
                  const Color(0xFF686B77)),
              Positioned(
                  left: 249,
                  top: 62,
                  width: 78,
                  height: 28,
                  child: Semantics(
                      button: true,
                      label: '直接实现版申诉',
                      child: MouseRegion(
                          cursor: SystemMouseCursors.click,
                          child: GestureDetector(
                              key: const ValueKey('direct-appeal-action'),
                              behavior: HitTestBehavior.opaque,
                              onTap: onAppeal,
                              child: DecoratedBox(
                                  decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(25),
                                      gradient: const LinearGradient(
                                          begin: Alignment.centerRight,
                                          end: Alignment.centerLeft,
                                          colors: [
                                            Color(0xFF372D22),
                                            Color(0xFF111111)
                                          ],
                                          stops: [
                                            0.0006282779720279722,
                                            1
                                          ]),
                                      border: Border.all(
                                          color: const Color.fromRGBO(
                                              214, 164, 74, .4),
                                          width: 1),
                                      boxShadow: const [
                                        BoxShadow(
                                            color: Color.fromRGBO(
                                                214, 164, 74, .1),
                                            offset: Offset(0, 8),
                                            blurRadius: 14,
                                            spreadRadius: 0)
                                      ]),
                                  child: Stack(children: [
                                    _text(
                                        '申诉',
                                        const Rect.fromLTWH(26, 5, 26, 18),
                                        13,
                                        18,
                                        const Color(0xFFE6B55E),
                                        weight: FontWeight.w600,
                                        align: TextAlign.left),
                                  ]))))))
            ])),
      );
}

class DirectAppealStage extends StatelessWidget {
  const DirectAppealStage({this.onAppeal, super.key});
  final VoidCallback? onAppeal;
  @override
  Widget build(BuildContext context) => SizedBox(
      width: 375,
      height: 125,
      child: ColoredBox(
          color: const Color(0xFFFFFEFA),
          child: Stack(children: [
            Positioned(
                left: 16, top: 4, child: DirectAppealCard(onAppeal: onAppeal)),
          ])));
}
