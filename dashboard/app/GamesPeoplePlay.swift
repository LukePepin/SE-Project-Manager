// Games-People-Play as a Mac app (D-049): one native window around the local dashboard.
//
// Status: PROPOSED (AI-drafted by Claude on 2026-10-10 from Luke's direction: "move it out of the port
// into a 'application' rather than a website"; not reviewed by Luke).
//
// The app starts dashboard/server.py, shows it in a WebKit window with no browser around it, and stops the
// server when the window closes. The server still listens on 127.0.0.1 inside the app, so the code stays one
// standard-library Python program on macOS and Windows; the port is just never seen. Built by make_app.py,
// which writes the repo path, Python and port into Info.plist (GPPRepo, GPPPython, GPPPort).

import Cocoa
import WebKit

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
    var window: NSWindow!
    var web: WKWebView!
    var server: Process?
    let info = Bundle.main.infoDictionary ?? [:]
    // Its own free port each launch: a dashboard left running elsewhere (an old version, say) can never stand in for
    // this one, which happened on 10/10 with a server started from Terminal the day before.
    lazy var port: Int = AppDelegate.freePort() ?? ((info["GPPPort"] as? Int) ?? 8765)
    var home: URL { URL(string: "http://127.0.0.1:\(port)/")! }

    static func freePort() -> Int? {
        let fd = socket(AF_INET, SOCK_STREAM, 0)
        guard fd >= 0 else { return nil }
        defer { close(fd) }
        var addr = sockaddr_in()
        addr.sin_family = sa_family_t(AF_INET)
        addr.sin_addr.s_addr = inet_addr("127.0.0.1")
        addr.sin_port = 0
        var len = socklen_t(MemoryLayout<sockaddr_in>.size)
        let bound = withUnsafeMutablePointer(to: &addr) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) { Darwin.bind(fd, $0, len) == 0 && Darwin.getsockname(fd, $0, &len) == 0 }
        }
        return bound ? Int(UInt16(bigEndian: addr.sin_port)) : nil
    }

    func applicationDidFinishLaunching(_ note: Notification) {
        startServer()
        let config = WKWebViewConfiguration()
        config.userContentController.add(self, name: "copy")  // the page's Copy buttons
        web = WKWebView(frame: .zero, configuration: config)
        web.navigationDelegate = self
        web.uiDelegate = self
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1200, height: 860),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "Games-People-Play"
        window.contentView = web
        window.center()
        window.setFrameAutosaveName("GamesPeoplePlayMain")
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        message("Starting…")
        waitThenLoad(tries: 0)
    }

    func startServer() {
        let repo = info["GPPRepo"] as? String ?? ""
        let python = info["GPPPython"] as? String ?? "/usr/bin/python3"
        let logURL = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Games-People-Play.log")
        FileManager.default.createFile(atPath: logURL.path, contents: nil)
        let log = try? FileHandle(forWritingTo: logURL)
        let p = Process()
        p.executableURL = URL(fileURLWithPath: python)
        p.arguments = [repo + "/dashboard/server.py", "--port", String(port)]
        p.currentDirectoryURL = URL(fileURLWithPath: repo)
        var env = ProcessInfo.processInfo.environment  // apps start with a bare PATH; /start needs `claude`
        let home = NSHomeDirectory()
        env["PATH"] = "\(home)/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + (env["PATH"] ?? "")
        p.environment = env
        p.standardOutput = log
        p.standardError = log
        do { try p.run(); server = p } catch { message("Could not start Python at \(python): \(error.localizedDescription)") }
    }

    func waitThenLoad(tries: Int) {
        var req = URLRequest(url: home)
        req.timeoutInterval = 1
        URLSession.shared.dataTask(with: req) { data, _, _ in
            DispatchQueue.main.async {
                if let d = data, String(decoding: d, as: UTF8.self).contains("<title>Games-People-Play</title>") {
                    self.web.load(URLRequest(url: self.home))
                } else if tries < 80 {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { self.waitThenLoad(tries: tries + 1) }
                } else {
                    self.message("The dashboard did not start. See ~/Library/Logs/Games-People-Play.log")
                }
            }
        }.resume()
    }

    func message(_ text: String) {
        web.loadHTMLString("<body style='font:17px Georgia,serif;color:#1f3a5f;padding:48px'>\(text)</body>", baseURL: nil)
    }

    func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage) {
        if let text = m.body as? String {
            NSPasteboard.general.clearContents()
            NSPasteboard.general.setString(text, forType: .string)
        }
    }

    // Links to folders and other sites open in Finder or the browser, not in this window.
    func webView(_ w: WKWebView, decidePolicyFor a: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let u = a.request.url, u.scheme != "about", !(u.scheme == "http" && u.host == "127.0.0.1") {
            NSWorkspace.shared.open(u)
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    func webView(_ w: WKWebView, createWebViewWith c: WKWebViewConfiguration, for a: WKNavigationAction,
                 windowFeatures f: WKWindowFeatures) -> WKWebView? {
        if let u = a.request.url { NSWorkspace.shared.open(u) }
        return nil
    }

    @objc func reloadPage(_ sender: Any?) { web.reload() }

    func applicationShouldTerminateAfterLastWindowClosed(_ s: NSApplication) -> Bool { true }

    func applicationWillTerminate(_ note: Notification) { server?.terminate() }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)

// Menus: Quit and Reload, and the Edit menu, without which Cmd-V would not paste a brain dump.
let mainMenu = NSMenu()
let appItem = NSMenuItem()
mainMenu.addItem(appItem)
let appMenu = NSMenu()
appMenu.addItem(withTitle: "Reload", action: #selector(AppDelegate.reloadPage(_:)), keyEquivalent: "r")
appMenu.addItem(NSMenuItem.separator())
appMenu.addItem(withTitle: "Quit Games-People-Play", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
appItem.submenu = appMenu
let editItem = NSMenuItem()
mainMenu.addItem(editItem)
let editMenu = NSMenu(title: "Edit")
editMenu.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
let redo = editMenu.addItem(withTitle: "Redo", action: Selector(("redo:")), keyEquivalent: "z")
redo.keyEquivalentModifierMask = [.command, .shift]
editMenu.addItem(NSMenuItem.separator())
editMenu.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
editMenu.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
editMenu.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
editMenu.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
editItem.submenu = editMenu
app.mainMenu = mainMenu
app.run()
