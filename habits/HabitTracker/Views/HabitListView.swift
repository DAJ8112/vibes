import SwiftUI
import SwiftData
import WidgetKit

/// Home screen: a list of all habits.
struct HabitListView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: \Habit.sortOrder) private var habits: [Habit]
    @State private var showingAdd = false
    @State private var showingWidgetPreview = false
    @State private var showingSettings = false
    @State private var path: [Habit] = []

    var body: some View {
        NavigationStack(path: $path) {
            Group {
                if habits.isEmpty {
                    ContentUnavailableView(
                        "No habits yet",
                        systemImage: "square.grid.3x3.fill",
                        description: Text("Tap + to add your first habit.")
                    )
                } else {
                    List {
                        ForEach(habits) { habit in
                            // A plain Button (not NavigationLink) so there's no
                            // disclosure chevron; the whole card is tappable.
                            Button {
                                path.append(habit)
                            } label: {
                                HabitRowView(habit: habit)
                            }
                            .buttonStyle(.plain)
                            // Each habit is its own card: a rounded surface on a
                            // clear row, with no separators and a gap between rows.
                            .padding()
                            .background(Color(.secondarySystemBackground))
                            .clipShape(RoundedRectangle(cornerRadius: 16))
                            .listRowSeparator(.hidden)
                            .listRowBackground(Color.clear)
                            .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
                        }
                        .onDelete(perform: deleteHabits)
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Habits")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Menu {
                        Button {
                            showingWidgetPreview = true
                        } label: {
                            Label("Widget preview", systemImage: "rectangle.3.group")
                        }
                        Button {
                            showingSettings = true
                        } label: {
                            Label("Settings", systemImage: "gearshape")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showingAdd = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .navigationDestination(for: Habit.self) { habit in
                HabitDetailView(habit: habit)
            }
            .sheet(isPresented: $showingAdd) {
                AddEditHabitView(habit: nil)
            }
            .sheet(isPresented: $showingWidgetPreview) {
                WidgetPreviewView()
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView()
            }
        }
        .onAppear(perform: maybeAutoOpen)
        .onChange(of: habits.map(\.id)) { _, _ in maybeAutoOpen() }
    }

    /// Dev-only: jump straight to the first habit's detail when launched with
    /// OPEN_FIRST_HABIT=1 (used for screenshots). No-op in normal use.
    private func maybeAutoOpen() {
        let env = ProcessInfo.processInfo.environment
        if env["OPEN_ADD"] == "1" { showingAdd = true }
        if env["WIDGET_PREVIEW"] == "1" { showingWidgetPreview = true }
        guard env["OPEN_FIRST_HABIT"] == "1",
              path.isEmpty, let first = habits.first else { return }
        path = [first]
    }

    private func deleteHabits(_ offsets: IndexSet) {
        for index in offsets {
            let habit = habits[index]
            NotificationManager.cancel(id: habit.id)
            context.delete(habit)
        }
        WidgetCenter.shared.reloadAllTimelines()
    }
}

/// A single row in the habit list.
struct HabitRowView: View {
    let habit: Habit

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 12) {
                ZStack {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(Color(hex: habit.colorHex).opacity(0.2))
                        .frame(width: 40, height: 40)
                    Image(systemName: habit.iconSymbol)
                        .foregroundStyle(Color(hex: habit.colorHex))
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text(habit.name)
                        .font(.headline)
                    Text(habit.trackingType == .count ? "Goal: \(habit.goalAmount)/day" : "Daily")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer(minLength: 0)
            }
            // Read-only recent heatmap that fills the full card width (flexible
            // square cells — no measurement, so it fills on every device).
            FillHeatmapView(source: habit, weeks: 22)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 4)
    }
}

#Preview {
    HabitListView()
        .modelContainer(for: [Habit.self, HabitEntry.self], inMemory: true)
}
