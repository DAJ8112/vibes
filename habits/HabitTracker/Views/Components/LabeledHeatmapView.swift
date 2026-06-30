import SwiftUI

/// The heatmap overview with month labels across the top and weekday labels down
/// the left, so each 7-cell column reads clearly as one Mon–Sun week.
/// Pass `onTap` to make cells interactive (logging); omit it for a read-only view.
struct LabeledHeatmapView: View {
    let source: HeatmapSource
    var weeks: Int = 26
    var cellSize: CGFloat = 13
    var spacing: CGFloat = 3
    var onTap: ((Date) -> Void)? = nil

    private let calendar = Calendar.mondayFirst
    private let today = Calendar.mondayFirst.startOfDay(for: Date())
    private let monthRowHeight: CGFloat = 16
    private let weekdayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    private struct MonthLabel: Identifiable {
        let id = UUID()
        let col: Int
        let name: String
    }

    private var columns: [[Date]] {
        HeatmapView.weekColumns(weeks: weeks, calendar: calendar, today: today)
    }

    private var gridWidth: CGFloat {
        CGFloat(weeks) * cellSize + CGFloat(weeks - 1) * spacing
    }

    var body: some View {
        HStack(alignment: .top, spacing: 6) {
            weekdayLabels
            ScrollView(.horizontal, showsIndicators: false) {
                VStack(alignment: .leading, spacing: spacing) {
                    monthLabels
                    HeatmapView(source: source, weeks: weeks, cellSize: cellSize, spacing: spacing, onTap: onTap)
                }
            }
            .defaultScrollAnchor(.trailing)   // start on the most recent weeks
        }
    }

    /// Fixed left column: labels every other row (Tue/Thu/Sat), aligned to cells.
    private var weekdayLabels: some View {
        VStack(alignment: .trailing, spacing: spacing) {
            Color.clear.frame(width: 1, height: monthRowHeight)   // aligns with the month row
            ForEach(0..<7, id: \.self) { row in
                Text(row % 2 == 1 ? weekdayNames[row] : "")
                    .font(.system(size: 9))
                    .foregroundStyle(.secondary)
                    .frame(height: cellSize)
            }
        }
    }

    /// Month labels positioned by the column where each month starts.
    private var monthLabels: some View {
        ZStack(alignment: .topLeading) {
            ForEach(monthBoundaries) { label in
                Text(label.name)
                    .font(.system(size: 10))
                    .foregroundStyle(.secondary)
                    .offset(x: CGFloat(label.col) * (cellSize + spacing))
            }
        }
        .frame(width: gridWidth, height: monthRowHeight, alignment: .topLeading)
    }

    private var monthBoundaries: [MonthLabel] {
        let formatter = DateFormatter()
        formatter.setLocalizedDateFormatFromTemplate("MMM")
        var result: [MonthLabel] = []
        var lastMonth = -1
        for (index, column) in columns.enumerated() {
            guard let firstDay = column.first else { continue }
            let month = calendar.component(.month, from: firstDay)
            if month != lastMonth {
                result.append(MonthLabel(col: index, name: formatter.string(from: firstDay)))
                lastMonth = month
            }
        }
        return result
    }
}
