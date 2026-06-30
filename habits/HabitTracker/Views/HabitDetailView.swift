import SwiftUI
import SwiftData
import WidgetKit

/// Shows a single habit: a labeled heatmap overview, stats, and a tappable
/// monthly calendar for logging any day.
struct HabitDetailView: View {
    @Environment(\.modelContext) private var context
    @Bindable var habit: Habit
    @State private var showingEdit = false

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(spacing: 24) {
                    header
                    heatmapSection
                    calendarSection
                    statsSection
                        .id("bottom")
                }
                .padding()
            }
            .onAppear {
                // Dev-only: scroll to the calendar for screenshots.
                if ProcessInfo.processInfo.environment["SCROLL_BOTTOM"] == "1" {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                        withAnimation { proxy.scrollTo("bottom", anchor: .bottom) }
                    }
                }
            }
        }
        .navigationTitle(habit.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Edit") { showingEdit = true }
            }
        }
        .sheet(isPresented: $showingEdit) {
            AddEditHabitView(habit: habit)
        }
    }

    private var header: some View {
        VStack(spacing: 8) {
            Image(systemName: habit.iconSymbol)
                .font(.system(size: 44))
                .foregroundStyle(Color(hex: habit.colorHex))
            Text(habit.name)
                .font(.title2.bold())
        }
    }

    private var statsSection: some View {
        let color = Color(hex: habit.colorHex)
        return LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            StatCard(title: "Streak",
                     value: "\(HabitStats.currentStreak(for: habit))",
                     unit: "days", systemImage: "flame.fill", color: color,
                     footnote: "Best \(HabitStats.longestStreak(for: habit))")
            StatCard(title: "This month",
                     value: "\(HabitStats.completedThisMonth(for: habit))",
                     unit: "days", systemImage: "calendar", color: color)
        }
    }

    private var heatmapSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("History")
                .font(.headline)
            Text(habit.trackingType == .binary
                 ? "Tap a day to mark it done."
                 : "Tap a day to add one; tap past the goal to reset.")
                .font(.caption2)
                .foregroundStyle(.secondary)

            LabeledHeatmapView(source: habit, weeks: 26) { day in
                cycle(on: day)
            }

            HStack {
                Spacer()
                HeatmapLegend(colorHex: habit.colorHex)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    private var calendarSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Calendar")
                .font(.headline)
            Text(habit.trackingType == .binary
                 ? "Tap a day to mark it done."
                 : "Tap a day to add one; tap past the goal to reset.")
                .font(.caption2)
                .foregroundStyle(.secondary)

            MonthCalendarView(habit: habit) { day in
                cycle(on: day)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    /// Heatmap tap behavior: binary toggles; count adds one and wraps to 0 past the goal.
    private func cycle(on date: Date) {
        let current = habit.amount(on: date)
        let next: Int
        if habit.trackingType == .binary {
            next = current > 0 ? 0 : 1
        } else {
            next = current >= habit.goalAmount ? 0 : current + 1
        }
        setAmount(next, on: date)
    }

    /// Set a day's logged amount, creating/updating/deleting the entry as needed.
    private func setAmount(_ newAmount: Int, on date: Date) {
        let clamped = max(0, newAmount)
        if let entry = habit.entry(on: date) {
            if clamped == 0 {
                context.delete(entry)
            } else {
                entry.amount = clamped
            }
        } else if clamped > 0 {
            let entry = HabitEntry(date: date, amount: clamped, habit: habit)
            context.insert(entry)
        }
        WidgetCenter.shared.reloadAllTimelines()
    }
}
