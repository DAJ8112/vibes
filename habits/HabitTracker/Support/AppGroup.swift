import Foundation

/// The App Group both the app and the widget use to share the SwiftData store.
/// Must match the `com.apple.security.application-groups` entitlement on BOTH
/// the app target and the widget target.
enum AppGroup {
    static let identifier = "group.com.dhruviljoshi.habittracker"
}
