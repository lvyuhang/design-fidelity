import SwiftUI
import UIKit

/// Where exported design assets are loaded from (an app bundle folder reference).
public enum SourceAssets {
    public static var bundle: Bundle = .main

    static func image(_ path: String) -> UIImage? {
        let url = URL(fileURLWithPath: path)
        let name = url.deletingPathExtension().lastPathComponent
        let folder = url.deletingLastPathComponent().relativePath
        guard let file = bundle.url(forResource: name, withExtension: url.pathExtension,
                                    subdirectory: folder == "." ? nil : folder) else { return nil }
        return UIImage(contentsOfFile: file.path)
    }
}

/// An exported source asset drawn in its export frame (which may exceed the node box).
public struct SourceAsset: View {
    let path: String
    let exportRect: CGRect?

    public init(_ path: String, exportRect: CGRect? = nil) {
        self.path = path
        self.exportRect = exportRect
    }

    public var body: some View {
        let attributes = ["data-df-asset": exportRect.map {
            [$0.minX, $0.minY, $0.width, $0.height].map(fidelityNumber).joined(separator: " ")
        } ?? ""]
        ZStack(alignment: .topLeading) {
            if let image = SourceAssets.image(path) {
                // The export rect has the bitmap's aspect at one density: fill is an exact scale.
                let picture = Image(uiImage: image).resizable().interpolation(.medium)
                if let rect = exportRect {
                    picture.frame(width: rect.width, height: rect.height).offset(x: rect.minX, y: rect.minY)
                } else {
                    picture
                }
            } else {
                SourcePlaceholder(nodeId: path, label: "素材缺失")
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .fidelityBinding(attributes)
    }
}

/// Missing exported asset: same frame, pink, labelled; never a drawn guess.
public struct SourcePlaceholder: View {
    let nodeId: String
    let label: String

    public init(nodeId: String, label: String = "设计素材未切图") {
        self.nodeId = nodeId
        self.label = label
    }

    public var body: some View {
        ZStack {
            Color(red: 1, green: 0.898, blue: 0.918)
            Text(label).font(.system(size: 10)).foregroundColor(Color(red: 0.773, green: 0.133, blue: 0.271))
                .minimumScaleFactor(0.1).padding(2)
        }
        .overlay(Rectangle().strokeBorder(Color(red: 1, green: 0.302, blue: 0.427), lineWidth: 1))
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityLabel("\(label) (\(nodeId))")
        .fidelityBinding(["data-df-placeholder": nodeId])
    }
}

private extension View {
    func fill(_ fill: Bool) -> some View {
        frame(maxWidth: fill ? .infinity : nil, maxHeight: fill ? .infinity : nil, alignment: .topLeading)
    }
}

/// Layer opacity composited once, like Sketch/Figma layer opacity.
public struct SourceOpacity<Content: View>: View {
    let value: CGFloat
    let fill: Bool
    let content: () -> Content

    public init(_ value: CGFloat, fill: Bool = true, @ViewBuilder content: @escaping () -> Content) {
        self.value = value
        self.fill = fill
        self.content = content
    }

    public var body: some View {
        content().fill(fill).compositingGroup().opacity(value)
            .fidelityBinding(["data-df-opacity": fidelityNumber(value)])
    }
}

public struct SourceFlip<Content: View>: View {
    let x: Bool
    let y: Bool
    let fill: Bool
    let content: () -> Content

    public init(x: Bool = false, y: Bool = false, fill: Bool = true, @ViewBuilder content: @escaping () -> Content) {
        self.x = x
        self.y = y
        self.fill = fill
        self.content = content
    }

    public var body: some View {
        content().fill(fill).scaleEffect(x: x ? -1 : 1, y: y ? -1 : 1)
    }
}

/// Gaussian layer blur; sigma = 0.5 x source radius.
public struct SourceLayerBlur<Content: View>: View {
    let radius: CGFloat
    let fill: Bool
    let content: () -> Content

    public init(_ radius: CGFloat, fill: Bool = true, @ViewBuilder content: @escaping () -> Content) {
        self.radius = radius
        self.fill = fill
        self.content = content
    }

    public var body: some View {
        let sigma = FidelityEffectMapping.layerBlurSigma(radius)
        content().fill(fill).blur(radius: FidelityEffectMapping.swiftUIBlurRadius(sigma: sigma), opaque: false)
            .fidelityBinding(["data-df-layer-blur": fidelityNumber(radius)])
    }
}

/// Background blur. SwiftUI materials have no calibrated radius, so this draws
/// the layer itself only; the generator reports the effect as unsupported for
/// SwiftUI and the scene check does not bind it.
public struct SourceBackdropBlur<Content: View>: View {
    let content: () -> Content

    public init(radius: CGFloat, shape: SourceShape = .rect(), saturation: CGFloat = 1,
                @ViewBuilder content: @escaping () -> Content) {
        self.content = content
    }

    public var body: some View { content() }
}

/// SwiftUI `Shape` for a source shape (clip to a mask layer).
public struct SourceClipShape: Shape {
    let shape: SourceShape
    public init(_ shape: SourceShape) { self.shape = shape }
    public func path(in rect: CGRect) -> Path { shape.path(in: rect) }
}

/// Clips the masked members to the mask layer's shape.
public struct SourceClip<Content: View>: View {
    let shape: SourceShape
    let content: () -> Content

    public init(_ shape: SourceShape, @ViewBuilder content: @escaping () -> Content) {
        self.shape = shape
        self.content = content
    }

    public var body: some View {
        ZStack(alignment: .topLeading) { content() }
            .environment(\.sourceClipped, true)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .clipShape(SourceClipShape(shape), style: FillStyle(eoFill: { if case let .path(_, _, eo) = shape { return eo }; return false }()))
    }
}
