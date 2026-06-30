import Foundation
import SwiftData

/// One logged day for a habit. At most one entry should exist per (habit, day).
@Model
final class HabitEntry {
    var id: UUID = UUID()
    var date: Date = Date()   // always normalized to the start of the day
    var amount: Int = 0       // binary: 0/1 ; count: 0...goal (or beyond)
    var habit: Habit?

    init(date: Date, amount: Int, habit: Habit? = nil) {
        self.id = UUID()
        self.date = Calendar.current.startOfDay(for: date)
        self.amount = amount
        self.habit = habit
    }
}
