import Cocoa
import Darwin
import WebKit

private enum ClientError: LocalizedError {
    case missingResource(String)
    case noPort
    case serverStopped
    case serverTimeout

    var errorDescription: String? {
        switch self {
        case .missingResource(let name): return "客户端缺少组件：\(name)"
        case .noPort: return "无法为本地服务分配端口。"
        case .serverStopped: return "本地验收服务启动失败，请查看客户端日志。"
        case .serverTimeout: return "本地验收服务启动超时。"
        }
    }
}

private final class ReviewServer {
    let process: Process
    let port: Int
    private let logHandle: FileHandle

    init(resources: URL, support: URL) throws {
        let executable = resources.appendingPathComponent("review-server/review-server")
        let adb = resources.appendingPathComponent("platform-tools/adb")
        let scrcpy = resources.appendingPathComponent("scrcpy-server-v4.1")
        for file in [executable, adb, scrcpy] where !FileManager.default.isExecutableFile(atPath: file.path) && file != scrcpy {
            throw ClientError.missingResource(file.lastPathComponent)
        }
        guard FileManager.default.fileExists(atPath: scrcpy.path) else {
            throw ClientError.missingResource(scrcpy.lastPathComponent)
        }

        port = try Self.availablePort()
        let logURL = support.appendingPathComponent("client.log")
        if !FileManager.default.fileExists(atPath: logURL.path) {
            FileManager.default.createFile(atPath: logURL.path, contents: nil)
        }
        logHandle = try FileHandle(forWritingTo: logURL)
        try logHandle.seekToEnd()

        process = Process()
        process.executableURL = executable
        process.arguments = ["--port", String(port)]
        var environment = ProcessInfo.processInfo.environment
        environment["REVIEW_DATA_DIR"] = support.appendingPathComponent("data").path
        environment["REVIEW_ADB"] = adb.path
        environment["REVIEW_SCRCPY_SERVER"] = scrcpy.path
        process.environment = environment
        process.currentDirectoryURL = resources
        process.standardOutput = logHandle
        process.standardError = logHandle
        try process.run()
    }

    func waitUntilReady() throws -> URL {
        let url = URL(string: "http://127.0.0.1:\(port)/")!
        for _ in 0..<160 {
            if !process.isRunning { throw ClientError.serverStopped }
            if let data = try? Data(contentsOf: url), !data.isEmpty { return url }
            Thread.sleep(forTimeInterval: 0.1)
        }
        throw ClientError.serverTimeout
    }

    func stop() {
        if process.isRunning {
            process.terminate()
            for _ in 0..<20 where process.isRunning { Thread.sleep(forTimeInterval: 0.05) }
            if process.isRunning { kill(process.processIdentifier, SIGKILL) }
        }
        try? logHandle.close()
    }

    private static func availablePort() throws -> Int {
        // Keep the public loopback URL stable so browser bookmarks and copied
        // review links continue to work after the client restarts.
        if canBind(port: 8769) { return 8769 }

        let descriptor = socket(AF_INET, SOCK_STREAM, 0)
        guard descriptor >= 0 else { throw ClientError.noPort }
        defer { close(descriptor) }
        var address = sockaddr_in()
        address.sin_len = UInt8(MemoryLayout<sockaddr_in>.size)
        address.sin_family = sa_family_t(AF_INET)
        address.sin_port = 0
        address.sin_addr.s_addr = inet_addr("127.0.0.1")
        let bound = withUnsafePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                Darwin.bind(descriptor, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        guard bound == 0 else { throw ClientError.noPort }
        var length = socklen_t(MemoryLayout<sockaddr_in>.size)
        let resolved = withUnsafeMutablePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                getsockname(descriptor, $0, &length)
            }
        }
        guard resolved == 0 else { throw ClientError.noPort }
        return Int(UInt16(bigEndian: address.sin_port))
    }

    private static func canBind(port: UInt16) -> Bool {
        let descriptor = socket(AF_INET, SOCK_STREAM, 0)
        guard descriptor >= 0 else { return false }
        defer { close(descriptor) }
        // Match HTTPServer's SO_REUSEADDR behavior: recently closed connections
        // in TIME_WAIT must not make a free service port look occupied.
        var reuse: Int32 = 1
        setsockopt(descriptor, SOL_SOCKET, SO_REUSEADDR, &reuse, socklen_t(MemoryLayout<Int32>.size))
        var address = sockaddr_in()
        address.sin_len = UInt8(MemoryLayout<sockaddr_in>.size)
        address.sin_family = sa_family_t(AF_INET)
        address.sin_port = port.bigEndian
        address.sin_addr.s_addr = inet_addr("127.0.0.1")
        return withUnsafePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                Darwin.bind(descriptor, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        } == 0
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate {
    private var window: NSWindow!
    private var webView: WKWebView!
    private var server: ReviewServer?
    private var spinner: NSProgressIndicator!
    private var statusLabel: NSTextField!
    private var downloads: [WKDownload] = []

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        configureMenu()
        configureWindow()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        startClient()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    func applicationWillTerminate(_ notification: Notification) {
        server?.stop()
    }

    @objc private func reloadPage() { webView?.reload() }
    @objc private func actualSize() { webView?.magnification = 1 }
    @objc private func showDataFolder() {
        if let folder = try? supportDirectory() { NSWorkspace.shared.activateFileViewerSelecting([folder]) }
    }

    private func configureMenu() {
        let menu = NSMenu()
        let appItem = NSMenuItem()
        menu.addItem(appItem)
        let appMenu = NSMenu()
        appItem.submenu = appMenu
        appMenu.addItem(withTitle: "关于设计验收", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "打开验收数据文件夹", action: #selector(showDataFolder), keyEquivalent: "d")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "退出设计验收", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")

        let viewItem = NSMenuItem()
        menu.addItem(viewItem)
        let viewMenu = NSMenu(title: "显示")
        viewItem.submenu = viewMenu
        viewMenu.addItem(withTitle: "重新载入", action: #selector(reloadPage), keyEquivalent: "r")
        viewMenu.addItem(withTitle: "实际大小", action: #selector(actualSize), keyEquivalent: "0")
        NSApp.mainMenu = menu
    }

    private func configureWindow() {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1440, height: 920),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
                          backing: .buffered, defer: false)
        window.title = "设计验收"
        window.minSize = NSSize(width: 1080, height: 700)
        window.center()
        window.titlebarAppearsTransparent = true

        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.allowsMagnification = true
        webView.autoresizingMask = [.width, .height]
        window.contentView = webView

        let loading = NSVisualEffectView(frame: webView.bounds)
        loading.identifier = NSUserInterfaceItemIdentifier("loading")
        loading.autoresizingMask = [.width, .height]
        loading.material = .contentBackground
        loading.blendingMode = .withinWindow
        loading.state = .active
        spinner = NSProgressIndicator()
        spinner.style = .spinning
        spinner.controlSize = .large
        spinner.startAnimation(nil)
        statusLabel = NSTextField(labelWithString: "正在准备设计验收…")
        statusLabel.font = .systemFont(ofSize: 15, weight: .medium)
        statusLabel.textColor = .secondaryLabelColor
        let stack = NSStackView(views: [spinner, statusLabel])
        stack.orientation = .vertical
        stack.spacing = 18
        stack.alignment = .centerX
        stack.translatesAutoresizingMaskIntoConstraints = false
        loading.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: loading.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: loading.centerYAnchor)
        ])
        webView.addSubview(loading)
    }

    private func startClient() {
        guard let resources = Bundle.main.resourceURL else {
            show(error: ClientError.missingResource("Resources")); return
        }
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self else { return }
            do {
                let support = try self.prepareData(resources: resources)
                let server = try ReviewServer(resources: resources, support: support)
                let url = try server.waitUntilReady()
                DispatchQueue.main.async {
                    self.server = server
                    self.webView.load(URLRequest(url: url))
                }
            } catch {
                DispatchQueue.main.async { self.show(error: error) }
            }
        }
    }

    private func supportDirectory() throws -> URL {
        let base = try FileManager.default.url(for: .applicationSupportDirectory,
                                               in: .userDomainMask,
                                               appropriateFor: nil,
                                               create: true)
        let support = base.appendingPathComponent("设计验收", isDirectory: true)
        try FileManager.default.createDirectory(at: support, withIntermediateDirectories: true)
        return support
    }

    private func prepareData(resources: URL) throws -> URL {
        let support = try supportDirectory()
        let destination = support.appendingPathComponent("data", isDirectory: true)
        let marker = destination.appendingPathComponent(".seed-complete")
        if FileManager.default.fileExists(atPath: marker.path) { return support }
        DispatchQueue.main.async { self.statusLabel.stringValue = "首次启动，正在导入当前验收资料…" }
        let seed = resources.appendingPathComponent("SeedData", isDirectory: true)
        guard FileManager.default.fileExists(atPath: seed.path) else {
            throw ClientError.missingResource("SeedData")
        }
        let staging = support.appendingPathComponent("data-importing", isDirectory: true)
        try? FileManager.default.removeItem(at: staging)
        try FileManager.default.copyItem(at: seed, to: staging)
        if FileManager.default.fileExists(atPath: destination.path) {
            try FileManager.default.removeItem(at: destination)
        }
        try FileManager.default.moveItem(at: staging, to: destination)
        FileManager.default.createFile(atPath: marker.path, contents: Data("1\n".utf8))
        return support
    }

    private func show(error: Error) {
        spinner.stopAnimation(nil)
        statusLabel.textColor = .systemRed
        statusLabel.stringValue = error.localizedDescription
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        webView.subviews.first(where: { $0.identifier?.rawValue == "loading" })?.removeFromSuperview()
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url else { decisionHandler(.cancel); return }
        if url.scheme == "blob" || url.host == "127.0.0.1" || url.host == "localhost" {
            decisionHandler(navigationAction.shouldPerformDownload ? .download : .allow)
        } else {
            NSWorkspace.shared.open(url)
            decisionHandler(.cancel)
        }
    }

    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = navigationAction.request.url { NSWorkspace.shared.open(url) }
        return nil
    }

    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) {
        downloads.append(download)
        download.delegate = self
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationResponse: WKNavigationResponse,
                 decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        decisionHandler(navigationResponse.canShowMIMEType ? .allow : .download)
    }

    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) {
        downloads.append(download)
        download.delegate = self
    }

    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse,
                  suggestedFilename: String, completionHandler: @escaping (URL?) -> Void) {
        let downloadsFolder = FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask)[0]
        var destination = downloadsFolder.appendingPathComponent(suggestedFilename)
        var suffix = 2
        while FileManager.default.fileExists(atPath: destination.path) {
            let stem = (suggestedFilename as NSString).deletingPathExtension
            let ext = (suggestedFilename as NSString).pathExtension
            destination = downloadsFolder.appendingPathComponent("\(stem)-\(suffix).\(ext)")
            suffix += 1
        }
        completionHandler(destination)
    }

    func downloadDidFinish(_ download: WKDownload) {
        downloads.removeAll { $0 === download }
    }

    func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
        downloads.removeAll { $0 === download }
    }
}

@main
private enum DesignReviewMain {
    static func main() {
        let application = NSApplication.shared
        let delegate = AppDelegate()
        application.delegate = delegate
        application.run()
    }
}
