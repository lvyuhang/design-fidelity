import SwiftUI
import UIKit

// MARK: - Bindings and geometry reported to the fidelity harness

/// Frames of `fidelity:<node id>` layers.
public struct SourceFramesKey: PreferenceKey {
    public static var defaultValue: [String: Anchor<CGRect>] = [:]
    public static func reduce(value: inout [String: Anchor<CGRect>], nextValue: () -> [String: Anchor<CGRect>]) {
        value.merge(nextValue()) { _, new in new }
    }
}

/// Paragraph frames per node (text drawn by SourceText).
public struct SourceTextFramesKey: PreferenceKey {
    public static var defaultValue: [String: Anchor<CGRect>] = [:]
    public static func reduce(value: inout [String: Anchor<CGRect>], nextValue: () -> [String: Anchor<CGRect>]) {
        value.merge(nextValue()) { old, _ in old }
    }
}

/// Primitive bindings per node: `data-df-*` attribute sets (same names as the web primitives).
public struct SourceBindingsKey: PreferenceKey {
    public static var defaultValue: [String: [[String: String]]] = [:]
    public static func reduce(value: inout [String: [[String: String]]], nextValue: () -> [String: [[String: String]]]) {
        value.merge(nextValue()) { $0 + $1 }
    }
}

/// SourceBox parameters per node, for the border-band probe.
public struct SourceBoxParamsKey: PreferenceKey {
    public static var defaultValue: [String: SourceBoxParams] = [:]
    public static func reduce(value: inout [String: SourceBoxParams], nextValue: () -> [String: SourceBoxParams]) {
        value.merge(nextValue()) { old, _ in old }
    }
}

private struct SourceNodeIDKey: EnvironmentKey { static let defaultValue: String? = nil }
private struct SourceClippedKey: EnvironmentKey { static let defaultValue = false }

extension EnvironmentValues {
    public var sourceNodeID: String? {
        get { self[SourceNodeIDKey.self] }
        set { self[SourceNodeIDKey.self] = newValue }
    }

    var sourceClipped: Bool {
        get { self[SourceClippedKey.self] }
        set { self[SourceClippedKey.self] = newValue }
    }
}

struct FidelityBinding: ViewModifier {
    let attributes: [String: String]
    let box: SourceBoxParams?
    @Environment(\.sourceNodeID) private var nodeID

    func body(content: Content) -> some View {
        content
            .preference(key: SourceBindingsKey.self, value: nodeID.map { [$0: [attributes]] } ?? [:])
            .transformPreference(SourceBoxParamsKey.self) { value in
                if let nodeID, let box, value[nodeID] == nil { value[nodeID] = box }
            }
    }
}

extension View {
    func fidelityBinding(_ attributes: [String: String], box: SourceBoxParams? = nil) -> some View {
        modifier(FidelityBinding(attributes: attributes, box: box))
    }
}

// MARK: - Placement (Flutter Positioned semantics)

/// Places its child in the proposed (parent) frame: any of left/top/right/bottom,
/// explicit width/height, or left+right / top+bottom to stretch. Without a size
/// on an axis the child keeps its ideal size (auto-width text). Fills the parent.
public struct SourcePlaced: Layout {
    public var left, top, right, bottom, width, height: CGFloat?

    public init(left: CGFloat? = nil, top: CGFloat? = nil, right: CGFloat? = nil, bottom: CGFloat? = nil,
                width: CGFloat? = nil, height: CGFloat? = nil) {
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.width = width
        self.height = height
    }

    public func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        proposal.replacingUnspecifiedDimensions()
    }

    public func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        for subview in subviews {
            var w = width
            if w == nil, let left, let right { w = max(0, bounds.width - left - right) }
            var h = height
            if h == nil, let top, let bottom { h = max(0, bounds.height - top - bottom) }
            let ideal = subview.sizeThatFits(ProposedViewSize(width: w, height: h))
            let fw = w ?? ideal.width
            let fh = h ?? ideal.height
            let x = left ?? (right.map { bounds.width - $0 - fw } ?? 0)
            let y = top ?? (bottom.map { bounds.height - $0 - fh } ?? 0)
            subview.place(at: CGPoint(x: bounds.minX + x, y: bounds.minY + y), anchor: .topLeading,
                          proposal: ProposedViewSize(width: fw, height: fh))
        }
    }
}

// MARK: - Overrides, taps, safe area

public struct SceneOverrides {
    public var overrides: [String: () -> AnyView]
    public var onTap: [String: () -> Void]
    public init(overrides: [String: () -> AnyView] = [:], onTap: [String: () -> Void] = [:]) {
        self.overrides = overrides
        self.onTap = onTap
    }
}

private struct SceneOverridesKey: EnvironmentKey { static let defaultValue = SceneOverrides() }

/// Safe-area insets forced by the fidelity harness; apps leave it nil.
public struct SourceInsets: Equatable {
    public var top: CGFloat
    public var bottom: CGFloat
    public init(top: CGFloat, bottom: CGFloat) {
        self.top = top
        self.bottom = bottom
    }
}

private struct SourceInsetsKey: EnvironmentKey { static let defaultValue: SourceInsets? = nil }

extension EnvironmentValues {
    var sceneOverrides: SceneOverrides {
        get { self[SceneOverridesKey.self] }
        set { self[SceneOverridesKey.self] = newValue }
    }

    public var sourceInsets: SourceInsets? {
        get { self[SourceInsetsKey.self] }
        set { self[SourceInsetsKey.self] = newValue }
    }
}

/// Run-time offsets of root layers: device inset minus design inset.
public struct SceneInsets {
    public var dy: CGFloat
    public var dyBottom: CGFloat
}

/// One source layer. `fill` boxes fill the placed frame; text keeps its
/// intrinsic size. Overrides replace the content inside the same frame.
public struct SourceNode<Content: View>: View {
    let id: String
    let fill: Bool
    let content: () -> Content
    @Environment(\.sceneOverrides) private var scene
    @Environment(\.sourceClipped) private var clipped

    public init(_ id: String, fill: Bool = true, @ViewBuilder content: @escaping () -> Content) {
        self.id = id
        self.fill = fill
        self.content = content
    }

    public var body: some View {
        let node = Group {
            if let override = scene.overrides[id] { override() } else { content() }
        }
        .environment(\.sourceNodeID, id)
        .frame(maxWidth: fill ? .infinity : nil, maxHeight: fill ? .infinity : nil, alignment: .topLeading)
        .contentShape(Rectangle())
        .anchorPreference(key: SourceFramesKey.self, value: .bounds) { [id: $0] }
        .transformPreference(SourceBindingsKey.self) { value in
            if clipped { value[id, default: []].append(["data-df-clipped": "1"]) }
        }
        if let tap = scene.onTap[id] {
            node.onTapGesture(perform: tap)
        } else {
            node
        }
    }
}

/// Full-screen page frame. Root layers move with the safe area, the body
/// scrolls when the screen is shorter than the design, footers stay pinned
/// above the bottom inset. Use it as the whole screen; do not add safe-area padding.
public struct SourceScene<Body: View, Footer: View>: View {
    let size: CGSize
    let designTop: CGFloat
    let designBottom: CGFloat
    let adaptSafeArea: Bool
    let overrides: SceneOverrides
    let content: (SceneInsets) -> Body
    let footer: (SceneInsets) -> Footer
    @Environment(\.sourceInsets) private var forced

    public init(designSize: CGSize, designTop: CGFloat, designBottom: CGFloat, adaptSafeArea: Bool = true,
                overrides: SceneOverrides = SceneOverrides(),
                @ViewBuilder footer: @escaping (SceneInsets) -> Footer,
                @ViewBuilder content: @escaping (SceneInsets) -> Body) {
        size = designSize
        self.designTop = designTop
        self.designBottom = designBottom
        self.adaptSafeArea = adaptSafeArea
        self.overrides = overrides
        self.content = content
        self.footer = footer
    }

    public var body: some View {
        GeometryReader { geometry in
            // The reader respects the safe area (so its insets are the device's);
            // the page itself is drawn edge to edge.
            let safe = geometry.safeAreaInsets
            let top = !adaptSafeArea ? designTop : (forced?.top ?? safe.top)
            let bottom = !adaptSafeArea ? designBottom : (forced?.bottom ?? safe.bottom)
            let insets = SceneInsets(dy: top - designTop, dyBottom: bottom - designBottom)
            let natural = size.height + insets.dy + insets.dyBottom
            let available = geometry.size.height + safe.top + safe.bottom
            let scrolls = available < natural - 0.5
            ZStack(alignment: .topLeading) {
                if scrolls {
                    ScrollView(.vertical, showsIndicators: false) {
                        ZStack(alignment: .topLeading) { content(insets) }
                            .frame(maxWidth: .infinity)
                            .frame(height: natural)
                    }
                } else {
                    ZStack(alignment: .topLeading) { content(insets) }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
                ZStack(alignment: .topLeading) { footer(insets) }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .ignoresSafeArea()
            .clipped()
            .preference(key: SourceScrollsKey.self, value: scrolls)
        }
        .environment(\.sceneOverrides, overrides)
    }
}

public struct SourceScrollsKey: PreferenceKey {
    public static var defaultValue = false
    public static func reduce(value: inout Bool, nextValue: () -> Bool) { value = value || nextValue() }
}
