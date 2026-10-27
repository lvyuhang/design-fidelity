import 'package:flutter/widgets.dart';

import 'source_paint.dart';

/// An original exported Lanhu asset placed by its export frame.
///
/// [exportRect] is the export frame relative to the node's layout frame (it
/// may extend beyond it because of transparent padding, strokes or shadows).
/// The image is drawn at that rect without clipping and without being squeezed
/// into the layout frame. When null, the asset fills the layout frame.
class SourceAsset extends StatelessWidget {
  const SourceAsset(
    this.asset, {
    super.key,
    this.exportRect,
    this.opacity = 1,
    this.semanticLabel,
    this.package,
  });

  final String asset;
  final Rect? exportRect;
  final double opacity;
  final String? semanticLabel;
  final String? package;

  @override
  Widget build(BuildContext context) {
    final image = Image.asset(
      asset,
      package: package,
      // The generator verified that the export rect has the asset's aspect
      // ratio at a consistent density, so fill is an exact uniform scale.
      fit: BoxFit.fill,
      filterQuality: FilterQuality.medium,
      gaplessPlayback: true,
      opacity: opacity < 1 ? AlwaysStoppedAnimation<double>(opacity) : null,
      semanticLabel: semanticLabel,
      excludeFromSemantics: semanticLabel == null,
    );
    final rect = exportRect;
    if (rect == null) return SizedBox.expand(child: image);
    return Stack(
      clipBehavior: Clip.none,
      fit: StackFit.expand,
      children: [Positioned.fromRect(rect: rect, child: image)],
    );
  }
}

enum SourcePlaceholderShape { rect, roundedRect, circle }

/// Shape-preserving stand-in for a design asset that was never exported.
///
/// It keeps the source frame and outline so neighbours do not move, and it is
/// visibly labelled; it must never be presented as a restored asset.
class SourcePlaceholder extends StatelessWidget {
  const SourcePlaceholder({
    super.key,
    required this.nodeId,
    this.shape = SourcePlaceholderShape.rect,
    this.radius = 0,
    this.label = '设计素材未切图',
  });

  final String nodeId;
  final SourcePlaceholderShape shape;
  final double radius;
  final String label;

  static const Color fillColor = Color(0xFFFFE5EA);
  static const Color strokeColor = Color(0xFFFF4D6D);
  static const Color labelColor = Color(0xFFC52245);

  SourceShape get sourceShape => switch (shape) {
        SourcePlaceholderShape.circle => const SourceOvalShape(),
        SourcePlaceholderShape.roundedRect => SourceRectShape.all(radius),
        SourcePlaceholderShape.rect => const SourceRectShape(),
      };

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '$label ($nodeId)',
      child: ClipPath(
        clipper: SourceShapeClipper(sourceShape),
        child: DecoratedBox(
          decoration: ShapeDecoration(
            color: fillColor,
            shape: switch (shape) {
              SourcePlaceholderShape.circle =>
                const CircleBorder(side: BorderSide(color: strokeColor)),
              SourcePlaceholderShape.roundedRect => RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(radius),
                  side: const BorderSide(color: strokeColor),
                ),
              SourcePlaceholderShape.rect => const RoundedRectangleBorder(
                  side: BorderSide(color: strokeColor),
                ),
            },
          ),
          child: Center(
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Padding(
                padding: const EdgeInsets.all(2),
                child: Text(
                  label,
                  textDirection: TextDirection.ltr,
                  style: const TextStyle(
                    inherit: false,
                    fontSize: 10,
                    height: 1.2,
                    color: labelColor,
                    decoration: TextDecoration.none,
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
