"""
generate_charts.py - Generate evaluation charts from full_metrics.json for SmellScope.

Writes four PNG files to output/:
  overall_results.png      - grouped bar chart: precision/recall/F1 per mode
  recall_by_severity.png   - line chart: recall across tiers per mode
  precision_by_severity.png - line chart: precision across tiers per mode
  f1_by_smell.png           - grouped bar chart: F1 per smell type per mode
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

BASE = Path(__file__).parent.parent
DATA_PATH = BASE / "output" / "full_metrics.json"
OUTPUT_DIR = BASE / "output"

MODES = ("oracle", "llm", "judge")
MODE_LABELS = ("Mode 1\nOracle", "Mode 2\nLLM", "Mode 3\nJudge")
TIERS = ("low", "medium", "high")
TIER_LABELS = ("Low", "Medium", "High")

MODE_COLORS = {
    "oracle": "#2D6A9F",
    "llm":    "#2AAE74",
    "judge":  "#E07B39",
}

METRIC_COLORS = {
    "precision": "#2D6A9F",
    "recall":    "#2AAE74",
    "f1":        "#E07B39",
}

SMELL_LABELS = {
    "circular_import":          "circular\nimport",
    "god_module":               "god\nmodule",
    "layer_boundary_violation": "layer\nviolation",
    "long_method":              "long\nmethod",
    "poor_naming":              "poor\nnaming",
}


def _bar_label(ax, bars, fmt="{:.2f}", offset=0.012):
    """Draw value labels centered above each bar."""
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + offset,
            fmt.format(h),
            ha="center",
            va="bottom",
            fontsize=8,
            color="#333333",
        )


def _clean_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.1f}"))
    ax.tick_params(left=False)
    ax.grid(False)


# Chart 1: overall results
def chart_overall(data: dict) -> None:
    overall = data["overall"]
    metrics = ["precision", "recall", "f1"]
    metric_labels = ["Precision", "Recall", "F1"]

    n_modes = len(MODES)
    n_metrics = len(metrics)
    group_width = 0.7
    bar_w = group_width / n_metrics
    offsets = np.arange(n_metrics) * bar_w - group_width / 2 + bar_w / 2

    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.arange(n_modes)
    for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
        vals = [overall[m][metric] or 0.0 for m in MODES]
        bars = ax.bar(
            x + offsets[i],
            vals,
            width=bar_w * 0.9,
            color=METRIC_COLORS[metric],
            label=label,
            zorder=3,
        )
        _bar_label(ax, bars)

    ax.set_xticks(x)
    ax.set_xticklabels(MODE_LABELS, fontsize=10)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score", fontsize=10)
    ax.set_title("Overall Precision, Recall, and F1 by Detection Mode", fontsize=12, pad=12)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    _clean_axes(ax)

    fig.tight_layout()
    out = OUTPUT_DIR / "overall_results.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[charts] Saved -> {out}")


# Chart 2: recall by severity tier
def chart_recall_by_severity(data: dict) -> None:
    by_tier = data["by_tier"]
    x = np.arange(len(TIERS))

    fig, ax = plt.subplots(figsize=(7, 5))

    for mode, label, marker in zip(
        MODES,
        ("Mode 1 Oracle", "Mode 2 LLM", "Mode 3 Judge"),
        ("o", "s", "^"),
    ):
        vals = [by_tier[mode][t]["recall"] if by_tier[mode][t] else 0.0 for t in TIERS]
        color = MODE_COLORS[mode]
        ax.plot(
            x, vals,
            marker=marker,
            color=color,
            linewidth=2,
            markersize=8,
            label=label,
            zorder=3,
        )
        for xi, v in zip(x, vals):
            ax.text(
                xi,
                v + 0.025,
                f"{v:.2f}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                color=color,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(TIER_LABELS, fontsize=10)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Recall", fontsize=10)
    ax.set_title("Recall Across Severity Tiers by Detection Mode", fontsize=12, pad=12)
    ax.legend(frameon=False, fontsize=9)
    _clean_axes(ax)

    fig.tight_layout()
    out = OUTPUT_DIR / "recall_by_severity.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[charts] Saved -> {out}")


# Chart 3: precision by severity tier
def chart_precision_by_severity(data: dict) -> None:
    by_tier = data["by_tier"]
    x = np.arange(len(TIERS))

    fig, ax = plt.subplots(figsize=(7, 5))

    for mode, label, marker in zip(
        MODES,
        ("Mode 1 Oracle", "Mode 2 LLM", "Mode 3 Judge"),
        ("o", "s", "^"),
    ):
        vals = [by_tier[mode][t]["precision"] if by_tier[mode][t] else 0.0 for t in TIERS]
        color = MODE_COLORS[mode]
        ax.plot(
            x, vals,
            marker=marker,
            color=color,
            linewidth=2,
            markersize=8,
            label=label,
            zorder=3,
        )
        for xi, v in zip(x, vals):
            ax.text(
                xi,
                v + 0.025,
                f"{v:.2f}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                color=color,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(TIER_LABELS, fontsize=10)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Precision", fontsize=10)
    ax.set_title("Precision Across Severity Tiers by Detection Mode", fontsize=12, pad=12)
    ax.legend(frameon=False, fontsize=9)
    _clean_axes(ax)

    fig.tight_layout()
    out = OUTPUT_DIR / "precision_by_severity.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[charts] Saved -> {out}")


# Chart 4: F1 score by smell type
def chart_f1_by_smell(data: dict) -> None:
    by_smell = data["by_smell"]
    smell_types = data["smell_types"]

    n_smells = len(smell_types)
    n_modes = len(MODES)
    group_width = 0.72
    bar_w = group_width / n_modes
    offsets = np.arange(n_modes) * bar_w - group_width / 2 + bar_w / 2

    fig, ax = plt.subplots(figsize=(10, 5))

    x = np.arange(n_smells)
    mode_labels_flat = ("Mode 1 Oracle", "Mode 2 LLM", "Mode 3 Judge")
    for i, (mode, label) in enumerate(zip(MODES, mode_labels_flat)):
        vals = [by_smell[mode][s]["f1"] or 0.0 for s in smell_types]
        bars = ax.bar(
            x + offsets[i],
            vals,
            width=bar_w * 0.88,
            color=MODE_COLORS[mode],
            label=label,
            zorder=3,
        )
        _bar_label(ax, bars)

    ax.set_xticks(x)
    ax.set_xticklabels([SMELL_LABELS[s] for s in smell_types], fontsize=9)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("F1 Score", fontsize=10)
    ax.set_title("F1 Score by Smell Type and Detection Mode", fontsize=12, pad=12)
    ax.legend(frameon=False, fontsize=9)
    _clean_axes(ax)

    fig.tight_layout()
    out = OUTPUT_DIR / "f1_by_smell.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[charts] Saved -> {out}")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(exist_ok=True)
    chart_overall(data)
    chart_recall_by_severity(data)
    chart_precision_by_severity(data)
    chart_f1_by_smell(data)


if __name__ == "__main__":
    main()
