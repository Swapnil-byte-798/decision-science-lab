"""Download and verify real sources; never generate substitute analysis data."""

import hashlib
from zipfile import ZipFile

import numpy as np
import pandas as pd
import requests

from decision_lab.common import write_json

DATASETS = {
    "hillstrom": {
        "filename": "hillstrom.csv.gz",
        "url": "https://hillstorm1.s3.us-east-2.amazonaws.com/hillstorm_no_indices.csv.gz",
        "sha256": "bab6578f60db5d792f1c2372c502f029152a5249cf5ea84390f3b7f885d7234f",
        "rows": 64000,
    },
    "retail": {
        "filename": "online_retail.zip",
        "url": "https://archive.ics.uci.edu/static/public/352/online+retail.zip",
        "sha256": "f5385cbb54bbebf7196389109c6b0621faab0c304e3702548165e71c84aede8b",
        "rows": 541909,
    },
}
ARMS = ("No E-Mail", "Mens E-Mail", "Womens E-Mail")
PRE_TREATMENT = ["recency", "history", "mens", "womens", "zip_code", "newbie", "channel"]


def verify_file(path, expected):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"Checksum mismatch for {path.name}: {actual}")


def download(root, names=None):
    raw = root / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    for name in DATASETS if names is None else names:
        meta = DATASETS[name]
        path = raw / meta["filename"]
        if not path.exists():
            temp = path.with_suffix(path.suffix + ".part")
            try:
                with requests.get(meta["url"], stream=True, timeout=(15, 120)) as response:
                    response.raise_for_status()
                    with temp.open("wb") as handle:
                        for chunk in response.iter_content(1024 * 1024):
                            handle.write(chunk)
                verify_file(temp, meta["sha256"])
                temp.replace(path)
            finally:
                temp.unlink(missing_ok=True)
        verify_file(path, meta["sha256"])
        print(f"Verified {name}", flush=True)
    out = root / "reports"
    out.mkdir(exist_ok=True)
    write_json(out / "data-provenance.json", DATASETS)


def validate_hillstrom(df):
    required = PRE_TREATMENT + ["segment", "visit", "conversion", "spend"]
    if not set(required).issubset(df.columns) or df[required].isna().any().any():
        raise ValueError("Missing Hillstrom columns or values")
    if set(df.segment.unique()) != set(ARMS):
        raise ValueError("Expected three randomized arms")
    for col in ["visit", "conversion", "mens", "womens", "newbie"]:
        if not df[col].isin([0, 1]).all():
            raise ValueError(f"Invalid binary column {col}")
    if not np.isfinite(df[["recency", "history", "spend"]].to_numpy()).all():
        raise ValueError("Nonfinite numeric data")
    if (df[["history", "spend"]] < 0).any().any() or (df.conversion > df.visit).any():
        raise ValueError("Invalid outcome or prior history")
    if ((df.spend > 0).astype(int) != df.conversion).any():
        raise ValueError("Spend/conversion inconsistency")


def load_hillstrom(root):
    meta = DATASETS["hillstrom"]
    path = root / "data/raw" / meta["filename"]
    verify_file(path, meta["sha256"])
    df = pd.read_csv(path)
    if len(df) != meta["rows"]:
        raise ValueError("Unexpected Hillstrom row count")
    validate_hillstrom(df)
    return df


def load_retail(root):
    meta = DATASETS["retail"]
    path = root / "data/raw" / meta["filename"]
    verify_file(path, meta["sha256"])
    cache = root / "data/processed/retail.pkl"
    if cache.exists():
        return pd.read_pickle(cache)  # Locally generated cache only; never load untrusted pickle.
    with ZipFile(path) as archive, archive.open("Online Retail.xlsx") as file:
        df = pd.read_excel(file, dtype={"InvoiceNo": str, "StockCode": str}, engine="openpyxl")
    if len(df) != meta["rows"]:
        raise ValueError("Unexpected retail row count")
    required = ["InvoiceNo", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
    if not set(required).issubset(df.columns):
        raise ValueError("Unexpected retail schema")
    df.InvoiceDate = pd.to_datetime(df.InvoiceDate, errors="raise")
    if df[["InvoiceNo", "Quantity", "InvoiceDate", "UnitPrice"]].isna().any().any():
        raise ValueError("Missing invoice/date/quantity/price")
    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(cache)
    return df
