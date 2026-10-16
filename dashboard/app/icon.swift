// Draws the app icon (1024 px PNG) for make_app.py: the dashboard's navy, a cream gate, "GPP".
// Status: PROPOSED (Claude, 2026-10-10). Usage: swiftc -o icon icon.swift && ./icon out.png

import Cocoa

let size: CGFloat = 1024
let out = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "icon.png"
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: Int(size), pixelsHigh: Int(size), bitsPerSample: 8,
                           samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB,
                           bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)

let navy = NSColor(red: 0x1f / 255, green: 0x3a / 255, blue: 0x5f / 255, alpha: 1)
let cream = NSColor(red: 0xf4 / 255, green: 0xf3 / 255, blue: 0xef / 255, alpha: 1)
navy.setFill()
NSBezierPath(roundedRect: NSRect(x: 100, y: 100, width: 824, height: 824), xRadius: 185, yRadius: 185).fill()

// The gate: two posts and an arch.
cream.setStroke()
let gate = NSBezierPath()
gate.lineWidth = 56
gate.lineCapStyle = .round
gate.move(to: NSPoint(x: 330, y: 330))
gate.line(to: NSPoint(x: 330, y: 600))
gate.appendArc(withCenter: NSPoint(x: 512, y: 600), radius: 182, startAngle: 180, endAngle: 0, clockwise: true)
gate.line(to: NSPoint(x: 694, y: 330))
gate.stroke()

let text = NSAttributedString(string: "GPP", attributes: [
    .font: NSFont(name: "Georgia-Bold", size: 150) ?? NSFont.boldSystemFont(ofSize: 150),
    .foregroundColor: cream, .kern: 6])
let w = text.size().width
text.draw(at: NSPoint(x: 512 - w / 2, y: 160))

NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
