import XCTest

/// One happy-path UI test: launch with sample data and confirm the habit list shows.
final class HabitTrackerUITests: XCTestCase {

    func testLaunchShowsSeededHabits() {
        let app = XCUIApplication()
        app.launchEnvironment["SEED_SAMPLE_DATA"] = "1"
        app.launch()

        XCTAssertTrue(app.navigationBars["Habits"].waitForExistence(timeout: 5),
                      "The Habits screen should appear on launch.")
        XCTAssertTrue(app.staticTexts["Drink water"].waitForExistence(timeout: 5),
                      "A seeded habit should be listed.")
    }
}
