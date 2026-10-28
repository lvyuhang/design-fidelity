import 'package:flutter/widgets.dart';

// Independent synthetic fixture. No production implementation is reused.
class SourceFixture extends StatelessWidget {
  const SourceFixture({super.key, this.iconOffset = 0});
  final double iconOffset;
  @override
  Widget build(BuildContext context) => SizedBox(
    width: 375, height: 812,
    child: ColoredBox(color: const Color(0xFFFFFFFF), child: Stack(children: [
      Positioned(left: 15, top: 15 + iconOffset, width: 30, height: 30,
        child: Image.asset('assets/icon.png')),
      const Positioned(left: 60, top: 20, width: 100, height: 20,
        child: ColoredBox(color: Color(0xFF222222))),
      const Positioned(left: 16, top: 714, width: 343, height: 50,
        child: ColoredBox(color: Color(0xFF222222))),
    ])),
  );
}
