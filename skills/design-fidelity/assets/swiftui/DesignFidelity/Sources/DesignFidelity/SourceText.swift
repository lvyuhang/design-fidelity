import SwiftUI
import UIKit

/// A source text style in design points; production fonts are chosen per platform.
public struct SourceTextSpec: Equatable {
    /// Design (fidelity) family, registered from the font map during fidelity renders.
    public var family: String
    /// Production family per platform ("ios"); nil value = system font, absent key = `family`.
    public var platforms: [String: String?]
    public var size: CGFloat
    public var weight: Int
    /// Absolute line height in design points; nil = font default.
    public var lineHeight: CGFloat?
    public var letterSpacing: CGFloat
    public var color: Color
    public var underline: Bool
    public var strikethrough: Bool

    public init(family: String, platforms: [String: String?] = [:], size: CGFloat, weight: Int = 400,
                lineHeight: CGFloat? = nil, letterSpacing: CGFloat = 0, color: Color,
                underline: Bool = false, strikethrough: Bool = false) {
        self.family = family
        self.platforms = platforms
        self.size = size
        self.weight = weight
        self.lineHeight = lineHeight
        self.letterSpacing = letterSpacing
        self.color = color
        self.underline = underline
        self.strikethrough = strikethrough
    }
}

/// Registered font faces by family and weight. The fidelity harness registers
/// the design fonts from the font map and sets `useDesignFonts`; apps register
/// any licensed production family they map in font-map.json.
public enum SourceFonts {
    public static var useDesignFonts = false
    private static var faces: [String: [Int: String]] = [:]

    /// Maps `family` at `weight` to a registered PostScript name.
    public static func register(family: String, weight: Int, postScriptName: String) {
        faces[family, default: [:]][weight] = postScriptName
    }

    static func postScriptName(_ family: String, weight: Int) -> String? {
        guard let weights = faces[family], !weights.isEmpty else { return nil }
        if let exact = weights[weight] { return exact }
        return weights.min(by: { abs($0.key - weight) < abs($1.key - weight) })?.value
    }

    /// (SwiftUI font, UIKit font for metrics) at a Dynamic Type scaled size.
    static func fonts(_ spec: SourceTextSpec, size: CGFloat) -> (Font, UIFont) {
        let family: String?
        if useDesignFonts || spec.platforms["ios"] == nil {
            family = spec.family
        } else {
            family = spec.platforms["ios"] ?? nil
        }
        if let family, let name = postScriptName(family, weight: spec.weight) ?? (UIFont(name: family, size: size) != nil ? family : nil),
           let ui = UIFont(name: name, size: size) {
            return (.custom(name, fixedSize: size), ui)
        }
        let weight = uiWeight(spec.weight)
        return (.system(size: size, weight: fontWeight(spec.weight)), .systemFont(ofSize: size, weight: weight))
    }

    static func fontWeight(_ w: Int) -> Font.Weight {
        switch w {
        case ..<150: return .ultraLight
        case ..<250: return .thin
        case ..<350: return .light
        case ..<450: return .regular
        case ..<550: return .medium
        case ..<650: return .semibold
        case ..<750: return .bold
        case ..<850: return .heavy
        default: return .black
        }
    }

    static func uiWeight(_ w: Int) -> UIFont.Weight {
        switch w {
        case ..<150: return .ultraLight
        case ..<250: return .thin
        case ..<350: return .light
        case ..<450: return .regular
        case ..<550: return .medium
        case ..<650: return .semibold
        case ..<750: return .bold
        case ..<850: return .heavy
        default: return .black
        }
    }
}

extension DynamicTypeSize {
    var contentSizeCategory: UIContentSizeCategory {
        switch self {
        case .xSmall: return .extraSmall
        case .small: return .small
        case .medium: return .medium
        case .large: return .large
        case .xLarge: return .extraLarge
        case .xxLarge: return .extraExtraLarge
        case .xxxLarge: return .extraExtraExtraLarge
        case .accessibility1: return .accessibilityMedium
        case .accessibility2: return .accessibilityLarge
        case .accessibility3: return .accessibilityExtraLarge
        case .accessibility4: return .accessibilityExtraExtraLarge
        case .accessibility5: return .accessibilityExtraExtraExtraLarge
        @unknown default: return .large
        }
    }
}

/// Text that reproduces a source text box: absolute line height with even
/// leading (half above, half below), explicit tracking, no ambient styles.
/// Auto-width source text stays on one line; fixed-width boxes wrap. Dynamic
/// Type scales sizes and line heights; the fidelity harness pins it to `.large`.
public struct SourceText: View {
    let runs: [(String, SourceTextSpec)]
    let style: SourceTextSpec
    let align: TextAlignment
    let wrap: Bool
    @Environment(\.dynamicTypeSize) private var dynamicType
    @Environment(\.sourceNodeID) private var nodeID

    public init(_ text: String, style: SourceTextSpec, align: TextAlignment = .leading, wrap: Bool = false) {
        runs = [(text, style)]
        self.style = style
        self.align = align
        self.wrap = wrap
    }

    public init(runs: [(String, SourceTextSpec)], style: SourceTextSpec, align: TextAlignment = .leading, wrap: Bool = false) {
        self.runs = runs
        self.style = style
        self.align = align
        self.wrap = wrap
    }

    private func scaled(_ value: CGFloat) -> CGFloat {
        UIFontMetrics(forTextStyle: .body).scaledValue(
            for: value, compatibleWith: UITraitCollection(preferredContentSizeCategory: dynamicType.contentSizeCategory))
    }

    public var body: some View {
        let (_, baseFont) = SourceFonts.fonts(style, size: scaled(style.size))
        let line = style.lineHeight.map(scaled) ?? baseFont.lineHeight
        let extra = max(0, line - baseFont.lineHeight)
        let text = runs.reduce(Text("")) { result, run in
            let (chunk, spec) = run
            let (font, _) = SourceFonts.fonts(spec, size: scaled(spec.size))
            return result + Text(chunk).font(font).foregroundColor(spec.color)
                .tracking(scaled(spec.letterSpacing)).underline(spec.underline).strikethrough(spec.strikethrough)
        }
        text
            .lineSpacing(extra)
            .padding(.vertical, extra / 2)
            .multilineTextAlignment(align)
            .lineLimit(wrap ? nil : 1)
            .fixedSize(horizontal: !wrap, vertical: true)
            .frame(maxWidth: wrap ? .infinity : nil, alignment: Alignment(horizontal: align == .center ? .center : align == .trailing ? .trailing : .leading, vertical: .top))
            .fidelityBinding(["data-df-text": ""])
            .anchorPreference(key: SourceTextFramesKey.self, value: .bounds) { anchor in
                nodeID.map { [$0: anchor] } ?? [:]
            }
    }
}
