import WidgetKit
import SwiftUI
import SwiftData

// The timeline entry, snapshot data type, and view live in HabitWidgetUI.swift
// (shared with the app so we can preview the exact widget view in-app).

struct Provider: TimelineProvider {
    func placeholder(in context: Context) -> HabitWidgetEntry { .placeholder }

    func getSnapshot(in context: Context, completion: @escaping (HabitWidgetEntry) -> Void) {
        completion(loadEntry() ?? .placeholder)
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<HabitWidgetEntry>) -> Void) {
        let entry = loadEntry() ?? .placeholder
        // Refresh roughly hourly; the app also nudges reloads when data changes.
        let next = Calendar.current.date(byAdding: .hour, value: 1, to: Date()) ?? Date().addingTimeInterval(3600)
        completion(Timeline(entries: [entry], policy: .after(next)))
    }

    /// Read the first habit from the shared store and snapshot it.
    private func loadEntry() -> HabitWidgetEntry? {
        guard let entry = WidgetData.firstHabitEntry() else { return nil }
        return entry
    }
}

/// Reads the shared SwiftData store and builds a widget snapshot. Shared with
/// the app's in-app preview so both go through the same code path.
enum WidgetData {
    static func firstHabitEntry() -> HabitWidgetEntry? {
        guard let container = try? makeContainer() else { return nil }
        let context = ModelContext(container)

        var descriptor = FetchDescriptor<Habit>(sortBy: [SortDescriptor(\.sortOrder)])
        descriptor.fetchLimit = 1
        guard let habit = try? context.fetch(descriptor).first else { return nil }

        var amounts: [Date: Int] = [:]
        for entry in habit.entries {
            amounts[Calendar.current.startOfDay(for: entry.date)] = entry.amount
        }
        let data = HabitHeatmapData(colorHex: habit.colorHex, goalAmount: habit.goalAmount, amounts: amounts)

        return HabitWidgetEntry(
            date: Date(),
            title: habit.name,
            iconSymbol: habit.iconSymbol,
            data: data,
            currentStreak: HabitStats.currentStreak(for: habit)
        )
    }

    static func makeContainer() throws -> ModelContainer {
        let schema = Schema([Habit.self, HabitEntry.self])
        let config = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: false,
            groupContainer: .identifier(AppGroup.identifier)
        )
        return try ModelContainer(for: schema, configurations: [config])
    }
}

struct HabitWidget: Widget {
    let kind = "HabitWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: Provider()) { entry in
            HabitWidgetView(entry: entry)
                .containerBackground(for: .widget) { Color(.systemBackground) }
        }
        .configurationDisplayName("Habit Heatmap")
        .description("Your most recent habit activity at a glance.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

@main
struct HabitWidgetBundle: WidgetBundle {
    var body: some Widget {
        HabitWidget()
    }
}
