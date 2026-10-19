import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'source_primitives.dart';

class ExpandedAssets {
  static const home =
      'assets/lanhu/nav/assets/a8071fdef24e364d65fb5159f6ac36f47d869667d188aca77e99a1fa52207622.png';
  static const shield =
      'assets/lanhu/appeal/assets/3c01e52ce3c5fd7658e2bb85964bf19046d219e3f4f0a6e2e1562aefded0f5b4.png';
}

/// Default source state, including the source's wording “清除记录”.
class CacheClearDialog extends StatelessWidget {
  const CacheClearDialog({this.onCancel, this.onConfirm, super.key});
  final VoidCallback? onCancel, onConfirm;
  @override
  Widget build(BuildContext context) {
    const origin = Offset(23, 267);
    Widget layer(String id, {VoidCallback? action, String? label}) =>
        sourceLayer('modal', id, origin, onTap: action, actionLabel: label);
    return Semantics(
        namesRoute: true,
        label: '清除缓存',
        child: SizedBox(
            width: 330,
            height: 228,
            child: Stack(clipBehavior: Clip.none, children: [
              layer('FC01670F-8A5F-4911-A3D0-A8FBD16728D3'),
              layer('9650F211-2C6C-4939-A1AB-65F0062270EB'),
              layer('1C822A70-2A93-4CCE-9DC0-284AB25F6E56',
                  action: onCancel, label: '取消清除'),
              layer('8B28FB00-FC47-4089-9322-C2D686F95D72',
                  action: onConfirm, label: '确认清除'),
              for (final id in [
                'C4175A96-4CCB-4A09-A989-A90729EC5E61',
                '39F5F8D9-44FE-4899-9A8D-EF27B87C6B58',
                '181D20B5-A2B3-47AB-9C05-CB506B698DD6',
                '0B960B60-B868-4D12-B9C5-BADBE0E3A0F9',
                'EDAA97EB-D272-488D-8ECC-164BE5B74C5D',
                'AD9DAA10-50F4-465D-BA80-03F96D50BD00'
              ])
                // Label layers must not intercept their underlying button's pointer events.
                _ignoreLayer(layer(id)),
            ])));
  }
}

Widget _ignoreLayer(Widget widget) {
  final p = widget as Positioned;
  return Positioned(
      left: p.left,
      top: p.top,
      width: p.width,
      height: p.height,
      child: IgnorePointer(child: p.child));
}

class ModalComponentStage extends StatelessWidget {
  const ModalComponentStage({this.onCancel, this.onConfirm, super.key});
  final VoidCallback? onCancel, onConfirm;
  @override
  Widget build(BuildContext context) => SizedBox(
      width: 375,
      height: 280,
      child: ClipRect(
          child: Stack(clipBehavior: Clip.none, children: [
        for (final id in [
          '269FCA6F-975D-47D8-B19D-A699C133603C',
          '6ABB4DE9-13D8-4EBB-8E66-3D8EF25832AD',
          'CFA1EFAD-725A-49F6-84B1-4DE236667049',
          '2870862D-2F99-4646-B95F-31613235929A',
          '631644BF-1CC6-477E-A875-44372D08B8FC',
          '3CF2EBF7-1F90-4E9C-A14A-E8B3F95BAC12',
          'F44FA91A-8190-486F-B9E1-8BA8192E2B7A',
          '94F25B4B-A4B5-4321-AD82-B8C42AB08068',
          '20341D03-5A04-48FF-8F2D-D7526754D906'
        ])
          sourceLayer('modal', id, const Offset(0, 245)),
        Positioned(
            left: 23,
            top: 22,
            child: CacheClearDialog(onCancel: onCancel, onConfirm: onConfirm)),
      ])));
}

/// A source-backed business card; the shield is a real exported 4× asset.
class AppealCard extends StatelessWidget {
  const AppealCard({this.onAppeal, super.key});
  final VoidCallback? onAppeal;
  @override
  Widget build(BuildContext context) {
    const origin = Offset(16, 352);
    return SizedBox(
        width: 343,
        height: 116,
        child: Stack(clipBehavior: Clip.none, children: [
          sourceLayer('appeal', '9E065EED-6A5B-4D37-9FFF-4160EA1C5B2C', origin),
          // Original PNG already includes layer opacity; do not multiply it twice.
          Positioned(
              left: 262,
              top: 8,
              width: 68,
              height: 79,
              child: Image.asset(ExpandedAssets.shield,
                  filterQuality: FilterQuality.high)),
          for (final id in [
            '4705348E-5591-402C-B0E8-EFE4515A92D2',
            '8AA38CE8-DF8A-42D9-843F-31E0D9BF6979',
            '53E090D4-80AA-4222-9DE7-BD9B1B003A4A',
            'D4518A43-893E-4A43-9493-DA9FE2E6A335',
            'F2C508B7-6708-4D7F-9AD8-2AA90D0A3FBA',
            '186F3D25-0CFD-458D-9CF8-3F7723A88251',
            'BA475018-F574-4608-8BCE-161532CCC271',
            '2E791406-EF40-404F-B148-1A426D320727'
          ])
            sourceLayer('appeal', id, origin),
          sourceLayer('appeal', '4849E7E6-6541-4A7B-813E-E98733ED8E49', origin,
              onTap: onAppeal, actionLabel: '申诉'),
          _ignoreLayer(sourceLayer(
              'appeal', '6FC9D722-17A3-42D8-910F-13FC0F8B5AF9', origin)),
        ]));
  }
}

class AppealComponentStage extends StatelessWidget {
  const AppealComponentStage({this.onAppeal, super.key});
  final VoidCallback? onAppeal;
  @override
  Widget build(BuildContext context) => SizedBox(
      width: 375,
      height: 125,
      child: ClipRect(
          child: ColoredBox(
              color: const Color(0xFFFFFEFA),
              child: Stack(clipBehavior: Clip.none, children: [
                Positioned(
                    left: 16, top: 4, child: AppealCard(onAppeal: onAppeal)),
              ]))));
}

/// Only the source's home-selected visual state is verified. Taps emit intent.
class JuxingBottomNavigation extends StatelessWidget {
  const JuxingBottomNavigation({this.onSelect, super.key});
  final ValueChanged<int>? onSelect;
  static const labels = ['首页', '消息', '关系', '任务', '我的'];
  @override
  Widget build(BuildContext context) {
    const origin = Offset(14, 735);
    return SizedBox(
        width: 347,
        height: 56,
        child: Stack(clipBehavior: Clip.none, children: [
          Positioned.fill(
              child: ClipRRect(
                  borderRadius: BorderRadius.circular(28),
                  child: BackdropFilter(
                      filter: ui.ImageFilter.blur(sigmaX: 6, sigmaY: 6),
                      child: const SizedBox.expand()))),
          sourceLayer('nav', 'F49FDD79-9EFF-47B9-9F75-46536003B9B0', origin),
          sourceLayer('nav', 'C4F39DD1-55FD-435B-8804-602B084E4DAC', origin),
          // Export frame includes 1px around the 20×18 geometric bounds.
          Positioned(
              left: 30,
              top: 12,
              width: 22,
              height: 20,
              child: Image.asset(ExpandedAssets.home,
                  fit: BoxFit.fill, filterQuality: FilterQuality.high)),
          // Missing in Lanhu raw data: boolean outline has layers=[], no points or asset.
          // Keep this explicit approximation separate from exact source paths.
          const Positioned(
              left: 97,
              top: 13,
              width: 20,
              height: 18.973801138537,
              child: CustomPaint(painter: _MessageOutlineApproximation())),
          for (final id in [
            '1730EC45-9AFA-4FA7-B064-34EF01D7317A',
            'CE1CFE5F-AFFD-4831-B066-91AB1EBB2862',
            '58B8A882-9FA0-4E9B-B98C-A41B7DA49A43',
            '5B71ADCC-7CE8-433E-AF40-382E4236BEBF',
            '3D319DC0-7A9E-4FC1-A388-B6FA99D18317',
            'FE65B1E8-88E4-49CA-9262-87A5DC80C90D',
            'A147A367-EF7C-4FAC-965F-A6D27285F529',
            '695C2456-A6CD-4AB6-ABB3-EFF2D4E5378A',
            'C3F74E49-5BC5-4A8D-BD03-77A0C0001436',
            '2F536DCE-DD11-4AA3-A311-7468D485FF8C',
            '650A1E83-B828-4A8F-9CA6-06963EDDE377',
            '14D79984-B6B9-43A6-8D55-426342332DEF',
            '6E0F5DFF-25F1-43BC-AB95-D443881DD9CA',
            '5B91A477-E263-43E2-9328-682BAE055DC2',
            'BBDE7A10-94B1-45C9-836E-C90C10083F21',
            '1AAA75CE-8D4B-4849-8310-6C57B0F08DA0',
            'C05C1798-5A7C-4A4C-92A0-0EBBF23C60B6'
          ])
            sourceLayer('nav', id, origin),
          for (var i = 0; i < 5; i++)
            Positioned(
                left: const [11.0, 77.0, 144.0, 211.0, 272.0][i],
                top: 6,
                width: 60,
                height: 44,
                child: Semantics(
                    button: true,
                    selected: i == 0,
                    label: labels[i],
                    child: MouseRegion(
                        cursor: SystemMouseCursors.click,
                        child: GestureDetector(
                            key: ValueKey('nav-$i'),
                            behavior: HitTestBehavior.opaque,
                            onTap: onSelect == null ? null : () => onSelect!(i),
                            child: const SizedBox.expand())))),
        ]));
  }
}

class NavigationComponentStage extends StatelessWidget {
  const NavigationComponentStage(
      {this.onSelect, this.includeCanvasBackground = true, super.key});
  final ValueChanged<int>? onSelect;
  final bool includeCanvasBackground;
  @override
  Widget build(BuildContext context) => SizedBox(
      width: 375,
      height: 98,
      child: ClipRect(
          child: Stack(clipBehavior: Clip.none, children: [
        if (includeCanvasBackground)
          sourceLayer('nav', '401D0155-DFE5-4E09-9C2D-89EBA74145FC',
              const Offset(0, 714)),
        sourceLayer('nav', 'F2083B30-CFB9-4FC7-A05B-047A7D0A2FBA',
            const Offset(0, 714)),
        Positioned(
            left: 14,
            top: 21,
            child: JuxingBottomNavigation(onSelect: onSelect)),
        sourceLayer('nav', '52E22BDC-0866-482C-B8CC-36255EC2AB7B',
            const Offset(0, 714)),
      ])));
}

class _MessageOutlineApproximation extends CustomPainter {
  const _MessageOutlineApproximation();
  @override
  void paint(Canvas canvas, Size size) {
    final p = Path()
      ..moveTo(10, .75)
      ..cubicTo(4.89, .75, .75, 4.65, .75, 9.46)
      ..cubicTo(.75, 12.01, 1.88, 14.31, 3.75, 15.91)
      ..lineTo(3.13, 18.22)
      ..lineTo(6.65, 17.44)
      ..cubicTo(7.70, 17.85, 8.82, 18.04, 10, 18.04)
      ..cubicTo(15.11, 18.04, 19.25, 14.19, 19.25, 9.46)
      ..cubicTo(19.25, 4.65, 15.11, .75, 10, .75)
      ..close();
    canvas.drawPath(
        p,
        Paint()
          ..color = const Color(0xFF18181B)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.5
          ..strokeJoin = StrokeJoin.round);
  }

  @override
  bool shouldRepaint(_MessageOutlineApproximation oldDelegate) => false;
}
