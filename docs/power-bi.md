# Optional Power BI report

Import the aggregate CSVs with Get Data → Text/CSV. No JavaScript, HTML or CSS is required.
This is a report design guide, not an executed Power BI Desktop validation or a supplied PBIX.

| Page | Inputs | Useful visuals |
|---|---|---|
| Experiment | comparisons.csv, arms.csv | Arm/metric filters, lift and adjusted-p-value table |
| Customers | cohorts.csv, monthly.csv | Cohort matrix, monthly sales and average-order trends |
| Forecasts | metrics.csv, backtest_predictions.csv | Actual/forecast line, validation/test filter, model WAPE |
| StockSense comparison | examples/policy-comparison.json in existing repo | Profit and fill intervals, failed guardrail |

Do not sum rates or average subgroup rates without denominators. Keep future cohort cells
blank, distinguish percentage points from relative percentages, and keep monetary units
visible. Customer-level RFM and targeting score files remain local.
