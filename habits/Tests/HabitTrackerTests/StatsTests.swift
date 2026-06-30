import Testing
import Foundation
import SwiftData
@testable import HabitTracker

/// Unit tests for the pure stats logic (no UI, fast and deterministic).
struct StatsTests {
    let calendar = Calendar.current

    /// Helper: a start-of-day date `offset` days from today.
    func day(_ offset: Int) -> Date {
        calendar.date(byAdding: .day, value: offset, to: calendar.startOfDay(for: Date()))!
    }

    @Test func currentStreakCountsConsecutiveDaysEndingToday() {
        let days: Set<Date> = [day(0), day(-1), day(-2)]
        #expect(HabitStats.currentStreak(completedDays: days) == 3)
    }

    @Test func currentStreakAllowsUnfinishedToday() {
        // Today not completed yet, but yesterday + the day before are.
        let days: Set<Date> = [day(-1), day(-2)]
        #expect(HabitStats.currentStreak(completedDays: days) == 2)
    }

    @Test func currentStreakIsZeroWhenRecentGap() {
        let days: Set<Date> = [day(-2), day(-3)]
        #expect(HabitStats.currentStreak(completedDays: days) == 0)
    }

    @Test func longestStreakFindsMaxRun() {
        let days: Set<Date> = [day(-10), day(-9), day(-8), day(-5), day(-4)]
        #expect(HabitStats.longestStreak(completedDays: days) == 3)
    }

    @Test func longestStreakOfEmptyIsZero() {
        #expect(HabitStats.longestStreak(completedDays: []) == 0)
    }

    @Test func completedThisMonthCountsOnlyCurrentMonth() {
        // Build explicit dates so the test doesn't drift near month boundaries.
        func date(_ year: Int, _ month: Int, _ day: Int) -> Date {
            calendar.date(from: DateComponents(year: year, month: month, day: day))!
        }
        let reference = date(2026, 6, 15)
        let days: Set<Date> = [
            date(2026, 6, 3),    // June  ✓
            date(2026, 6, 14),   // June  ✓
            date(2026, 5, 31),   // May   ✗
            date(2026, 7, 1),    // July  ✗
        ]
        #expect(HabitStats.completedThisMonth(completedDays: days, asOf: reference) == 2)
    }

    @Test func completedThisMonthOfEmptyIsZero() {
        #expect(HabitStats.completedThisMonth(completedDays: [], asOf: Date()) == 0)
    }

    @Test func heatmapLevelBuckets() {
        #expect(HeatmapView.level(amount: 0, goal: 8) == 0)   // nothing logged
        #expect(HeatmapView.level(amount: 1, goal: 1) == 4)   // binary complete = full
        #expect(HeatmapView.level(amount: 8, goal: 8) == 4)   // goal met = full
        #expect(HeatmapView.level(amount: 2, goal: 8) >= 1)   // partial = some shade
        #expect(HeatmapView.level(amount: 2, goal: 8) < 4)    // ...but not full
    }

    /// A model-level test using an in-memory SwiftData store.
    @MainActor
    @Test func habitCompletionRespectsGoal() throws {
        let config = ModelConfiguration(isStoredInMemoryOnly: true)
        let container = try ModelContainer(for: Habit.self, HabitEntry.self, configurations: config)
        let context = container.mainContext

        let habit = Habit(name: "Water", trackingType: .count, goalAmount: 5)
        context.insert(habit)

        let today = calendar.startOfDay(for: Date())
        context.insert(HabitEntry(date: today, amount: 4, habit: habit))
        #expect(habit.isComplete(on: today) == false)   // 4 < goal 5

        habit.entry(on: today)?.amount = 5
        #expect(habit.isComplete(on: today) == true)     // 5 >= goal 5
        #expect(HabitStats.currentStreak(for: habit) == 1)
    }
}
