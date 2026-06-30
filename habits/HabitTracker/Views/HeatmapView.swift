import SwiftUI

extension Calendar {
    /// Current calendar but with weeks starting on Monday — used across the
    /// heatmap and calendar so their columns/rows line up.
    static var mondayFirst: Calendar {
        var calendar = Calendar.current
        calendar.firstWeekday = 2   // 1 = Sunday, 2 = Monday
        return calendar
    }
}

/// Anything that can drive a heatmap: a theme color, a daily goal, and a way to
/// look up how much was logged on a given day. `Habit` conforms directly; the
/// widget uses a lightweight value-type snapshot that also conforms.
protocol HeatmapSource {
    var colorHex: String { get }
    var goalAmount: Int { get }
    func amount(on day: Date) -> Int
}

extension Habit: HeatmapSource {}

/// A GitHub-contributions-style grid for one habit.
/// Columns are weeks (oldest → newest), rows are the 7 days of the week.
/// Pass an `onTap` closure to make cells interactive (logging); omit it for a
/// read-only view (e.g. the habit list row or the widget).
struct HeatmapView: View {
    let source: HeatmapSource
    var weeks: Int = 17
    var cellSize: CGFloat = 14
    var spacing: CGFloat = 3
    var onTap: ((Date) -> Void)? = nil

    private let calendar = Calendar.mondayFirst
    private let today = Calendar.mondayFirst.startOfDay(for: Date())

    var body: some View {
        let columns = HeatmapView.weekColumns(weeks: weeks, calendar: calendar, today: today)
        HStack(alignment: .top, spacing: spacing) {
            ForEach(columns.indices, id: \.self) { col in
                VStack(spacing: spacing) {
                    ForEach(columns[col], id: \.self) { date in
                        cell(for: date)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func cell(for date: Date) -> some View {
        let isFuture = date > today
        let view = DayCellView(date: date, source: source, size: cellSize, isFuture: isFuture)
        if let onTap, !isFuture {
            view.onTapGesture { onTap(date) }
        } else {
            view
        }
    }

    /// Build `weeks` columns of 7 aligned days, ending with the week containing
    /// `today`. Shared by the grid and by the labeled wrapper (so month labels
    /// line up with the exact same columns).
    static func weekColumns(weeks: Int, calendar: Calendar = .mondayFirst, today: Date) -> [[Date]] {
        let weekday = calendar.component(.weekday, from: today)
        let offset = (weekday - calendar.firstWeekday + 7) % 7
        guard
            let startOfThisWeek = calendar.date(byAdding: .day, value: -offset, to: today),
            let gridStart = calendar.date(byAdding: .day, value: -7 * (weeks - 1), to: startOfThisWeek)
        else { return [] }

        var columns: [[Date]] = []
        for col in 0..<weeks {
            var column: [Date] = []
            for row in 0..<7 {
                if let day = calendar.date(byAdding: .day, value: col * 7 + row, to: gridStart) {
                    column.append(calendar.startOfDay(for: day))
                }
            }
            columns.append(column)
        }
        return columns
    }

    /// Map a day's logged amount to an intensity level 0...4 (0 = nothing).
    static func level(amount: Int, goal: Int) -> Int {
        guard amount > 0 else { return 0 }
        let ratio = Double(amount) / Double(max(1, goal))
        if ratio >= 1 { return 4 }
        return min(4, max(1, Int(ceil(ratio * 4))))
    }
}

/// A single day square in the heatmap.
struct DayCellView: View {
    let date: Date
    let source: HeatmapSource
    var size: CGFloat = 14
    var isFuture: Bool = false

    var body: some View {
        RoundedRectangle(cornerRadius: size * 0.25, style: .continuous)
            .fill(fillColor)
            .frame(width: size, height: size)
    }

    private var fillColor: Color {
        if isFuture { return .clear }
        let level = HeatmapView.level(amount: source.amount(on: date), goal: source.goalAmount)
        if level == 0 { return Color.secondary.opacity(0.12) }
        let opacities: [Double] = [0, 0.3, 0.5, 0.75, 1.0]
        return Color(hex: source.colorHex).opacity(opacities[level])
    }
}

/// Small "Less □□□□ More" legend shown under the full heatmap.
struct HeatmapLegend: View {
    let colorHex: String

    var body: some View {
        HStack(spacing: 4) {
            Text("Less").font(.caption2).foregroundStyle(.secondary)
            ForEach([0.12, 0.3, 0.5, 0.75, 1.0], id: \.self) { opacity in
                RoundedRectangle(cornerRadius: 2, style: .continuous)
                    .fill(opacity == 0.12
                          ? Color.secondary.opacity(0.12)
                          : Color(hex: colorHex).opacity(opacity))
                    .frame(width: 12, height: 12)
            }
            Text("More").font(.caption2).foregroundStyle(.secondary)
        }
    }
}
