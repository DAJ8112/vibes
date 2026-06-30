import Foundation
import SwiftData

/// Development helper: seeds a few habits with history so we can see the UI
/// (and heatmap) populated. Runs ONLY when the app is launched with the
/// environment variable SEED_SAMPLE_DATA=1, so it never affects real usage.
enum SampleData {
    static var isEnabled: Bool {
        ProcessInfo.processInfo.environment["SEED_SAMPLE_DATA"] == "1"
    }

    @MainActor
    static func seedIfNeeded(_ context: ModelContext) {
        guard isEnabled else { return }

        // Don't double-seed if data already exists.
        let existing = (try? context.fetch(FetchDescriptor<Habit>())) ?? []
        guard existing.isEmpty else { return }

        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())

        let specs: [(name: String, icon: String, color: String, type: TrackingType, goal: Int, prob: Double)] = [
            ("Drink water", "drop.fill", "#42A5F5", .count, 8, 0.8),
            ("Read", "book.fill", "#AB47BC", .binary, 1, 0.65),
            ("Workout", "figure.run", "#EF5350", .binary, 1, 0.5),
        ]

        for (index, spec) in specs.enumerated() {
            let habit = Habit(
                name: spec.name,
                iconSymbol: spec.icon,
                colorHex: spec.color,
                trackingType: spec.type,
                goalAmount: spec.goal,
                sortOrder: index
            )
            context.insert(habit)

            // Generate ~100 days of plausible history.
            for dayOffset in 0..<100 {
                guard Double.random(in: 0...1) < spec.prob else { continue }
                guard let day = calendar.date(byAdding: .day, value: -dayOffset, to: today) else { continue }
                let amount: Int = spec.type == .binary
                    ? 1
                    : max(1, Int.random(in: (spec.goal - 2)...(spec.goal + 1)))
                let entry = HabitEntry(date: day, amount: amount, habit: habit)
                context.insert(entry)
            }
        }

        try? context.save()
    }
}
