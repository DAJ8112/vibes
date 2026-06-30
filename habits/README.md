# Habit Tracker

A [HabitKit](https://apps.apple.com/us/app/habit-tracker-habitkit/id6443918070)-style habit tracker
for iOS, built with **SwiftUI** + **SwiftData**. Create habits and log each day into a
GitHub-contributions-style heatmap, with a tappable monthly calendar, streaks & stats, daily
reminders, and per-habit colors/icons.

## Features
- Multiple habits, each **done/not-done** or **count toward a daily goal**
- GitHub-style **heatmap** with month + weekday labels (Monday-first)
- Tappable **monthly calendar** to log any day (heatmap updates instantly)
- **Streaks**, longest streak, completion %, and totals
- **Daily reminders** (local notifications) per habit
- Custom **color + SF Symbol icon** per habit
- A home-screen **widget** (paid Apple Developer account required on a physical device — see below)

## Requirements
- macOS with **Xcode 26+**
- [**XcodeGen**](https://github.com/yonaskolb/XcodeGen) — `brew install xcodegen`

## Setup
The Xcode project is generated from [`project.yml`](project.yml) (not committed), so generate it first:

```bash
brew install xcodegen        # one-time
xcodegen generate            # creates HabitTracker.xcodeproj
open HabitTracker.xcodeproj  # then press ⌘R to run
```

Run the tests with **⌘U** in Xcode, or:

```bash
xcodebuild -scheme HabitTracker -destination 'platform=iOS Simulator,name=iPhone 17 Pro' test
```

## Project layout
```
HabitTracker/      # the app (Models, Views, Logic, Support)
HabitWidget/       # WidgetKit extension + shared widget UI
Tests/             # unit tests (stats logic) + a UI test
project.yml        # XcodeGen project definition (source of truth)
```

## Notes
- This build is configured to sign on a **free Apple ID** (Personal Team): the home-screen widget
  and its App Group are paid-only capabilities, so they're currently disabled for on-device builds.
  Re-enable the `HabitWidgetExtension` target + App Group in `project.yml` (and the `groupContainer`
  in `HabitTrackerApp.swift`) after enrolling in the Apple Developer Program.
- Free signing: apps stop launching after ~7 days; just re-run from Xcode to refresh.
