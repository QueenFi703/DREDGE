import Foundation

public enum SharedStore {
    private static let key = "surfacedInsight"
    private static let defaults = UserDefaults(suiteName: "group.com.dredge.agent")
    public static func saveSurfaced(_ text: String) { defaults?.set(text, forKey: key) }
    public static func loadSurfaced() -> String { defaults?.string(forKey: key) ?? "Something surfaced…" }
}
