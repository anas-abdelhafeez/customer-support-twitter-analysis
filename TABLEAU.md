# Build the Tableau workbook

The `.hyper` file and the CSVs in `extracts/` are ready for Tableau Desktop or Tableau Public. No data prep is needed.

## Connect
1. Tableau: Connect > More > **Tableau Extract (.hyper)** > `extracts/support_extracts.hyper`.
   (Or Connect > Text file for any CSV.)
2. The extract holds six tables: `brand_summary`, `daily_volume`, `hour_weekday`, `frt_buckets`, `frt_by_hour`, `brand_hour`. They are independent summary tables, so build one sheet per table. No joins are required.

## Sheets that match the HTML dashboard
| Sheet | Table | Build |
| --- | --- | --- |
| Daily volume | `daily_volume` | Day (continuous) on Columns, SUM(conversations) on Rows, area chart |
| Heatmap | `hour_weekday` | hour on Columns, weekday on Rows (sort by dow), SUM(conversations) on Color, square mark |
| FRT distribution | `frt_buckets` | bucket on Columns, SUM(conversations) on Rows |
| Brand speed | `brand_summary` | answered_conversations on Columns (log axis), median_frt_min on Rows, brand on Label |
| Wait by hour | `frt_by_hour` | hour on Columns, median_frt_min and p90_frt_min on Rows (dual line) |
| Brand x hour | `brand_hour` | hour on Columns, brand on Rows, median_frt_min on Color |

## Colors
Use a dark background (`#0F1426`) with accents `#6C8CFF`, `#27D3A2`, `#FFB454`, `#FF6B8B`, `#B07CFF`, matching the HTML dashboard.

## Parameters worth adding
- **SLA minutes** (default 60): calculated field `IF [median_frt_min] <= [SLA minutes] THEN "On target" ELSE "Late" END` on the brand sheet.

## Publish
Tableau Public: File > Save to Tableau Public. Extracts under the Tableau Public size limit publish as-is (this one is about 130 KB).

## Note
The workbook itself (`.twbx`) is not in this repo. It is built in Tableau Desktop from these extracts. The `.hyper` is created by `analysis.py` using the `pantab` library.
