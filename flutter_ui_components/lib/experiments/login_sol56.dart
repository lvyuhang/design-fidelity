import 'package:flutter/widgets.dart';

/// Source-backed login controls for the 375 x 395 evidence region.
class Sol56LoginComponentStage extends StatelessWidget {
  const Sol56LoginComponentStage({
    super.key,
    this.onProviderTap,
  });

  final ValueChanged<String>? onProviderTap;

  static const double width = 375;
  static const double height = 395;

  static const _buttonFill = Color.fromRGBO(255, 253, 249, 0.85);
  static const _buttonBorder = Color(0xFFEEDCC4);
  static const _buttonShadow = Color.fromRGBO(216, 155, 71, 0.10);
  static const _buttonText = Color(0xFF22242A);
  static const _agreementText = Color(0xFF91919B);

  static const _wechatAsset =
      'assets/lanhu/assets/05d568660f8b15118112812d36654cc19a41abfa447fcaf5aa60ea9eba71a8db.png';
  static const _qqAsset =
      'assets/lanhu/assets/6ae1b2c8ae7ea66059d0dc46e6197f7ea99ea82ac2cddc0c66beb254b8d1798d.png';
  static const _phoneAsset =
      'assets/lanhu/assets/aa419996555f658c1ee97725d7f9fa542e2992af291636eff79e96e9dfa5855d.png';
  static const _appleAsset =
      'assets/lanhu/assets/9b1e35de0078f86a5139ce45acbb9fae30e8548c2fa8029fb8116dce58924a87.png';
  static const _uncheckedAsset =
      'assets/lanhu/assets/9d0654e6ecfa4fe81881a272ab3990f51329b81d32eaecc985c37e6084f234c8.png';

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      height: height,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          _providerButton(
            id: 'wechat',
            label: '微信登录',
            top: 10,
            iconAsset: _wechatAsset,
            iconLeft: 103,
            iconTop: 16,
            iconWidth: 22.8148148148148,
            iconHeight: 18.7407407407407,
            textWidth: 56,
          ),
          _providerButton(
            id: 'qq',
            label: 'QQ登录',
            top: 78,
            iconAsset: _qqAsset,
            iconLeft: 105,
            iconTop: 16,
            iconWidth: 18.7407407407407,
            iconHeight: 18.7407407407407,
            textWidth: 50,
          ),
          _providerButton(
            id: 'phone',
            label: '手机号登录',
            top: 146,
            iconAsset: _phoneAsset,
            iconLeft: 108,
            iconTop: 15,
            iconWidth: 13.6363636363636,
            iconHeight: 20,
            textWidth: 70,
          ),
          _providerButton(
            id: 'apple',
            label: '苹果登录',
            top: 214,
            iconAsset: _appleAsset,
            iconLeft: 108,
            iconTop: 16,
            iconWidth: 15.402116,
            iconHeight: 18.7504020869565,
            textWidth: 60,
          ),
          Positioned(
            left: 28,
            top: 346,
            width: 14,
            height: 14,
            child: Image.asset(
              _uncheckedAsset,
              fit: BoxFit.fill,
              filterQuality: FilterQuality.high,
            ),
          ),
          const Positioned(
            left: 48,
            top: 345,
            width: 301,
            height: 32,
            child: Text(
              '我已阅读并同意《用户协议》、《隐私协议》、《用户违规行为管理办法》、《运营商认证服务条款》',
              maxLines: 2,
              overflow: TextOverflow.clip,
              style: TextStyle(
                fontFamily: 'SourcePingFang',
                fontSize: 11,
                fontWeight: FontWeight.w400,
                height: 16 / 11,
                letterSpacing: 0,
                color: _agreementText,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _providerButton({
    required String id,
    required String label,
    required double top,
    required String iconAsset,
    required double iconLeft,
    required double iconTop,
    required double iconWidth,
    required double iconHeight,
    required double textWidth,
  }) {
    return Positioned(
      left: 38,
      top: top,
      width: 299,
      height: 50,
      child: Semantics(
        button: true,
        label: label,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: onProviderTap == null ? null : () => onProviderTap!(id),
          child: Stack(
            children: [
              const Positioned.fill(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: _buttonFill,
                    borderRadius: BorderRadius.all(Radius.circular(25)),
                    border: Border.fromBorderSide(
                      BorderSide(
                        color: _buttonBorder,
                        width: 1,
                        strokeAlign: BorderSide.strokeAlignInside,
                      ),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: _buttonShadow,
                        offset: Offset(0, 6),
                        blurRadius: 12,
                      ),
                    ],
                  ),
                ),
              ),
              Positioned(
                left: iconLeft,
                top: iconTop,
                width: iconWidth,
                height: iconHeight,
                child: Image.asset(
                  iconAsset,
                  fit: BoxFit.fill,
                  filterQuality: FilterQuality.high,
                ),
              ),
              Positioned(
                left: 134,
                top: 15,
                width: textWidth,
                height: 20,
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.clip,
                  style: const TextStyle(
                    fontFamily: 'SourcePingFang',
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    height: 20 / 14,
                    letterSpacing: 0,
                    color: _buttonText,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
