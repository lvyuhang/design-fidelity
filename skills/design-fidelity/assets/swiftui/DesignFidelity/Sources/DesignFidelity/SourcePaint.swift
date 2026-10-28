import SwiftUI

/// Source shapes; geometry in design points. Same semantics as the Flutter,
/// web and Compose primitives.
public enum SourceShape: Equatable {
    /// Corner radii: top-left, top-right, bottom-right, bottom-left.
    case rect(radii: [CGFloat] = [0, 0, 0, 0])
    case oval
    /// Points in unit coordinates of the layer box.
    case path(points: [SourcePathPoint], closed: Bool = true, evenOdd: Bool = false)

    public static func rect(_ all: CGFloat) -> SourceShape { .rect(radii: [all, all, all, all]) }

    public var isClosed: Bool {
        if case let .path(_, closed, _) = self { return closed }
        return true
    }

    public var supportsExactGrow: Bool {
        if case .path = self { return false }
        return true
    }

    public var kind: String {
        switch self {
        case .rect: return "rect"
        case .oval: return "oval"
        case .path: return "path"
        }
    }

    /// Outline of `rect` grown by `grow` points (negative shrinks).
    public func path(in rect: CGRect, grow: CGFloat = 0) -> Path {
        switch self {
        case let .rect(radii):
            let r = rect.insetBy(dx: -grow, dy: -grow)
            func radius(_ i: Int) -> CGFloat {
                let source = min(i < radii.count ? radii[i] : 0, min(rect.width, rect.height) / 2)
                // Clamped on the source rect, then grown with it (concentric spread).
                return source > 0 || grow > 0 ? max(0, source + grow) : 0
            }
            return Path { p in
                let tl = radius(0), tr = radius(1), br = radius(2), bl = radius(3)
                p.move(to: CGPoint(x: r.minX + tl, y: r.minY))
                p.addLine(to: CGPoint(x: r.maxX - tr, y: r.minY))
                p.addArc(tangent1End: CGPoint(x: r.maxX, y: r.minY), tangent2End: CGPoint(x: r.maxX, y: r.minY + tr), radius: tr)
                p.addLine(to: CGPoint(x: r.maxX, y: r.maxY - br))
                p.addArc(tangent1End: CGPoint(x: r.maxX, y: r.maxY), tangent2End: CGPoint(x: r.maxX - br, y: r.maxY), radius: br)
                p.addLine(to: CGPoint(x: r.minX + bl, y: r.maxY))
                p.addArc(tangent1End: CGPoint(x: r.minX, y: r.maxY), tangent2End: CGPoint(x: r.minX, y: r.maxY - bl), radius: bl)
                p.addLine(to: CGPoint(x: r.minX, y: r.minY + tl))
                p.addArc(tangent1End: CGPoint(x: r.minX, y: r.minY), tangent2End: CGPoint(x: r.minX + tl, y: r.minY), radius: tl)
                p.closeSubpath()
            }
        case .oval:
            return Path(ellipseIn: rect.insetBy(dx: -grow, dy: -grow))
        case let .path(points, closed, _):
            return Path { p in
                guard let first = points.first else { return }
                func at(_ v: CGPoint) -> CGPoint { CGPoint(x: rect.minX + v.x * rect.width, y: rect.minY + v.y * rect.height) }
                p.move(to: at(first.point))
                let count = closed ? points.count + 1 : points.count
                for i in 1..<max(count, 1) {
                    let previous = points[(i - 1) % points.count]
                    let current = points[i % points.count]
                    if previous.curveFrom != nil || current.curveTo != nil {
                        p.addCurve(to: at(current.point), control1: at(previous.curveFrom ?? previous.point),
                                   control2: at(current.curveTo ?? current.point))
                    } else {
                        p.addLine(to: at(current.point))
                    }
                }
                if closed { p.closeSubpath() }
            }
        }
    }

    var fillStyle: FillStyle {
        if case let .path(_, _, evenOdd) = self { return FillStyle(eoFill: evenOdd, antialiased: true) }
        return FillStyle(eoFill: false, antialiased: true)
    }
}

public struct SourcePathPoint: Equatable {
    public var point: CGPoint
    public var curveFrom: CGPoint?
    public var curveTo: CGPoint?

    public init(_ point: CGPoint, curveFrom: CGPoint? = nil, curveTo: CGPoint? = nil) {
        self.point = point
        self.curveFrom = curveFrom
        self.curveTo = curveTo
    }
}

public struct SourceGradientStop: Equatable {
    public var position: CGFloat
    public var color: Color
    public init(_ position: CGFloat, _ color: Color) {
        self.position = position
        self.color = color
    }
}

/// Linear gradient between two unit points of the layer box.
public struct SourceLinearGradient: Equatable {
    public var from: CGPoint
    public var to: CGPoint
    public var stops: [SourceGradientStop]
    public init(from: CGPoint, to: CGPoint, stops: [SourceGradientStop]) {
        self.from = from
        self.to = to
        self.stops = stops
    }
}

public enum SourceFill: Equatable {
    case solid(Color, opacity: CGFloat = 1)
    case linear(SourceLinearGradient, opacity: CGFloat = 1)

    func shading(in rect: CGRect) -> GraphicsContext.Shading {
        switch self {
        case let .solid(color, opacity):
            return .color(color.opacity(opacity))
        case let .linear(gradient, opacity):
            func at(_ v: CGPoint) -> CGPoint { CGPoint(x: rect.minX + v.x * rect.width, y: rect.minY + v.y * rect.height) }
            let stops = gradient.stops.map { Gradient.Stop(color: $0.color.opacity(opacity), location: $0.position) }
            return .linearGradient(Gradient(stops: stops), startPoint: at(gradient.from), endPoint: at(gradient.to))
        }
    }
}

public enum SourceBorderPosition: String, Equatable { case inside, center, outside }

public struct SourceBorder: Equatable {
    public var thickness: CGFloat
    public var fill: SourceFill
    public var position: SourceBorderPosition
    public var cap: CGLineCap
    public var join: CGLineJoin
    public var dash: [CGFloat]

    public init(thickness: CGFloat, fill: SourceFill, position: SourceBorderPosition = .center,
                cap: CGLineCap = .butt, join: CGLineJoin = .miter, dash: [CGFloat] = []) {
        self.thickness = thickness
        self.fill = fill
        self.position = position
        self.cap = cap
        self.join = join
        self.dash = dash
    }
}

public struct SourceShadow: Equatable {
    public var color: Color
    public var offset: CGSize
    /// Source blur radius; sigma = 0.5 x radius (FidelityEffectMapping).
    public var blurRadius: CGFloat
    public var spread: CGFloat
    public var inner: Bool

    public init(color: Color, offset: CGSize = .zero, blurRadius: CGFloat = 0, spread: CGFloat = 0, inner: Bool = false) {
        self.color = color
        self.offset = offset
        self.blurRadius = blurRadius
        self.spread = spread
        self.inner = inner
    }
}

/// The single place where design effect radii become blur parameters.
///
/// SwiftUI's `blur(radius:)` / `GraphicsContext.Filter.blur(radius:)` take the
/// Gaussian standard deviation. Recalibrate here, once, if a device comparison
/// shows a different factor.
public enum FidelityEffectMapping {
    public static let shadowSigmaPerRadius: CGFloat = 0.5
    public static let layerBlurSigmaPerRadius: CGFloat = 0.5

    public static func shadowSigma(_ radius: CGFloat) -> CGFloat { radius <= 0 ? 0 : radius * shadowSigmaPerRadius }
    public static func layerBlurSigma(_ radius: CGFloat) -> CGFloat { radius <= 0 ? 0 : radius * layerBlurSigmaPerRadius }
    public static func swiftUIBlurRadius(sigma: CGFloat) -> CGFloat { sigma }

    /// Visible extent of a Gaussian beyond the source edge (~3 sigma).
    public static func shadowExtent(_ radius: CGFloat, spread: CGFloat) -> CGFloat { shadowSigma(radius) * 3 + abs(spread) }
}

/// Same compact number format as the generators ("1", "0.5", "1.25").
public func fidelityNumber(_ value: CGFloat) -> String {
    var text = String(format: "%.4f", locale: Locale(identifier: "en_US_POSIX"), Double(value))
    while text.contains(".") && (text.hasSuffix("0") || text.hasSuffix(".")) { text.removeLast() }
    return text == "-0" || text.isEmpty ? "0" : text
}
