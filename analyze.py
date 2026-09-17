#!/usr/bin/env python3
"""Onboarding A/B experiment analysis.

Reproduces every number in ANSWERS.md / answers.json and writes the
figures used in the writeup.

Usage:
    python analyze.py --csv path/to/experiment_results.csv
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


Z95 = 1.959963984540054


def two_prop_diff_ci(p_t: float, n_t: int, p_c: float, n_c: int):
    """Unpooled SE, 95% CI, z-stat, two-sided normal p-value for p_t - p_c."""
    se = math.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    diff = p_t - p_c
    z = diff / se if se > 0 else float("nan")
    p = float(2 * (1 - stats.norm.cdf(abs(z)))) if se > 0 else float("nan")
    return se, diff - Z95 * se, diff + Z95 * se, z, p


def load_and_validate(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    expected_cols = ["user_id", "segment", "variant", "converted"]
    if list(df.columns) != expected_cols:
        raise ValueError(f"Unexpected columns: {list(df.columns)}")

    issues = []
    if df.isnull().any().any():
        issues.append(f"missing values:\n{df.isnull().sum()}")
    if df["user_id"].duplicated().any():
        issues.append(f"duplicate user_id count: {int(df['user_id'].duplicated().sum())}")
    extra_seg = set(df["segment"].unique()) - {"organic", "paid_search", "referral", "app_store", "influencer"}
    extra_var = set(df["variant"].unique()) - {"control", "treatment"}
    extra_conv = set(df["converted"].unique()) - {0, 1}
    if extra_seg:
        issues.append(f"unexpected segments: {extra_seg}")
    if extra_var:
        issues.append(f"unexpected variants: {extra_var}")
    if extra_conv:
        issues.append(f"unexpected converted values: {extra_conv}")
    if issues:
        raise ValueError("Data validation failed:\n" + "\n".join(issues))
    return df


def compute(df: pd.DataFrame) -> dict:
    n_total = len(df)
    n_c = int((df.variant == "control").sum())
    n_t = int((df.variant == "treatment").sum())
    conv_c = int(df.loc[df.variant == "control", "converted"].sum())
    conv_t = int(df.loc[df.variant == "treatment", "converted"].sum())
    cr_c = conv_c / n_c
    cr_t = conv_t / n_t
    naive_lift = cr_t - cr_c
    se_o, lo_o, hi_o, z_o, p_o = two_prop_diff_ci(cr_t, n_t, cr_c, n_c)

    segments = []
    mix = 0.0
    for seg in ["app_store", "influencer", "organic", "paid_search", "referral"]:
        sub = df[df.segment == seg]
        c = sub[sub.variant == "control"]
        t = sub[sub.variant == "treatment"]
        nc, nt = int(len(c)), int(len(t))
        cc, ct = int(c.converted.sum()), int(t.converted.sum())
        pc, pt = cc / nc, ct / nt
        lift = pt - pc
        se, lo, hi, z, p = two_prop_diff_ci(pt, nt, pc, nc)
        n_seg = nc + nt
        share = n_seg / n_total
        contrib = share * lift
        mix += contrib
        segments.append(
            {
                "segment": seg,
                "n": n_seg,
                "n_control": nc,
                "n_treatment": nt,
                "conv_control": cc,
                "conv_treatment": ct,
                "cr_control": pc,
                "cr_treatment": pt,
                "lift": lift,
                "se": se,
                "ci_low": lo,
                "ci_high": hi,
                "z": z,
                "pval": p,
                "share": share,
                "contrib": contrib,
                "ctrl_share": nc / n_seg,
                "treat_share": nt / n_seg,
            }
        )

    tab = pd.crosstab(df.segment, df.variant)
    chi2, chi_p, dof, _ = stats.chi2_contingency(tab)

    return {
        "n_total": n_total,
        "n_control": n_c,
        "n_treatment": n_t,
        "conv_control": conv_c,
        "conv_treatment": conv_t,
        "cr_control": cr_c,
        "cr_treatment": cr_t,
        "naive_lift": naive_lift,
        "naive_se": se_o,
        "naive_ci_low": lo_o,
        "naive_ci_high": hi_o,
        "naive_z": z_o,
        "naive_p": p_o,
        "mix_adjusted_lift": mix,
        "segments": segments,
        "assignment_chi2": float(chi2),
        "assignment_chi2_p": float(chi_p),
        "assignment_dof": int(dof),
    }


def _style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.titlesize": 13,
            "axes.labelsize": 11,
        }
    )


CTRL = "#5B6B7A"
TREAT = "#2F6FED"
POS = "#2A9D6A"
NEG = "#C44B4B"


def plot_overall(res: dict, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    rates = [res["cr_control"] * 100, res["cr_treatment"] * 100]
    bars = ax.bar(["Control", "Treatment"], rates, color=[CTRL, TREAT], width=0.55, zorder=3)
    for bar, rate, n, conv in zip(
        bars,
        rates,
        [res["n_control"], res["n_treatment"]],
        [res["conv_control"], res["conv_treatment"]],
    ):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.45,
            f"{rate:.2f}%\n({conv:,} / {n:,})",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    ax.set_ylabel("Conversion rate")
    ax.set_title("Overall conversion: control vs treatment (naive)")
    ax.set_ylim(0, 32)
    ax.annotate(
        f"Naive lift = +{res['naive_lift']*100:.2f} pp",
        xy=(0.5, 0.92),
        xycoords="axes fraction",
        ha="center",
        fontsize=10,
        color="#333",
    )
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def plot_segment_crs(res: dict, out: Path) -> None:
    segs = res["segments"]
    labels = [s["segment"] for s in segs]
    x = np.arange(len(labels))
    w = 0.38
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    b1 = ax.bar(x - w / 2, [s["cr_control"] * 100 for s in segs], w, label="Control", color=CTRL, zorder=3)
    b2 = ax.bar(x + w / 2, [s["cr_treatment"] * 100 for s in segs], w, label="Treatment", color=TREAT, zorder=3)
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.4, f"{h:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Conversion rate")
    ax.set_title("Conversion rate by acquisition segment")
    ax.legend(frameon=False)
    ax.set_ylim(0, 42)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def plot_lifts(res: dict, out: Path) -> None:
    segs = res["segments"]
    labels = [s["segment"] for s in segs]
    lifts = [s["lift"] * 100 for s in segs]
    lows = [s["ci_low"] * 100 for s in segs]
    highs = [s["ci_high"] * 100 for s in segs]
    colors = [POS if v >= 0 else NEG for v in lifts]
    yerr = np.vstack([np.array(lifts) - np.array(lows), np.array(highs) - np.array(lifts)])
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    x = np.arange(len(labels))
    ax.bar(x, lifts, color=colors, width=0.62, zorder=3, yerr=yerr, capsize=4, ecolor="#444", error_kw={"linewidth": 1})
    ax.axhline(0, color="#222", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Lift (percentage points)")
    ax.set_title("Treatment - control lift by segment (95% CI)")
    for i, v in enumerate(lifts):
        offset = 0.55 if v >= 0 else -0.9
        ax.text(i, v + offset, f"{v:+.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def plot_allocation(res: dict, out: Path) -> None:
    segs = res["segments"]
    labels = [s["segment"] for s in segs]
    ctrl = [s["ctrl_share"] * 100 for s in segs]
    treat = [s["treat_share"] * 100 for s in segs]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    ax.bar(x, ctrl, 0.62, label="Control", color=CTRL, zorder=3)
    ax.bar(x, treat, 0.62, bottom=ctrl, label="Treatment", color=TREAT, zorder=3)
    ax.axhline(50, color="#888", linewidth=1, linestyle=":")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Share of segment")
    ax.set_title("Variant assignment mix within each segment")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, loc="upper right")
    for i, (c, t) in enumerate(zip(ctrl, treat)):
        ax.text(i, c / 2, f"{c:.0f}%", ha="center", va="center", color="white", fontsize=9)
        ax.text(i, c + t / 2, f"{t:.0f}%", ha="center", va="center", color="white", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def plot_contrib(res: dict, out: Path) -> None:
    segs = res["segments"]
    labels = [s["segment"] for s in segs]
    vals = [s["contrib"] * 100 for s in segs]
    colors = [POS if v >= 0 else NEG for v in vals]
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    x = np.arange(len(labels))
    ax.bar(x, vals, color=colors, width=0.62, zorder=3)
    ax.axhline(0, color="#222", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Contribution (percentage points)")
    ax.set_title("Each segment's contribution to the mix-adjusted lift")
    for i, v in enumerate(vals):
        ax.text(i, v + (0.04 if v >= 0 else -0.06), f"{v:+.3f}", ha="center", fontsize=9)
    ax.annotate(
        f"Sum = {res['mix_adjusted_lift']*100:.2f} pp",
        xy=(0.98, 0.95),
        xycoords="axes fraction",
        ha="right",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def write_answers_json(res: dict, path: Path) -> None:
    payload = {
        "q1_naive_lift_pp": round(res["naive_lift"] * 100, 4),
        "q1_n_control": res["n_control"],
        "q1_n_treatment": res["n_treatment"],
        "q2_untrustworthy_segment": "influencer",
        "q3_mix_adjusted_lift_pp": round(res["mix_adjusted_lift"] * 100, 2),
        "q4_real_effect_segment": "app_store",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default=str(Path(__file__).resolve().parent / "data" / "experiment_results.csv"),
        help="Path to experiment_results.csv",
    )
    parser.add_argument(
        "--outdir",
        default=str(Path(__file__).resolve().parent),
        help="Directory to write figures/ and answers.json",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    outdir = Path(args.outdir)
    figdir = outdir / "figures"
    figdir.mkdir(parents=True, exist_ok=True)

    df = load_and_validate(csv_path)
    res = compute(df)

    print(f"rows={res['n_total']} control={res['n_control']} treatment={res['n_treatment']}")
    print(f"naive lift = {res['naive_lift']*100:.4f} pp")
    print(f"mix-adjusted lift = {res['mix_adjusted_lift']*100:.4f} pp")
    for s in res["segments"]:
        print(
            f"{s['segment']:12} n={s['n']:5} "
            f"CR {s['cr_control']*100:6.2f}/{s['cr_treatment']*100:6.2f} "
            f"lift={s['lift']*100:+7.2f} pp  "
            f"CI[{s['ci_low']*100:+6.2f},{s['ci_high']*100:+6.2f}]  "
            f"p={s['pval']:.3g}"
        )

    _style()
    plot_overall(res, figdir / "01_overall_conversion.png")
    plot_segment_crs(res, figdir / "02_segment_conversion.png")
    plot_lifts(res, figdir / "03_segment_lift.png")
    plot_allocation(res, figdir / "04_segment_allocation.png")
    plot_contrib(res, figdir / "05_mix_adjusted_contribution.png")

    write_answers_json(res, outdir / "answers.json")
    print(f"wrote figures to {figdir}")
    print(f"wrote {outdir / 'answers.json'}")


if __name__ == "__main__":
    main()
