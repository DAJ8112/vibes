import Foundation
import SwiftData

/// How a habit is measured each day.
enum TrackingType: Int, Codable, CaseIterable, Identifiable {
    case binary = 0   // done / not done
    case count  = 1   // count toward a daily goal (e.g. 5 glasses of water)

    var id: Int { rawValue }

    var label: String {
        switch self {
        case .binary: return "Done / Not done"
        case .count:  return "Count toward a goal"
        }
    }
}

/// A single habit the user tracks. Owns a list of daily `HabitEntry` records.
@Model
final class Habit {
    var id: UUID = UUID()
    var name: String = ""
    var iconSymbol: String = "star.fill"   // an SF Symbol name
    var colorHex: String = "#66BB6A"       // theme color, stored as hex
    var trackingTypeRaw: Int = TrackingType.binary.rawValue
    var goalAmount: Int = 1                 // 1 for binary; daily target for count
    var reminderTime: Date?                 // time-of-day for a daily reminder
    var reminderEnabled: Bool = false
    var createdAt: Date = Date()
    var sortOrder: Int = 0

    // Deleting a habit deletes all of its entries (cascade).
    @Relationship(deleteRule: .cascade, inverse: \HabitEntry.habit)
    var entries: [HabitEntry] = []

    init(
        name: String,
        iconSymbol: String = "star.fill",
        colorHex: String = "#66BB6A",
        trackingType: TrackingType = .binary,
        goalAmount: Int = 1,
        reminderTime: Date? = nil,
        reminderEnabled: Bool = false,
        sortOrder: Int = 0
    ) {
        self.id = UUID()
        self.name = name
        self.iconSymbol = iconSymbol
        self.colorHex = colorHex
        self.trackingTypeRaw = trackingType.rawValue
        self.goalAmount = max(1, goalAmount)
        self.reminderTime = reminderTime
        self.reminderEnabled = reminderEnabled
        self.createdAt = Date()
        self.sortOrder = sortOrder
    }

    /// Convenience accessor that maps the stored Int to/from the enum.
    var trackingType: TrackingType {
        get { TrackingType(rawValue: trackingTypeRaw) ?? .binary }
        set { trackingTypeRaw = newValue.rawValue }
    }

    /// The logged entry for a given day, if one exists.
    func entry(on day: Date) -> HabitEntry? {
        let target = Calendar.current.startOfDay(for: day)
        return entries.first { Calendar.current.isDate($0.date, inSameDayAs: target) }
    }

    /// How much was logged on a given day (0 if nothing).
    func amount(on day: Date) -> Int {
        entry(on: day)?.amount ?? 0
    }

    /// Whether the goal was met on a given day.
    func isComplete(on day: Date) -> Bool {
        amount(on: day) >= goalAmount
    }
}
