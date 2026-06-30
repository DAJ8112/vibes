import Foundation
import UserNotifications

/// Schedules per-habit daily local notifications. Each habit's reminder is keyed
/// by its UUID so we can update or cancel it independently.
///
/// We pass plain values (not the SwiftData `Habit` object) so this code is safe
/// to run off the main actor.
enum NotificationManager {

    static func identifier(for id: UUID) -> String {
        "habit-reminder-\(id.uuidString)"
    }

    /// Ask the user for permission to send notifications (no-op if already decided).
    @discardableResult
    static func requestAuthorization() async -> Bool {
        do {
            return try await UNUserNotificationCenter.current()
                .requestAuthorization(options: [.alert, .sound, .badge])
        } catch {
            return false
        }
    }

    /// Create or replace a habit's daily reminder. If `enabled` is false (or no
    /// time is given), any existing reminder is removed.
    static func reschedule(id: UUID, title: String, enabled: Bool, time: Date?) async {
        let center = UNUserNotificationCenter.current()
        let identifier = identifier(for: id)

        // Always clear the old one first.
        center.removePendingNotificationRequests(withIdentifiers: [identifier])

        guard enabled, let time else { return }
        guard await requestAuthorization() else { return }

        let content = UNMutableNotificationContent()
        content.title = title.isEmpty ? "Habit reminder" : title
        content.body = "Time to log your habit."
        content.sound = .default

        let components = Calendar.current.dateComponents([.hour, .minute], from: time)
        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: true)
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)

        try? await center.add(request)
    }

    static func cancel(id: UUID) {
        UNUserNotificationCenter.current()
            .removePendingNotificationRequests(withIdentifiers: [identifier(for: id)])
    }
}
