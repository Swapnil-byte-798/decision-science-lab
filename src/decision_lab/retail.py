"""Sequential positive-sales audit and order-grain SQL business metrics."""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from decision_lab.common import report_dir, save_chart, write_json


def clean_sales(raw):
    frame = raw.copy()
    audit = [{"step": "raw", "rows": len(frame), "removed": 0}]
    rules = [
        ("remove_exact_duplicates", lambda x: ~x.duplicated()),
        ("exclude_cancellation_invoices", lambda x: ~x.InvoiceNo.str.upper().str.startswith("C")),
        ("require_positive_quantity", lambda x: x.Quantity > 0),
        ("require_positive_price", lambda x: x.UnitPrice > 0),
    ]
    for name, keep in rules:
        before = len(frame)
        frame = frame.loc[keep(frame)].copy()
        audit.append({"step": name, "rows": len(frame), "removed": before - len(frame)})
    frame["revenue"] = frame.Quantity * frame.UnitPrice
    return frame, pd.DataFrame(audit)


def complete_month_cutoff(raw):
    # Conservatively exclude the final observed month, which is partial in this source.
    return raw.InvoiceDate.max().to_period("M").start_time


def orders_table(sales, cutoff):
    frame = sales[sales.InvoiceDate < cutoff].copy()
    frame["customer_id"] = frame.CustomerID.astype("Int64").astype("string")
    if (frame.groupby("InvoiceNo").customer_id.nunique(dropna=False) > 1).any():
        raise ValueError("Conflicting customer_id within invoice")
    # The real extract contains same-invoice timestamps differing by a minute.
    invoice_day = frame.InvoiceDate.dt.normalize().groupby(frame.InvoiceNo).nunique()
    if (invoice_day > 1).any():
        raise ValueError("Conflicting invoice day")
    orders = frame.groupby("InvoiceNo", as_index=False).agg(
        invoice_date=("InvoiceDate", "min"),
        customer_id=("customer_id", "first"),
        revenue=("revenue", "sum"),
    )
    orders = orders.rename(columns={"InvoiceNo": "invoice_no"})
    orders.invoice_date = orders.invoice_date.dt.strftime("%Y-%m-%d %H:%M:%S")
    return orders


def sql_reports(orders, cutoff, db_path=":memory:"):
    sql_dir = Path(__file__).parent / "sql"
    with sqlite3.connect(db_path) as conn:
        orders.to_sql("orders", conn, index=False, if_exists="replace")
        conn.execute("CREATE INDEX IF NOT EXISTS customer_date ON orders(customer_id,invoice_date)")
        first = pd.Timestamp(orders.invoice_date.min()).to_period("M")
        last = (cutoff - pd.Timedelta(days=1)).to_period("M")
        pd.DataFrame({"month": pd.period_range(first, last, freq="M").astype(str)}).to_sql(
            "months", conn, index=False, if_exists="replace"
        )
        return {
            name: pd.read_sql_query(
                (sql_dir / f"{name}.sql").read_text(),
                conn,
                params={"asof": cutoff.strftime("%Y-%m-%d")},
            )
            for name in ["cohorts", "monthly", "rfm"]
        }


def run(raw, root):
    out = report_dir(root, "03_customer_analytics")
    sales, audit = clean_sales(raw)
    cutoff = complete_month_cutoff(raw)
    orders = orders_table(sales, cutoff)
    db = root / "data/processed/retail.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    tables = sql_reports(orders, cutoff, db)
    for name, frame in tables.items():
        frame.to_csv(out / f"{name}.csv", index=False)
    audit.to_csv(out / "cleaning_audit.csv", index=False)
    summary = {
        "raw_rows": len(raw),
        "positive_sales_rows": len(sales),
        "positive_sales_rows_missing_customer": int(sales.CustomerID.isna().sum()),
        "complete_month_orders": len(orders),
        "identified_customers": len(tables["rfm"]),
        "analysis_asof_exclusive": str(cutoff.date()),
        "gross_sales_gbp_complete_months": float(orders.revenue.sum()),
        "note": "Positive gross sales exclude returns; cohort is first observed purchase, not verified acquisition.",
    }
    write_json(out / "summary.json", summary)
    pivot = tables["cohorts"].pivot(
        index="cohort", columns="month_age", values="repeat_purchase_rate"
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(pivot.to_numpy(), vmin=0, vmax=1, cmap="YlGnBu", aspect="auto")
    ax.set_yticks(range(len(pivot)), pivot.index)
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set(
        xlabel="Months after first observed purchase",
        ylabel="Observed cohort",
        title="Monthly repeat purchase · blanks are not yet observable",
    )
    fig.colorbar(im, ax=ax, label="Share of original cohort purchasing")
    save_chart(fig, out / "cohort_retention.png")
    (out / "readout.md").write_text(
        f"# SQL customer analytics\n\n{len(raw):,} original rows → {len(sales):,} positive-sale lines. "
        f"Complete months end before {cutoff.date()}: {len(orders):,} orders and {len(tables['rfm']):,} identified customers.\n\n"
        "Gross sales include anonymous purchases; cohorts and RFM require known IDs. Returns are excluded, "
        "so sales are not net revenue or profit. Future cohort cells remain missing; observed zero-repeat cells are zero. "
        "Earliest invoice timestamp handles real minute-varying line times. RFM uses illustrative fixed thresholds. "
        "Customer-level RFM exports remain local. Associations do not establish causality.\n"
    )
    return summary
