"""Frozen-model evaluation of a budgeted causal targeting policy."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from decision_lab.common import report_dir, save_chart, write_json
from decision_lab.data import PRE_TREATMENT


def ipw_scores(y, treatment, propensity=0.5):
    y, t = np.asarray(y, dtype=float), np.asarray(treatment)
    if y.ndim != 1 or y.shape != t.shape or not np.isin(t, [0, 1]).all():
        raise ValueError("Aligned 1D outcomes and binary assignment required")
    if not 0 < propensity < 1 or not np.isfinite(y).all():
        raise ValueError("Invalid outcomes or propensity")
    return y * (t / propensity - (1 - t) / (1 - propensity))


def top_fraction(scores, fraction=0.3):
    scores = np.asarray(scores)
    if (
        scores.ndim != 1
        or not len(scores)
        or not np.isfinite(scores).all()
        or not 0 < fraction <= 1
    ):
        raise ValueError("Invalid scores or budget")
    selected = np.zeros(len(scores), dtype=int)
    selected[np.argsort(-scores, kind="stable")[: int(np.ceil(len(scores) * fraction))]] = 1
    return selected


def qini_area(y, t, predictions):
    score = ipw_scores(y, t)
    order = np.argsort(-np.asarray(predictions), kind="stable")
    x = np.arange(len(score) + 1) / len(score)
    gain = np.r_[0, np.cumsum(score[order])] / len(score)
    return float(np.trapezoid(gain - x * gain[-1], x)), x, gain


def bootstrap_mean(values, bootstrap=2000, seed=2026):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all() or bootstrap < 100:
        raise ValueError("Need finite 1D values and at least 100 replicates")
    rng = np.random.default_rng(seed)
    means = [values[rng.integers(0, len(values), len(values))].mean() for _ in range(bootstrap)]
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {"estimate": float(values.mean()), "ci_low": float(lo), "ci_high": float(hi)}


def estimate_policy(y, t, selected, bootstrap=2000, seed=2026):
    score = ipw_scores(y, t)
    selected = np.asarray(selected)
    if selected.shape != score.shape or not np.isin(selected, [0, 1]).all():
        raise ValueError("Aligned binary policy required")
    value = bootstrap_mean(score * selected, bootstrap, seed)
    value["incremental_visits_per_eligible_customer"] = value.pop("estimate")
    value["target_fraction"] = float(selected.mean())
    return value


def model(kind):
    cats = ["zip_code", "channel"]
    prep = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cats),
            ("num", StandardScaler(), [c for c in PRE_TREATMENT if c not in cats]),
        ]
    )
    estimator = (
        LogisticRegression(C=0.1, max_iter=1000)
        if kind == "logistic"
        else RandomForestClassifier(
            n_estimators=150, max_depth=6, min_samples_leaf=200, random_state=2026, n_jobs=2
        )
    )
    return make_pipeline(prep, estimator)


def fit_pair(frame, kind):
    return [
        model(kind).fit(
            frame.loc[frame.treatment == t, PRE_TREATMENT], frame.loc[frame.treatment == t, "visit"]
        )
        for t in [0, 1]
    ]


def predict_pair(pair, frame):
    return (
        pair[1].predict_proba(frame[PRE_TREATMENT])[:, 1]
        - pair[0].predict_proba(frame[PRE_TREATMENT])[:, 1]
    )


def run(df, root):
    out = report_dir(root, "02_uplift")
    frame = df[df.segment.isin(["Mens E-Mail", "No E-Mail"])].copy()
    frame["treatment"] = (frame.segment == "Mens E-Mail").astype(int)
    train, held = train_test_split(
        frame, test_size=0.4, random_state=2026, stratify=frame.treatment
    )
    validation, test = train_test_split(
        held, test_size=0.5, random_state=2027, stratify=held.treatment
    )
    candidates = []
    for kind in ["logistic", "forest"]:
        pair = fit_pair(train, kind)
        area, _, _ = qini_area(
            validation.visit, validation.treatment, predict_pair(pair, validation)
        )
        candidates.append({"model": kind, "validation_qini_area": area})
    selected = max(candidates, key=lambda r: r["validation_qini_area"])["model"]
    pair = fit_pair(pd.concat([train, validation]), selected)
    predictions = predict_pair(pair, test)
    policy = top_fraction(predictions)
    result = estimate_policy(test.visit, test.treatment, policy)
    area, x, gain = qini_area(test.visit, test.treatment, predictions)
    score = ipw_scores(test.visit, test.treatment)
    random_value = 0.3 * score.mean()
    advantage = bootstrap_mean((policy - 0.3) * score)
    summary = {
        "contrast": "Mens E-Mail versus No E-Mail",
        "outcome": "visit",
        "propensity": 0.5,
        "split_rows": {"train": len(train), "validation": len(validation), "test": len(test)},
        "features": PRE_TREATMENT,
        "candidates": candidates,
        "selected_model": selected,
        "test_qini_area": area,
        "top_30_percent": result,
        "random_30_percent_expected_incremental_visits": float(random_value),
        "paired_advantage_over_expected_random_30_percent": advantage,
        "email_everyone": estimate_policy(
            test.visit, test.treatment, np.ones(len(test), dtype=int)
        ),
        "note": "Pointwise intervals conditional on frozen model/actions, excluding training uncertainty.",
    }
    write_json(out / "summary.json", summary)
    pd.DataFrame(candidates).to_csv(out / "validation.csv", index=False)
    pd.DataFrame({"fraction_contacted": x[::100], "ipw_gain_per_eligible": gain[::100]}).to_csv(
        out / "uplift_curve.csv", index=False
    )
    pd.DataFrame(
        {"local_row": test.index, "estimated_visit_uplift": predictions, "contact": policy}
    ).to_csv(out / "customer_scores.csv", index=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(x, gain, color="#166b73", label=f"Frozen {selected} T-learner")
    ax.plot(x, x * gain[-1], ls="--", color="#bb743c", label="Expected random targeting")
    ax.set(
        xlabel="Fraction contacted",
        ylabel="Incremental visits per eligible customer",
        title="Held-out targeting curve · randomized email data",
    )
    ax.legend()
    save_chart(fig, out / "uplift_curve.png")
    (out / "readout.md").write_text(
        f"# Causal targeting readout\n\nValidation selected **{selected}**. Untouched test: {len(test):,} customers.\n\n"
        f"Top 30% value: {result['incremental_visits_per_eligible_customer']:.4f} incremental visits per eligible customer "
        f"(95% interval [{result['ci_low']:.4f}, {result['ci_high']:.4f}]).\n\n"
        f"Same expected-budget random targeting: {random_value:.4f}. Paired advantage: {advantage['estimate']:.4f} "
        f"(95% interval [{advantage['ci_low']:.4f}, {advantage['ci_high']:.4f}]).\n\n"
        "Do not infer a targeting win if the paired advantage interval includes zero. "
        "Only pretreatment features enter the model. Visit, conversion, spend and assignment are excluded. "
        "The outcome is visits, not profit; individual counterfactual truth is unobserved. "
        "Intervals exclude model-training uncertainty. No live campaign was run.\n"
    )
    return summary
