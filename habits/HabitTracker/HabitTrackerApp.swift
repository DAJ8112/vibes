import SwiftUI
import SwiftData

@main
struct HabitTrackerApp: App {
    // User's chosen appearance (System/Light/Dark). Applied app-wide below.
    @AppStorage(AppAppearance.storageKey) private var appearanceRaw = AppAppearance.system.rawValue

    var body: some Scene {
        WindowGroup {
            HabitListView()
                .task {
                    // Dev-only: populate sample data when launched with the
                    // SEED_SAMPLE_DATA flag. No-op in normal use.
                    SampleData.seedIfNeeded(sharedModelContainer.mainContext)
                }
                // Force the chosen scheme app-wide (incl. sheets). `nil` for
                // System, which falls back to the iOS appearance.
                .preferredColorScheme(AppAppearance(rawValue: appearanceRaw)?.colorScheme)
        }
        // Sets up the on-device database (SwiftData) for our two models.
        // SwiftData creates/loads the store automatically and injects a
        // `modelContext` into the SwiftUI environment for all child views.
        .modelContainer(sharedModelContainer)
    }

    /// The app's SwiftData container. Uses the default on-device store.
    ///
    /// (The App Group container — which let a home-screen widget share this data
    /// — is a paid-only capability, so it's disabled for free-Apple-ID device
    /// builds. Re-add `groupContainer: .identifier(AppGroup.identifier)` here when
    /// you restore the widget on a paid account.)
    let sharedModelContainer: ModelContainer = {
        let schema = Schema([Habit.self, HabitEntry.self])
        let config = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: false
        )
        do {
            return try ModelContainer(for: schema, configurations: [config])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()
}
