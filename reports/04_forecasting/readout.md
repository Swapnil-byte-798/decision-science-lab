# Forecast benchmark

52 complete weeks: 26 initial train, 12 validation, 14 final test. Validation MAE selects **trailing_4_week_mean**.

All model test scores are in metrics.csv. Each prediction uses strictly prior weeks; already observed test weeks become available at later origins. No shuffled time split or test tuning. Zero recorded sales may include closure or missing feeds. The short historical series cannot validate annual seasonality, latent demand, future performance, or business savings.
