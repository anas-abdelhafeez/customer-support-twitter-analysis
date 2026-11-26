# Build the Tableau workbook

**Live on Tableau Public:** https://public.tableau.com/app/profile/anas.mahmoud7907/viz/CustomerSupportonTwitter-ResponseTimeAnalysis/Dashboard1

It was built in the browser with Tableau Public web authoring (no desktop install), from the files in `extracts/`.

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

## Build it in the browser (Tableau Public web authoring)
1. Sign in at public.tableau.com, then Create > **Web Authoring**.
2. Connect to Data > Files > Upload from computer. Upload one extract (for example `extracts/brand_summary.csv`). Use New Data Source (the cylinder icon) to add the next CSV. Each CSV is its own data source, so no joins are needed.
3. Sheet 1: drag `brand_summary` Median Frt Min to Columns and Brand to Rows. Sort descending, put Answered Conversations on Color.
4. Sheet 2: from `daily_volume`, drag Conversations to Rows and Day to Columns. Open the Day pill menu and choose the discrete Day (May 8, 2015 style) so you get one point per day.
5. Sheet 3: from `frt_by_hour`, drag Median Frt Min to Rows and Hour to Columns. Right-click the Hour pill and choose Dimension.
6. New Dashboard: drag the three sheets in.
7. Publish As... > name the workbook > Publish. The dashboard opens at a public.tableau.com profile URL.

Limits of the browser editor: no custom dark theme, fewer formatting controls than Desktop, and web authoring publishes only to Tableau Public (the workbook is public by design).

## Note
The `.hyper` is created by `analysis.py` using the `pantab` library. The workbook lives on Tableau Public (link above); a downloadable `.twbx` can be exported from there if needed.
