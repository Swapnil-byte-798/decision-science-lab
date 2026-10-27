from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from decision_lab.data import DATASETS, load_hillstrom, load_retail
from decision_lab.forecasting import features, predict, weekly_sales
from decision_lab.retail import clean_sales, complete_month_cutoff, orders_table, sql_reports

ROOT = Path(__file__).resolve().parents[1]


def invoices():
    return pd.DataFrame(
        [
            ["1", "2011-01-01 12:00", 1, 2, 5],
            ["1", "2011-01-01 12:01", 1, 3, 5],
            ["2", "2011-02-01 12:00", 1, 1, 7],
            ["3", "2011-02-03 12:00", 2, 2, 8],
            ["4", "2011-03-04 12:00", 3, 3, 9],
        ],
        columns=["InvoiceNo", "InvoiceDate", "CustomerID", "Quantity", "UnitPrice"],
    ).assign(InvoiceDate=lambda d: pd.to_datetime(d.InvoiceDate))


def test_cleaning_sequential_counts_reconcile():
    raw = invoices()
    raw = pd.concat(
        [
            raw,
            raw.iloc[[0]],
            raw.iloc[[0]].assign(InvoiceNo="C1", Quantity=-1),
            raw.iloc[[0]].assign(InvoiceNo="5", UnitPrice=0),
        ],
        ignore_index=True,
    )
    clean, audit = clean_sales(raw)
    assert len(raw) == len(clean) + audit.removed.sum()
    assert len(clean) == 5


def test_invoice_minute_variation_is_one_order_and_revenue_reconciles():
    clean, _ = clean_sales(invoices())
    orders = orders_table(clean, pd.Timestamp("2011-04-01"))
    assert len(orders) == 4
    assert orders.revenue.sum() == clean.revenue.sum()
    assert orders.iloc[0].invoice_date == "2011-01-01 12:00:00"


def test_mixed_customers_within_invoice_rejected():
    raw = invoices()
    raw.loc[1, "CustomerID"] = 2
    clean, _ = clean_sales(raw)
    with pytest.raises(ValueError):
        orders_table(clean, pd.Timestamp("2011-04-01"))


def test_cross_day_invoice_rejected():
    raw = invoices()
    raw.loc[1, "InvoiceDate"] = pd.Timestamp("2011-01-02 12:00")
    clean, _ = clean_sales(raw)
    with pytest.raises(ValueError):
        orders_table(clean, pd.Timestamp("2011-04-01"))


def test_cohorts_observed_zero_is_zero_future_is_missing():
    clean, _ = clean_sales(invoices())
    cutoff = pd.Timestamp("2011-04-01")
    cohort = sql_reports(orders_table(clean, cutoff), cutoff)["cohorts"]
    assert (
        cohort[
            (cohort.cohort == "2011-01") & (cohort.month == "2011-03")
        ].repeat_purchase_rate.iloc[0]
        == 0
    )
    assert not (cohort.month > "2011-03").any()
    assert (cohort[cohort.month_age == 0].repeat_purchase_rate == 1).all()


def test_future_changes_do_not_change_forecast_features():
    values = np.arange(60, dtype=float)
    before = features(values, 30)
    values[30:] = 1e9
    np.testing.assert_array_equal(before, features(values, 30))


def test_forecast_baseline_and_short_history_guard():
    assert predict(np.arange(20), "last_week") == 19
    assert predict(np.arange(20), "trailing_4_week_mean") == 17.5
    with pytest.raises(ValueError):
        predict([1, 2], "ridge_lags")


@pytest.mark.integration
def test_real_data_contracts_and_all_rows():
    if not all((ROOT / "data/raw" / meta["filename"]).exists() for meta in DATASETS.values()):
        pytest.skip("Download the real sources first")
    email, raw = load_hillstrom(ROOT), load_retail(ROOT)
    assert len(email) == 64000 and len(raw) == 541909
    clean, audit = clean_sales(raw)
    assert len(clean) + audit.removed.sum() == len(raw)
    cutoff = complete_month_cutoff(raw)
    orders = orders_table(clean, cutoff)
    assert pd.to_datetime(orders.invoice_date).max() < cutoff
    weekly = weekly_sales(clean, raw)
    assert (weekly.index.dayofweek == 0).all()
    assert weekly.index[0] > raw.InvoiceDate.min()
