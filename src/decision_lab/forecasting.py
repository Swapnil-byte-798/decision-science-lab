"""One-week-ahead expanding-origin evaluation with separate validation and final test."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from decision_lab.common import report_dir, save_chart, write_json
from decision_lab.retail import clean_sales


def weekly_sales(sales, raw):
    first = raw.InvoiceDate.min().normalize()
    start = first + pd.Timedelta(days=(7 - first.weekday()) % 7)
    last = raw.InvoiceDate.max().normalize()
    stop = last - pd.Timedelta(days=last.weekday())
    days = pd.date_range(start, stop - pd.Timedelta(days=1), freq="D")
    daily = (
        sales.groupby(sales.InvoiceDate.dt.normalize()).revenue.sum().reindex(days, fill_value=0)
    )
    return daily.resample("W-MON", label="left", closed="left").sum()


def features(values, index):
    past = np.asarray(values[:index])
    return np.r_[past[-1], past[-2], past[-4], past[-8], past[-4:].mean(), past[-8:].mean(), index]


def predict(history, name):
    y = np.asarray(history, dtype=float)
    if len(y) < 16:
        raise ValueError("Need at least 16 prior complete weeks")
    if name == "last_week":
        return float(y[-1])
    if name == "trailing_4_week_mean":
        return float(y[-4:].mean())
    if name != "ridge_lags":
        raise ValueError("Unknown model")
    x = np.vstack([features(y, i) for i in range(8, len(y))])
    estimator = make_pipeline(StandardScaler(), Ridge(alpha=10))
    estimator.fit(x, y[8:])
    return float(max(0, estimator.predict(features(y, len(y)).reshape(1, -1))[0]))


def metrics(actual, predicted):
    a, p = np.asarray(actual), np.asarray(predicted)
    return {
        "mae_gbp": float(np.abs(a - p).mean()),
        "rmse_gbp": float(np.sqrt(np.mean((a - p) ** 2))),
        "wape": float(np.abs(a - p).sum() / np.abs(a).sum()),
    }


def run(raw, root):
    out = report_dir(root, "04_forecasting")
    sales, _ = clean_sales(raw)
    weekly = weekly_sales(sales, raw)
    if len(weekly) < 40:
        raise ValueError("Need at least 40 complete weeks")
    rows = []
    for i in range(26, len(weekly)):
        for name in ["last_week", "trailing_4_week_mean", "ridge_lags"]:
            rows.append(
                {
                    "week": str(weekly.index[i].date()),
                    "origin_index": i,
                    "model": name,
                    "split": "validation" if i < 38 else "test",
                    "actual_gbp": weekly.iloc[i],
                    "forecast_gbp": predict(weekly.iloc[:i], name),
                    "last_training_week": str(weekly.index[i - 1].date()),
                }
            )
    predictions = pd.DataFrame(rows)
    scores = pd.DataFrame(
        [
            {"split": split, "model": name, **metrics(frame.actual_gbp, frame.forecast_gbp)}
            for (split, name), frame in predictions.groupby(["split", "model"])
        ]
    )
    selected = scores[scores.split == "validation"].sort_values(["mae_gbp", "model"]).iloc[0].model
    predictions.to_csv(out / "backtest_predictions.csv", index=False)
    scores.to_csv(out / "metrics.csv", index=False)
    weekly.rename("gross_sales_gbp").to_csv(out / "weekly_sales.csv", index_label="week")
    summary = {
        "complete_weeks": len(weekly),
        "initial_train_weeks": 26,
        "validation_weeks": 12,
        "test_weeks": len(weekly) - 38,
        "horizon_weeks": 1,
        "selected_model": selected,
        "selection_metric": "validation MAE",
        "test_results": scores[scores.split == "test"].to_dict("records"),
        "note": "Expanding origins use prior actuals only. No annual seasonality or profit claim.",
    }
    write_json(out / "summary.json", summary)
    chosen = predictions[predictions.model == selected]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(
        pd.to_datetime(chosen.week),
        chosen.actual_gbp,
        color="#202d41",
        label="Observed positive sales",
    )
    ax.plot(pd.to_datetime(chosen.week), chosen.forecast_gbp, color="#166b73", label=selected)
    ax.axvline(weekly.index[38], ls="--", color="#bb743c", label="Final test begins")
    ax.set(title="One-week-ahead expanding-window revenue benchmark", ylabel="GBP")
    ax.legend()
    save_chart(fig, out / "forecast_backtest.png")
    (out / "readout.md").write_text(
        f"# Forecast benchmark\n\n{len(weekly)} complete weeks: 26 initial train, 12 validation, "
        f"{len(weekly) - 38} final test. Validation MAE selects **{selected}**.\n\n"
        "All model test scores are in metrics.csv. Each prediction uses strictly prior weeks; "
        "already observed test weeks become available at later origins. No shuffled time split or test tuning. "
        "Zero recorded sales may include closure or missing feeds. The short historical series cannot validate "
        "annual seasonality, latent demand, future performance, or business savings.\n"
    )
    return summary
