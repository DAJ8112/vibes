import SwiftUI

private extension Calendar {
    func startOfMonth(for date: Date) -> Date {
        self.date(from: dateComponents([.year, .month], from: date)) ?? startOfDay(for: date)
    }
}

/// A tappable monthly calendar for one habit. Each day shows the habit-colored
/// intensity for that date (+ a dot when anything is logged, a ring on today);
/// tapping an in-month, non-future day calls `onTapDay` to log it.
struct MonthCalendarView: View {
    let habit: Habit
    var onTapDay: (Date) -> Void

    @State private var monthAnchor: Date = Calendar.mondayFirst.startOfMonth(for: Date())

    private let calendar = Calendar.mondayFirst
    private let today = Calendar.mondayFirst.startOfDay(for: Date())
    private let weekdaySymbols = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    private var color: Color { Color(hex: habit.colorHex) }

    var body: some View {
        VStack(spacing: 12) {
            weekdayHeader
            grid
            footer
        }
    }

    private var weekdayHeader: some View {
        HStack(spacing: 4) {
            ForEach(weekdaySymbols, id: \.self) { symbol in
                Text(symbol)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity)
            }
        }
    }

    private var grid: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 4), count: 7), spacing: 6) {
            ForEach(daysForGrid(), id: \.self) { day in
                dayCell(day)
            }
        }
    }

    @ViewBuilder
    private func dayCell(_ day: Date) -> some View {
        let inMonth = calendar.isDate(day, equalTo: monthAnchor, toGranularity: .month)
        let isFuture = day > today
        let isToday = calendar.isDate(day, inSameDayAs: today)
        let amount = habit.amount(on: day)
        let level = HeatmapView.level(amount: amount, goal: habit.goalAmount)
        let opacities: [Double] = [0, 0.3, 0.5, 0.75, 1.0]

        VStack(spacing: 3) {
            Text("\(calendar.component(.day, from: day))")
                .font(.callout)
                .foregroundStyle(inMonth ? .primary : Color.secondary.opacity(0.4))
            Circle()
                .fill(amount > 0 ? color : .clear)
                .frame(width: 5, height: 5)
        }
        .frame(maxWidth: .infinity)
        .frame(height: 46)
        .background(level == 0 ? Color.clear : color.opacity(opacities[level]))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .stroke(color, lineWidth: isToday ? 2 : 0)
        )
        .opacity(inMonth ? 1 : 0.45)
        .contentShape(Rectangle())
        .onTapGesture {
            if inMonth && !isFuture { onTapDay(day) }
        }
    }

    private var footer: some View {
        HStack {
            Text(monthTitle)
                .font(.subheadline.weight(.semibold))
            Spacer()
            Button { changeMonth(by: -1) } label: {
                Image(systemName: "chevron.left").padding(8)
            }
            Button { changeMonth(by: 1) } label: {
                Image(systemName: "chevron.right").padding(8)
            }
            .disabled(isShowingCurrentMonth)
            .opacity(isShowingCurrentMonth ? 0.3 : 1)
        }
        .tint(color)
    }

    // MARK: - Helpers

    private var monthTitle: String {
        let formatter = DateFormatter()
        formatter.setLocalizedDateFormatFromTemplate("MMMM yyyy")
        return formatter.string(from: monthAnchor)
    }

    private var isShowingCurrentMonth: Bool {
        calendar.isDate(monthAnchor, equalTo: today, toGranularity: .month)
    }

    private func changeMonth(by delta: Int) {
        guard let newAnchor = calendar.date(byAdding: .month, value: delta, to: monthAnchor) else { return }
        // Don't navigate past the current month.
        if delta > 0 && newAnchor > calendar.startOfMonth(for: today) { return }
        monthAnchor = calendar.startOfMonth(for: newAnchor)
    }

    /// All day cells for the visible month, padded to full Mon–Sun weeks.
    private func daysForGrid() -> [Date] {
        let firstOfMonth = monthAnchor
        let weekdayOfFirst = calendar.component(.weekday, from: firstOfMonth)
        let leading = (weekdayOfFirst - calendar.firstWeekday + 7) % 7
        guard let start = calendar.date(byAdding: .day, value: -leading, to: firstOfMonth) else { return [] }

        let daysInMonth = calendar.range(of: .day, in: .month, for: firstOfMonth)?.count ?? 30
        let totalCells = Int((Double(leading + daysInMonth) / 7.0).rounded(.up)) * 7

        return (0..<totalCells).compactMap {
            calendar.date(byAdding: .day, value: $0, to: start).map { calendar.startOfDay(for: $0) }
        }
    }
}
