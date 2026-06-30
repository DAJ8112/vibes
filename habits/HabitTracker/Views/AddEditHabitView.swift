import SwiftUI
import SwiftData
import WidgetKit

/// Create a new habit (when `habit == nil`) or edit an existing one.
struct AddEditHabitView: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    @Query(sort: \Habit.sortOrder) private var allHabits: [Habit]

    let habit: Habit?

    @State private var name: String = ""
    @State private var trackingType: TrackingType = .binary
    @State private var goalAmount: Int = 1
    @State private var colorHex: String = HabitTheme.colors.first ?? "#66BB6A"
    @State private var iconSymbol: String = HabitTheme.icons.first ?? "star.fill"
    @State private var reminderEnabled: Bool = false
    @State private var reminderTime: Date =
        Calendar.current.date(bySettingHour: 9, minute: 0, second: 0, of: Date()) ?? Date()

    private var isEditing: Bool { habit != nil }

    var body: some View {
        NavigationStack {
            Form {
                Section("Name") {
                    TextField("e.g. Drink water", text: $name)
                }

                Section("Tracking") {
                    Picker("Type", selection: $trackingType) {
                        ForEach(TrackingType.allCases) { type in
                            Text(type.label).tag(type)
                        }
                    }
                    if trackingType == .count {
                        Stepper("Daily goal: \(goalAmount)", value: $goalAmount, in: 1...100)
                    }
                }

                Section("Reminder") {
                    Toggle("Daily reminder", isOn: $reminderEnabled)
                    if reminderEnabled {
                        DatePicker("Time", selection: $reminderTime, displayedComponents: .hourAndMinute)
                    }
                }

                Section("Color") {
                    colorPicker
                }

                Section("Icon") {
                    iconPicker
                }
            }
            .navigationTitle(isEditing ? "Edit Habit" : "New Habit")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { save() }
                        .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .onAppear {
                load()
                // Dev-only: show the reminder controls expanded for screenshots.
                if ProcessInfo.processInfo.environment["OPEN_ADD"] == "1" {
                    reminderEnabled = true
                }
            }
        }
    }

    private var colorPicker: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(HabitTheme.colors, id: \.self) { hex in
                    Circle()
                        .fill(Color(hex: hex))
                        .frame(width: 34, height: 34)
                        .overlay(
                            Circle().stroke(Color.primary, lineWidth: colorHex == hex ? 3 : 0)
                        )
                        .onTapGesture { colorHex = hex }
                }
            }
            .padding(.vertical, 4)
        }
    }

    private var iconPicker: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 6), spacing: 12) {
            ForEach(HabitTheme.icons, id: \.self) { symbol in
                Image(systemName: symbol)
                    .font(.title3)
                    .frame(width: 42, height: 42)
                    .background(
                        iconSymbol == symbol
                            ? Color(hex: colorHex).opacity(0.25)
                            : Color.secondary.opacity(0.1)
                    )
                    .foregroundStyle(iconSymbol == symbol ? Color(hex: colorHex) : .primary)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .onTapGesture { iconSymbol = symbol }
            }
        }
        .padding(.vertical, 4)
    }

    private func load() {
        guard let habit else { return }
        name = habit.name
        trackingType = habit.trackingType
        goalAmount = habit.goalAmount
        colorHex = habit.colorHex
        iconSymbol = habit.iconSymbol
        reminderEnabled = habit.reminderEnabled
        if let time = habit.reminderTime { reminderTime = time }
    }

    private func save() {
        let trimmed = name.trimmingCharacters(in: .whitespaces)
        let goal = trackingType == .count ? goalAmount : 1

        let savedID: UUID
        if let habit {
            habit.name = trimmed
            habit.trackingType = trackingType
            habit.goalAmount = goal
            habit.colorHex = colorHex
            habit.iconSymbol = iconSymbol
            habit.reminderEnabled = reminderEnabled
            habit.reminderTime = reminderTime
            savedID = habit.id
        } else {
            let nextOrder = (allHabits.map(\.sortOrder).max() ?? -1) + 1
            let newHabit = Habit(
                name: trimmed,
                iconSymbol: iconSymbol,
                colorHex: colorHex,
                trackingType: trackingType,
                goalAmount: goal,
                reminderTime: reminderTime,
                reminderEnabled: reminderEnabled,
                sortOrder: nextOrder
            )
            context.insert(newHabit)
            savedID = newHabit.id
        }

        // Schedule/cancel the daily reminder for this habit.
        let enabled = reminderEnabled
        let time = reminderTime
        Task {
            await NotificationManager.reschedule(id: savedID, title: trimmed, enabled: enabled, time: time)
        }
        WidgetCenter.shared.reloadAllTimelines()

        dismiss()
    }
}

#Preview {
    AddEditHabitView(habit: nil)
        .modelContainer(for: [Habit.self, HabitEntry.self], inMemory: true)
}
