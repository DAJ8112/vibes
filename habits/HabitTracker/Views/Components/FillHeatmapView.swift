import SwiftUI

/// A compact, read-only heatmap that fills the full width of its container using
/// pure layout — each cell is a square that flexes to divide the available width
/// evenly. No width measurement, so it renders identically on every device.
/// Used in the habit list rows.
struct FillHeatmapView: View {
    let source: HeatmapSource
    var weeks: Int = 22
    var spacing: CGFloat = 3
    var cornerRadius: CGFloat = 3

    private let calendar = Calendar.mondayFirst
    private let today = Calendar.mondayFirst.startOfDay(for: Date())

    var body: some View {
        let columns = HeatmapView.weekColumns(weeks: weeks, calendar: calendar, today: today)
        HStack(spacing: spacing) {
            ForEach(columns.indices, id: \.self) { col in
                VStack(spacing: spacing) {
                    ForEach(columns[col], id: \.self) { date in
                        RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                            .fill(fill(for: date))
                            .aspectRatio(1, contentMode: .fit)   // square; flexes to fill width
                    }
                }
            }
        }
    }

    private func fill(for date: Date) -> Color {
        if date > today { return .clear }
        let level = HeatmapView.level(amount: source.amount(on: date), goal: source.goalAmount)
        if level == 0 { return Color.secondary.opacity(0.12) }
        let opacities: [Double] = [0, 0.3, 0.5, 0.75, 1.0]
        return Color(hex: source.colorHex).opacity(opacities[level])
    }
}
