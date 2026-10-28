// Fidelity render harness for SwiftUI (tool code; copied next to the page's render
// test by `page generate` and kept in sync). App-hosted XCTest on a simulator:
//
//   xcodebuild test -scheme <App> -destination 'platform=iOS Simulator,name=iPhone 15' \
//     -only-testing:<AppTests>/<Page>FidelityTests
//
// Writes <output> (PNG at the given scale), <output>.geometry.json (schema 1) and
// <output>.variants.json (schema 2) in the same format as the Flutter, web and
// Compose harnesses. `checkScene` runs the obligations listed in <Page>.scene.g.json.
import CoreText
import DesignFidelity
import SwiftUI
import UIKit
import XCTest

public struct FidelityDevice {
    public let name: String
    public let width: CGFloat, height: CGFloat, top: CGFloat, bottom: CGFloat
}

public let fidelityDefaultDevices = [
    FidelityDevice(name: "iphone_se", width: 375, height: 667, top: 20, bottom: 0),
    FidelityDevice(name: "iphone_15", width: 393, height: 852, top: 59, bottom: 34),
    FidelityDevice(name: "iphone_15_pro_max", width: 430, height: 932, top: 59, bottom: 34),
    FidelityDevice(name: "android_compact", width: 360, height: 800, top: 24, bottom: 0),
    FidelityDevice(name: "android_large", width: 412, height: 915, top: 24, bottom: 24),
]

/// Collects what the page reports through preferences during a render pass.
final class FidelityRecorder: ObservableObject {
    var frames: [String: CGRect] = [:]
    var texts: [String: CGRect] = [:]
    var bindings: [String: [[String: String]]] = [:]
    var boxes: [String: SourceBoxParams] = [:]
    var scrolls = false
}

struct FidelityRoot<Page: View>: View {
    let page: Page
    let insets: SourceInsets
    let dynamicType: DynamicTypeSize
    let recorder: FidelityRecorder

    var body: some View {
        page
            .environment(\.sourceInsets, insets)
            .environment(\.dynamicTypeSize, dynamicType)
            .overlayPreferenceValue(SourceFramesKey.self) { anchors in
                GeometryReader { proxy in
                    let _ = record { recorder.frames = anchors.mapValues { proxy[$0] } }
                    Color.clear
                }
            }
            .overlayPreferenceValue(SourceTextFramesKey.self) { anchors in
                GeometryReader { proxy in
                    let _ = record { recorder.texts = anchors.mapValues { proxy[$0] } }
                    Color.clear
                }
            }
            .onPreferenceChange(SourceBindingsKey.self) { recorder.bindings = $0 }
            .onPreferenceChange(SourceBoxParamsKey.self) { recorder.boxes = $0 }
            .onPreferenceChange(SourceScrollsKey.self) { recorder.scrolls = $0 }
    }

    private func record(_ update: () -> Void) -> Bool {
        update()
        return true
    }
}

@MainActor
public enum FidelityHarness {
    public static func outputPath(_ variable: String) -> String {
        ProcessInfo.processInfo.environment[variable]
            ?? (NSTemporaryDirectory() as NSString).appendingPathComponent("design-fidelity-\(UUID().uuidString).png")
    }

    /// Registers every design font of the font map under its runtime family.
    public static func loadSourceFontMap(_ path: String) throws {
        SourceFonts.useDesignFonts = true
        let url = URL(fileURLWithPath: (path as NSString).expandingTildeInPath)
        let map = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as? [String: Any] ?? [:]
        for (label, value) in map["fonts"] as? [String: [String: Any]] ?? [:] {
            guard let family = value["runtime_family"] as? String, let raw = value["path"] as? String else { continue }
            var file = URL(fileURLWithPath: (raw as NSString).expandingTildeInPath)
            if !raw.hasPrefix("/") && !raw.hasPrefix("~") { file = url.deletingLastPathComponent().appendingPathComponent(raw) }
            var error: Unmanaged<CFError>?
            CTFontManagerRegisterFontsForURL(file as CFURL, .process, &error)
            guard let descriptors = CTFontManagerCreateFontDescriptorsFromURL(file as CFURL) as? [CTFontDescriptor],
                  let first = descriptors.first,
                  let name = CTFontDescriptorCopyAttribute(first, kCTFontNameAttribute) as? String else {
                throw NSError(domain: "fidelity", code: 1, userInfo: [NSLocalizedDescriptionKey: "Font failed to load: \(file.path)"])
            }
            let weight = Int(label.split(separator: "@").last ?? "") ?? 400
            SourceFonts.register(family: family, weight: weight, postScriptName: name)
        }
    }

    private static func host<Page: View>(_ page: Page, width: CGFloat, height: CGFloat, insets: SourceInsets,
                                         dynamicType: DynamicTypeSize = .large) -> (UIWindow, UIView, FidelityRecorder) {
        let recorder = FidelityRecorder()
        let controller = UIHostingController(rootView: FidelityRoot(page: page, insets: insets, dynamicType: dynamicType, recorder: recorder))
        let window = UIWindow(frame: CGRect(x: 0, y: 0, width: width, height: height))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.frame = window.bounds
        // Let layout and preference passes settle.
        for _ in 0..<3 {
            controller.view.setNeedsLayout()
            controller.view.layoutIfNeeded()
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
        }
        return (window, controller.view, recorder)
    }

    private static func image(_ view: UIView, scale: CGFloat) -> Data {
        let format = UIGraphicsImageRendererFormat()
        format.scale = scale
        format.opaque = false
        return UIGraphicsImageRenderer(bounds: view.bounds, format: format).image { _ in
            view.drawHierarchy(in: view.bounds, afterScreenUpdates: true)
        }.pngData() ?? Data()
    }

    private static func json(_ rects: [String: CGRect]) -> [String: [Double]] {
        rects.mapValues { [$0.minX, $0.minY, $0.width, $0.height].map(Double.init) }
    }

    private static func write(_ path: String, _ value: Any) throws {
        let data = try JSONSerialization.data(withJSONObject: value, options: [.prettyPrinted, .sortedKeys])
        try FileManager.default.createDirectory(atPath: (path as NSString).deletingLastPathComponent, withIntermediateDirectories: true)
        try data.write(to: URL(fileURLWithPath: path))
    }

    /// Renders `page` at the design size and safe area; writes the PNG and geometry.
    public static func capturePage<Page: View>(output: String, width: CGFloat, height: CGFloat, top: CGFloat,
                                               bottom: CGFloat, scale: CGFloat, page: Page) throws {
        let (window, view, recorder) = host(page, width: width, height: height, insets: SourceInsets(top: top, bottom: bottom))
        defer { window.isHidden = true }
        if !recorder.frames.isEmpty {
            try write("\(output).geometry.json", ["schema": 1, "canvas": [Double(width), Double(height)],
                                                   "nodes": json(recorder.frames), "text_nodes": json(recorder.texts)])
        }
        try image(view, scale: scale).write(to: URL(fileURLWithPath: output))
    }

    /// Lays the page out on each device frame at text scale 1.0 and ~1.3 (Dynamic Type xxxLarge).
    public static func captureVariants<Page: View>(output: String, devices: [FidelityDevice] = fidelityDefaultDevices,
                                                   page: Page) throws {
        var variants: [[String: Any]] = []
        for device in devices {
            for (scale, size) in [(1.0, DynamicTypeSize.large), (1.3, DynamicTypeSize.xxxLarge)] {
                let (window, _, recorder) = host(page, width: device.width, height: device.height,
                                                 insets: SourceInsets(top: device.top, bottom: device.bottom), dynamicType: size)
                variants.append(["device": device.name, "width": Double(device.width), "height": Double(device.height),
                                 "padding": ["top": Double(device.top), "bottom": Double(device.bottom)],
                                 "text_scale": scale, "exception": NSNull(), "scrollable": recorder.scrolls,
                                 "nodes": json(recorder.frames), "text_nodes": json(recorder.texts)])
                window.isHidden = true
            }
        }
        try write("\(output).variants.json", ["schema": 2, "variants": variants])
    }

    // MARK: Scene obligations (scene.g.json, shared with the web and Compose harnesses)

    public static func checkScene<Scene: View>(specPath: String, top: CGFloat, bottom: CGFloat, scene: Scene) throws {
        let spec = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: specPath))) as? [String: Any] ?? [:]
        let canvas = spec["canvas"] as? [Double] ?? [375, 812]
        let (window, view, recorder) = host(scene, width: canvas[0], height: canvas[1], insets: SourceInsets(top: top, bottom: bottom))
        defer { window.isHidden = true }
        var failures: [String] = []
        var pixels: UIImage?
        for check in spec["checks"] as? [[String: Any]] ?? [] {
            let label = "\(check["kind"] ?? ""): \(check["id"] ?? "")"
            for bound in check["bound"] as? [[String: Any]] ?? [] {
                let node = bound["node"] as? String ?? ""
                let attr = bound["attr"] as? String ?? ""
                let wanted = bound["equals"] as? [String: String] ?? [:]
                let candidates = (recorder.bindings[node] ?? []).filter { $0[attr] != nil }
                if recorder.frames[node] == nil { failures.append("\(label): \(node): node not rendered"); continue }
                if candidates.isEmpty { failures.append("\(label): \(node): does not render through \(attr)"); continue }
                if !candidates.contains(where: { c in wanted.allSatisfy { c[$0.key] == $0.value } }) {
                    failures.append("\(label): \(node): expected \(wanted), found \(candidates)")
                }
            }
            for member in check["clipped"] as? [String] ?? [] {
                if !(recorder.bindings[member] ?? []).contains(where: { $0["data-df-clipped"] == "1" }) {
                    failures.append("\(label): \(member) is not clipped by its mask shape")
                }
            }
            if let pixel = check["pixel"] as? [String: Any], let at = pixel["at"] as? [Double], let want = pixel["rgb"] as? [Int] {
                let picture = pixels ?? UIImage(data: image(view, scale: 1))!
                pixels = picture
                let got = rgb(picture, x: Int(at[0]), y: Int(at[1]))
                if zip(got, want).map({ abs($0 - $1) }).max() ?? 0 > (pixel["tolerance"] as? Int ?? 3) {
                    failures.append("\(label): composited fills \(got), source \(want)")
                }
            }
            if let band = check["band"] as? [String: Any] {
                if let message = borderBand(band, boxes: recorder.boxes) { failures.append("\(label): \(message)") }
            }
        }
        if !failures.isEmpty { XCTFail("Scene obligations failed:\n" + failures.joined(separator: "\n")) }
    }

    private static func rgb(_ image: UIImage, x: Int, y: Int) -> [Int] {
        guard let cg = image.cgImage, let data = cg.dataProvider?.data, let bytes = CFDataGetBytePtr(data) else { return [0, 0, 0] }
        let px = min(max(x, 0), cg.width - 1), py = min(max(y, 0), cg.height - 1)
        let offset = py * cg.bytesPerRow + px * (cg.bitsPerPixel / 8)
        let info = cg.bitmapInfo.rawValue & CGBitmapInfo.alphaInfoMask.rawValue
        let bgra = cg.bitmapInfo.contains(.byteOrder32Little)
        let r = Int(bytes[offset + (bgra ? 2 : 0)]), g = Int(bytes[offset + 1]), b = Int(bytes[offset + (bgra ? 0 : 2)])
        _ = info
        return [r, g, b]
    }

    /// Renders the node's SourceBox on mid-grey with and without its border (same probe as Flutter).
    private static func borderBand(_ band: [String: Any], boxes: [String: SourceBoxParams]) -> String? {
        let node = band["node"] as? String ?? ""
        guard let params = boxes[node] else { return "\(node): no SourceBox to probe" }
        let t = CGFloat(band["thickness"] as? Double ?? 1)
        let size = band["size"] as? [Double] ?? [0, 0]
        let w = CGFloat(size[0]), h = CGFloat(size[1])
        let margin = t * 2 + 4
        let ratio: CGFloat = 4
        func render(_ box: SourceBoxParams) -> UIImage {
            let probe = ZStack(alignment: .topLeading) {
                Color(white: 128.0 / 255.0)
                SourceBox(box).frame(width: w, height: h).offset(x: margin, y: margin)
            }.frame(width: w + margin * 2, height: h + margin * 2, alignment: .topLeading)
            let (window, view, _) = host(probe, width: w + margin * 2, height: h + margin * 2, insets: SourceInsets(top: 0, bottom: 0))
            defer { window.isHidden = true }
            return UIImage(data: image(view, scale: ratio))!
        }
        var plainParams = params
        plainParams.borders = []
        let bordered = render(params), plain = render(plainParams)
        let y = Int(floor((margin + h / 2) * ratio))
        func px(_ x: CGFloat) -> Int { Int(floor(x * ratio)) }
        func diff(_ x: CGFloat) -> Int { zip(rgb(bordered, x: px(x), y: y), rgb(plain, x: px(x), y: y)).map { abs($0 - $1) }.max() ?? 0 }
        let position = band["position"] as? String ?? "center"
        let at = position == "inside" ? margin + t / 2 : position == "center" ? margin : margin - t / 2
        if diff(at) <= 2 { return "\(node): border band must be painted at \(at)" }
        let outside = position == "inside" ? margin - 1.5 : position == "center" ? margin - t / 2 - 1.5 : margin - t - 1.5
        let inside = position == "inside" ? margin + t + 1.5 : position == "center" ? margin + t / 2 + 1.5 : margin + 1.5
        for x in [outside, inside] where diff(x) > 2 { return "\(node): border must not leak to \(x)" }
        return nil
    }
}
