"""Fixed-family, retrospective A/B/N experiment analysis."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from decision_lab.common import report_dir, save_chart, write_json
from decision_lab.data import ARMS, PRE_TREATMENT


def holm(p_values):
    p = np.asarray(p_values, dtype=float)
    if p.ndim != 1 or not len(p) or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Expected a nonempty p-value vector in [0,1]")
    order = np.argsort(p)
    result = np.empty_like(p)
    result[order] = np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)).clip(0, 1)
    return result


def sample_size(p0, absolute_mde, power=0.8, alpha=0.05):
    p1 = p0 + absolute_mde
    if not 0 < p0 < p1 < 1 or not 0 < power < 1 or not 0 < alpha < 1:
        raise ValueError("Invalid planning inputs")
    pbar = (p0 + p1) / 2
    numerator = (
        stats.norm.ppf(1 - alpha / 2) * np.sqrt(2 * pbar * (1 - pbar))
        + stats.norm.ppf(power) * np.sqrt(p0 * (1 - p0) + p1 * (1 - p1))
    ) ** 2
    return int(np.ceil(numerator / absolute_mde**2))


def compare(control, treatment, binary=False, alpha=0.05):
    a, b = np.asarray(control, dtype=float), np.asarray(treatment, dtype=float)
    if (
        a.ndim != 1
        or b.ndim != 1
        or min(len(a), len(b)) < 2
        or not np.isfinite(a).all()
        or not np.isfinite(b).all()
    ):
        raise ValueError("Need two finite 1D samples")
    if binary and (not np.isin(a, [0, 1]).all() or not np.isin(b, [0, 1]).all()):
        raise ValueError("Binary observations must be 0/1")
    delta = b.mean() - a.mean()
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va**2 / (len(a) - 1) + vb**2 / (len(b) - 1)) if se else np.inf
    if binary:
        pooled = (a.sum() + b.sum()) / (len(a) + len(b))
        null_se = np.sqrt(pooled * (1 - pooled) * (1 / len(a) + 1 / len(b)))
        p = 2 * stats.norm.sf(abs(delta / null_se)) if null_se else 1.0
        critical = stats.norm.ppf(1 - alpha / 2)
    else:
        p = 2 * stats.t.sf(abs(delta / se), df) if se else (1.0 if delta == 0 else 0.0)
        critical = stats.t.ppf(1 - alpha / 2, df)
    return {
        "n_control": len(a),
        "n_treatment": len(b),
        "control_mean": a.mean(),
        "treatment_mean": b.mean(),
        "absolute_lift": delta,
        "relative_lift": delta / a.mean() if a.mean() else None,
        "standard_error": se,
        "ci_low": delta - critical * se,
        "ci_high": delta + critical * se,
        "p_value": float(p),
    }


def run(df, root):
    out = report_dir(root, "01_experiments")
    counts = df.segment.value_counts().reindex(ARMS)
    srm = stats.chisquare(counts.to_numpy())
    rows = []
    for metric in ["conversion", "visit", "spend"]:
        for arm in ARMS[1:]:
            a, b = df.loc[df.segment == ARMS[0], metric], df.loc[df.segment == arm, metric]
            result = compare(a, b, binary=metric != "spend")
            family = compare(a, b, binary=metric != "spend", alpha=0.05 / 6)
            rows.append(
                {
                    "metric": metric,
                    "arm": arm,
                    **result,
                    "family_ci_low": family["ci_low"],
                    "family_ci_high": family["ci_high"],
                }
            )
    results = pd.DataFrame(rows)
    results["p_holm"] = holm(results.p_value)
    results.to_csv(out / "comparisons.csv", index=False)
    x = pd.get_dummies(df[PRE_TREATMENT], dtype=float)
    balance = []
    for arm in ARMS[1:]:
        a, b = x[df.segment == ARMS[0]], x[df.segment == arm]
        sd = np.sqrt((a.var() + b.var()) / 2)
        for col in x:
            balance.append(
                {
                    "arm": arm,
                    "feature": col,
                    "standardized_mean_difference": float((b[col].mean() - a[col].mean()) / sd[col])
                    if sd[col]
                    else 0.0,
                }
            )
    balance = pd.DataFrame(balance)
    balance.to_csv(out / "balance.csv", index=False)
    df.groupby("segment").agg(
        customers=("conversion", "size"),
        conversions=("conversion", "sum"),
        visitors=("visit", "sum"),
        spend=("spend", "sum"),
    ).to_csv(out / "arms.csv")
    summary = {
        "rows": len(df),
        "arm_counts": counts.to_dict(),
        "srm_p_value": float(srm.pvalue),
        "srm_pass_at_001": bool(srm.pvalue >= 0.01),
        "primary_metric": "conversion",
        "family_size": 6,
        "max_absolute_balance_smd": balance.standardized_mean_difference.abs().max(),
        "planning": {
            "baseline_conversion": 0.01,
            "absolute_mde": 0.003,
            "power": 0.8,
            "alpha_per_comparison": 0.05 / 6,
            "customers_per_arm": sample_size(0.01, 0.003, alpha=0.05 / 6),
            "note": "Illustrative prospective assumptions, not observed business targets.",
        },
    }
    write_json(out / "summary.json", summary)
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    for ax, metric in zip(axes, ["conversion", "visit", "spend"]):
        subset = results[results.metric == metric]
        scale = 1 if metric == "spend" else 100
        center = subset.absolute_lift.to_numpy() * scale
        lo, hi = subset.family_ci_low.to_numpy() * scale, subset.family_ci_high.to_numpy() * scale
        ax.errorbar(
            center,
            np.arange(2),
            xerr=[center - lo, hi - center],
            fmt="o",
            capsize=4,
            color="#166b73",
        )
        ax.axvline(0, color="gray", ls="--", lw=1)
        ax.set_yticks([0, 1], ["Mens", "Womens"])
        ax.set_title(metric.capitalize())
        ax.set_xlabel("USD per customer" if metric == "spend" else "Percentage point change")
    fig.suptitle("Email versus no email · simultaneous 95% family intervals", y=1.04)
    fig.tight_layout()
    save_chart(fig, out / "experiment_effects.png")
    text = [
        "# Campaign experiment readout",
        "",
        "Retrospective reanalysis, not a preregistered or live experiment.",
        f"\nRandomized customers: {len(df):,}. Equal-thirds SRM p-value: {srm.pvalue:.4f}.",
        "\n| Metric | Email | Absolute change | Holm p | Family interval |",
        "|---|---|---:|---:|---:|",
    ]
    for r in results.itertuples():
        scale, unit = (1, "USD") if r.metric == "spend" else (100, "pp")
        text.append(
            f"| {r.metric} | {r.arm} | {r.absolute_lift * scale:.4f} {unit} | {r.p_holm:.3g} | [{r.family_ci_low * scale:.4f}, {r.family_ci_high * scale:.4f}] |"
        )
    text += [
        "",
        "Holm adjusts six p-values; Bonferroni intervals provide conservative simultaneous coverage.",
        "Binary intervals use an unpooled large-sample normal approximation; spend uses Welch t intervals.",
        "Email-versus-control results do not establish that the two creatives differ from each other.",
        "Costs, unsubscribes, timing/exposure logs and long-term outcomes are unavailable. Revenue is not profit.",
        "SRM and measured balance cannot certify every instrumentation assumption.",
    ]
    (out / "readout.md").write_text("\n".join(text) + "\n")
    return summary
