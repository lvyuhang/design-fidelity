import SwiftUI

/// Everything a source shape layer paints; also reported to the scene checks.
public struct SourceBoxParams: Equatable {
    public var shape: SourceShape
    public var fills: [SourceFill]
    public var borders: [SourceBorder]
    public var shadows: [SourceShadow]
    public var opacity: CGFloat

    public init(shape: SourceShape = .rect(), fills: [SourceFill] = [], borders: [SourceBorder] = [],
                shadows: [SourceShadow] = [], opacity: CGFloat = 1) {
        self.shape = shape
        self.fills = fills
        self.borders = borders
        self.shadows = shadows
        self.opacity = opacity
    }

    var attributes: [String: String] {
        [
            "data-df-box": shape.kind,
            "data-df-fills": String(fills.count),
            "data-df-shadows": String(shadows.count),
            "data-df-borders": borders.map { border in
                let position = shape.isClosed ? border.position : .center
                return "\(fidelityNumber(border.thickness)):\(position.rawValue)"
            }.joined(separator: " "),
        ]
    }

    /// Margin that contains every outer shadow and outside border.
    var paintExtent: CGFloat {
        var extent: CGFloat = 0
        for s in shadows where !s.inner {
            extent = max(extent, FidelityEffectMapping.shadowExtent(s.blurRadius, spread: s.spread)
                + max(abs(s.offset.width), abs(s.offset.height)))
        }
        for b in borders { extent = max(extent, b.thickness) }
        return extent + 2
    }
}

/// A source shape layer: outer shadows, fills, inner shadows, borders. Fills its frame.
///
/// * inside / center / outside borders keep the fill geometry unchanged;
/// * outer shadows are knocked out under the shape (not tinted through translucent fills);
/// * shadow spread grows the casting outline before blurring;
/// * layer opacity applies once to the composited layer.
public struct SourceBox: View {
    let params: SourceBoxParams

    public init(shape: SourceShape = .rect(), fills: [SourceFill] = [], borders: [SourceBorder] = [],
                shadows: [SourceShadow] = [], opacity: CGFloat = 1) {
        params = SourceBoxParams(shape: shape, fills: fills, borders: borders, shadows: shadows, opacity: opacity)
    }

    public init(_ params: SourceBoxParams) { self.params = params }

    public var body: some View {
        let extent = params.paintExtent
        // The canvas extends beyond the layout frame so shadows and outside
        // borders are not clipped; negative padding keeps the layout size.
        Canvas { context, size in
            let rect = CGRect(x: extent, y: extent, width: size.width - 2 * extent, height: size.height - 2 * extent)
            draw(&context, rect: rect)
        }
        .padding(-extent)
        .fidelityBinding(params.attributes, box: params)
    }

    private func draw(_ context: inout GraphicsContext, rect: CGRect) {
        guard params.opacity > 0, rect.width >= 0, rect.height >= 0 else { return }
        let shape = params.shape
        let outline = shape.path(in: rect)
        context.opacity = params.opacity
        context.drawLayer { layer in
            for shadow in params.shadows where !shadow.inner {
                layer.drawLayer { s in
                    // Knock out the shape interior: the shadow only exists outside the shape.
                    s.clip(to: outline, options: .inverse)
                    let sigma = FidelityEffectMapping.shadowSigma(shadow.blurRadius)
                    if sigma > 0 { s.addFilter(.blur(radius: FidelityEffectMapping.swiftUIBlurRadius(sigma: sigma))) }
                    let moved = rect.offsetBy(dx: shadow.offset.width, dy: shadow.offset.height)
                    if shape.supportsExactGrow || shadow.spread == 0 {
                        s.fill(shape.path(in: moved, grow: shadow.spread), with: .color(shadow.color))
                    } else {
                        // Free paths grow with a round stroke.
                        s.drawLayer { solid in
                            let path = shape.path(in: moved)
                            solid.fill(path, with: .color(shadow.color))
                            if shadow.spread > 0 {
                                solid.stroke(path, with: .color(shadow.color),
                                             style: StrokeStyle(lineWidth: shadow.spread * 2, lineCap: .round, lineJoin: .round))
                            }
                        }
                    }
                }
            }
            for fill in params.fills {
                layer.fill(outline, with: fill.shading(in: rect), style: shape.fillStyle)
            }
            for shadow in params.shadows where shadow.inner {
                layer.drawLayer { s in
                    s.clip(to: outline)
                    let sigma = FidelityEffectMapping.shadowSigma(shadow.blurRadius)
                    if sigma > 0 { s.addFilter(.blur(radius: FidelityEffectMapping.swiftUIBlurRadius(sigma: sigma))) }
                    let extent = FidelityEffectMapping.shadowExtent(shadow.blurRadius, spread: shadow.spread)
                        + max(abs(shadow.offset.width), abs(shadow.offset.height)) + 2
                    let moved = rect.offsetBy(dx: shadow.offset.width, dy: shadow.offset.height)
                    var ring = Path(rect.insetBy(dx: -extent, dy: -extent))
                    ring.addPath(shape.path(in: moved, grow: shape.supportsExactGrow ? -shadow.spread : 0))
                    s.fill(ring, with: .color(shadow.color), style: FillStyle(eoFill: true))
                }
            }
            for border in params.borders where border.thickness > 0 {
                let position = shape.isClosed ? border.position : .center
                let width = border.thickness * (position == .center ? 1 : 2)
                layer.drawLayer { b in
                    switch position {
                    case .inside: b.clip(to: outline)
                    case .outside: b.clip(to: outline, options: .inverse)
                    case .center: break
                    }
                    b.stroke(outline, with: border.fill.shading(in: rect),
                             style: StrokeStyle(lineWidth: width, lineCap: border.cap, lineJoin: border.join, dash: border.dash))
                }
            }
        }
    }
}
