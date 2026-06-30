import SwiftUI
import SwiftData

/// Dev-only screen that renders the exact widget view using real data from the
/// shared store, at both supported sizes. Lets us verify the widget UI without
/// manually adding it to the simulator's home screen.
struct WidgetPreviewView: View {
    @Environment(\.dismiss) private var dismiss
    @Query(sort: \Habit.sortOrder) private var habits: [Habit]

    var body: some View {
        let entry = makeEntry()
        NavigationStack {
            ScrollView {
                VStack(spacing: 28) {
                    card(entry: entry, width: 158, height: 158, weeks: 9, label: "Small")
                    card(entry: entry, width: 338, height: 158, weeks: 20, label: "Medium")
                }
                .padding()
                .frame(maxWidth: .infinity)
            }
            .background(Color(.secondarySystemBackground))
            .navigationTitle("Widget preview")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    private func makeEntry() -> HabitWidgetEntry {
        guard let habit = habits.first else { return .placeholder }
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

    private func card(entry: HabitWidgetEntry, width: CGFloat, height: CGFloat, weeks: Int, label: String) -> some View {
        VStack(spacing: 8) {
            HabitWidgetView(entry: entry, weeksOverride: weeks)
                .padding()
                .frame(width: width, height: height)
                .background(Color(.systemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                .shadow(color: .black.opacity(0.12), radius: 8, y: 3)
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}
