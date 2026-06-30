import SwiftUI

extension Color {
    /// Create a Color from a hex string like "#66BB6A" or "66BB6A".
    init(hex: String) {
        let cleaned = hex.trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "#", with: "")
        var value: UInt64 = 0
        Scanner(string: cleaned).scanHexInt64(&value)

        let r, g, b: UInt64
        switch cleaned.count {
        case 6:   // RRGGBB
            (r, g, b) = (value >> 16 & 0xFF, value >> 8 & 0xFF, value & 0xFF)
        case 3:   // RGB shorthand
            (r, g, b) = ((value >> 8) * 17, (value >> 4 & 0xF) * 17, (value & 0xF) * 17)
        default:  // fallback green
            (r, g, b) = (102, 187, 106)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: 1
        )
    }
}

/// Preset colors and icons offered when creating a habit.
enum HabitTheme {
    static let colors: [String] = [
        "#EF5350", "#EC407A", "#AB47BC", "#7E57C2", "#5C6BC0",
        "#42A5F5", "#29B6F6", "#26C6DA", "#26A69A", "#66BB6A",
        "#9CCC65", "#FFA726", "#FF7043", "#8D6E63"
    ]

    static let icons: [String] = [
        "star.fill", "drop.fill", "figure.run", "book.fill", "dumbbell.fill",
        "bed.double.fill", "fork.knife", "leaf.fill", "heart.fill", "brain.head.profile",
        "cup.and.saucer.fill", "pencil", "moon.fill", "sun.max.fill"
    ]
}
