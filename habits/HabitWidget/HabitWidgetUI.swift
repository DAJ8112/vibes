import WidgetKit
import SwiftUI

/// A value-type snapshot of a habit's data so the widget can render the heatmap
/// without holding a live SwiftData object across reloads. Also reused by an
/// in-app preview screen.
struct HabitHeatmapData: HeatmapSource {
    let colorHex: String
    let goalAmount: Int
    let amounts: [Date: Int]

    func amount(on day: Date) -> Int {
        amounts[Calendar.current.startOfDay(for: day)] ?? 0
    }
}

struct HabitWidgetEntry: TimelineEntry {
    let date: Date
    let title: String
    let iconSymbol: String
    let data: HabitHeatmapData
    let currentStreak: Int

    static let placeholder = HabitWidgetEntry(
        date: Date(),
        title: "Drink water",
        iconSymbol: "drop.fill",
        data: HabitHeatmapData(colorHex: "#42A5F5", goalAmount: 8, amounts: [:]),
        currentStreak: 0
    )
}

struct HabitWidgetView: View {
    var entry: HabitWidgetEntry
    /// When set, overrides the week count (used by the in-app preview, where the
    /// real `widgetFamily` environment value isn't available to set).
    var weeksOverride: Int? = nil
    @Environment(\.widgetFamily) private var family

    private var weeks: Int { weeksOverride ?? (family == .systemSmall ? 9 : 20) }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                Image(systemName: entry.iconSymbol)
                    .foregroundStyle(Color(hex: entry.data.colorHex))
                Text(entry.title)
                    .font(.headline)
                    .lineLimit(1)
                Spacer(minLength: 0)
                if entry.currentStreak > 0 {
                    Label("\(entry.currentStreak)", systemImage: "flame.fill")
                        .font(.caption2)
                        .foregroundStyle(.orange)
                }
            }
            Spacer(minLength: 0)
            HeatmapView(source: entry.data, weeks: weeks, cellSize: 12, spacing: 2)
        }
    }
}
