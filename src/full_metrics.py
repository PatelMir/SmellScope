"""
full_metrics.py - Comprehensive per-mode metrics for SmellScope.

Computes TP, FP, FN, Precision, Recall, F1 for Modes 1 (oracle), 2 (llm),
and 3 (judge) at four aggregation levels: per smell type, per severity tier,
overall, and per-repo coarse recall. Writes output/full_metrics.json.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import REPO_CONFIGS, SEVERITY_TIERS, SMELL_TYPES

SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots"
RESULTS_DIR = Path(__file__).parent.parent / "output"

COARSE_SMELLS = frozenset({"circular_import", "god_module", "layer_boundary_violation"})
FINE_SMELLS = frozenset({"long_method", "poor_naming"})
ALL_REPOS = list(REPO_CONFIGS.keys())
MODES = ("oracle", "llm", "judge")


# Data loading
def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _injected_types(injection_log: dict | None) -> frozenset:
    if not injection_log:
        return frozenset()
    return frozenset(e["smell_type"] for e in injection_log.get("injections", []))


def _oracle_detected(oracle: dict | None) -> frozenset:
    if not oracle:
        return frozenset()
    findings = (
        oracle.get("pylint", {}).get("smell_relevant", [])
        + oracle.get("flake8", {}).get("smell_relevant", [])
    )
    return frozenset(e["smell_type"] for e in findings if e.get("smell_type"))


def _llm_detected(llm: dict | None) -> frozenset:
    if not llm:
        return frozenset()
    return frozenset(e["smell_type"] for e in llm.get("detected_smells", []) if e.get("smell_type"))


def _judge_detected(judge: dict | None) -> frozenset:
    if not judge:
        return frozenset()
    return frozenset(e["smell_type"] for e in judge.get("validated", []) if e.get("smell_type"))


def _load_snapshot(repo: str, tier: str) -> dict:
    d = SNAPSHOTS_DIR / repo / tier
    inj = _load_json(d / "injection_log.json")
    return {
        "repo": repo,
        "tier": tier,
        "injected": _injected_types(inj),
        "oracle": _oracle_detected(_load_json(d / "oracle_results.json")),
        "llm": _llm_detected(_load_json(d / "llm_results.json")),
        "judge": _judge_detected(_load_json(d / "judge_results.json")),
    }


# Metrics computation
def _metrics(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall) else None
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4) if f1 is not None else None,
    }


def _accumulate(detected: frozenset, injected: frozenset, restrict: frozenset | None = None):
    """Return (tp, fp, fn) for one snapshot, optionally restricted to a smell subset."""
    if restrict is not None:
        detected = detected & restrict
        injected = injected & restrict
    tp = len(detected & injected)
    fp = len(detected - injected)
    fn = len(injected - detected)
    return tp, fp, fn


def compute_overall(snapshots: list, mode: str) -> dict:
    tp = fp = fn = 0
    for s in snapshots:
        if not s["injected"]:
            continue
        a, b, c = _accumulate(s[mode], s["injected"])
        tp += a; fp += b; fn += c
    return _metrics(tp, fp, fn)


def compute_by_smell(snapshots: list, mode: str) -> dict:
    """One row per smell type, micro-aggregated across all non-baseline snapshots."""
    results = {}
    for smell in SMELL_TYPES:
        tp = fp = fn = 0
        for s in snapshots:
            if not s["injected"]:
                continue
            injected_here = smell in s["injected"]
            detected_here = smell in s[mode]
            if injected_here and detected_here:
                tp += 1
            elif injected_here:
                fn += 1
            elif detected_here:
                fp += 1
        results[smell] = _metrics(tp, fp, fn)
    return results


def compute_by_tier(snapshots: list, mode: str) -> dict:
    results = {}
    for tier in SEVERITY_TIERS:
        if tier == "none":
            results[tier] = None
            continue
        tp = fp = fn = 0
        for s in snapshots:
            if s["tier"] != tier:
                continue
            a, b, c = _accumulate(s[mode], s["injected"])
            tp += a; fp += b; fn += c
        results[tier] = _metrics(tp, fp, fn)
    return results


def compute_per_repo_coarse(snapshots: list, mode: str) -> dict:
    """Coarse-smell TP/FP/FN/precision/recall/F1 per repo (non-baseline tiers only)."""
    results = {}
    for repo in ALL_REPOS:
        tp = fp = fn = 0
        for s in snapshots:
            if s["repo"] != repo or s["tier"] == "none":
                continue
            a, b, c = _accumulate(s[mode], s["injected"], restrict=COARSE_SMELLS)
            tp += a; fp += b; fn += c
        results[repo] = _metrics(tp, fp, fn)
    return results


# Table printing
def _pf(val: float | None, pct: bool = True) -> str:
    if val is None:
        return "  N/A  "
    if pct:
        return f"{val * 100:5.1f}%"
    return f"{val:5d}"


def print_tables(full: dict) -> None:
    modes_label = {"oracle": "Mode 1 Oracle", "llm": "Mode 2 LLM", "judge": "Mode 3 Judge"}

    # Overall
    print("\n=== OVERALL (all non-baseline snapshots) ===")
    print(f"{'Mode':<16} {'TP':>4} {'FP':>4} {'FN':>4}  {'Precision':>10} {'Recall':>8} {'F1':>8}")
    print("-" * 60)
    for m in MODES:
        r = full["overall"][m]
        print(
            f"{modes_label[m]:<16} {r['tp']:>4} {r['fp']:>4} {r['fn']:>4}"
            f"  {_pf(r['precision']):>10} {_pf(r['recall']):>8} {_pf(r['f1']):>8}"
        )

    # By smell type
    print("\n=== PER SMELL TYPE (non-baseline, micro-aggregated) ===")
    header = f"{'Smell Type':<28}"
    for m in MODES:
        header += f"  {'P':>6} {'R':>6} {'F1':>6}"
    print(header)
    print("-" * (28 + 3 * 22))
    for smell in SMELL_TYPES:
        row = f"{smell:<28}"
        for m in MODES:
            r = full["by_smell"][m][smell]
            row += f"  {_pf(r['precision']):>6} {_pf(r['recall']):>6} {_pf(r['f1']):>6}"
        print(row)

    # By tier
    print("\n=== PER SEVERITY TIER (micro-aggregated across repos and smells) ===")
    header = f"{'Tier':<10}"
    for m in MODES:
        header += f"  {'P':>6} {'R':>6} {'F1':>6}"
    print(header)
    print("-" * (10 + 3 * 22))
    for tier in SEVERITY_TIERS:
        row = f"{tier:<10}"
        for m in MODES:
            r = full["by_tier"][m][tier]
            if r is None:
                row += "  " + " " * 20
            else:
                row += f"  {_pf(r['precision']):>6} {_pf(r['recall']):>6} {_pf(r['f1']):>6}"
        print(row)

    # Per-repo coarse recall
    print("\n=== PER-REPO COARSE RECALL (circular_import, god_module, layer_boundary_violation) ===")
    header = f"{'Repo':<36}"
    for m in MODES:
        header += f"  {'Recall':>8} {'Prec':>6}"
    print(header)
    print("-" * (36 + 3 * 18))
    for repo in ALL_REPOS:
        row = f"{repo:<36}"
        for m in MODES:
            r = full["per_repo_coarse"][m][repo]
            row += f"  {_pf(r['recall']):>8} {_pf(r['precision']):>6}"
        print(row)
    print()


# Main
def main() -> None:
    print(f"[metrics] Loading snapshots for {len(ALL_REPOS)} repos x {len(SEVERITY_TIERS)} tiers...", file=sys.stderr)

    snapshots = [
        _load_snapshot(repo, tier)
        for repo in ALL_REPOS
        for tier in SEVERITY_TIERS
    ]

    full = {
        "repos": ALL_REPOS,
        "tiers": SEVERITY_TIERS,
        "smell_types": SMELL_TYPES,
        "overall": {m: compute_overall(snapshots, m) for m in MODES},
        "by_smell": {m: compute_by_smell(snapshots, m) for m in MODES},
        "by_tier": {m: compute_by_tier(snapshots, m) for m in MODES},
        "per_repo_coarse": {m: compute_per_repo_coarse(snapshots, m) for m in MODES},
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "full_metrics.json"
    out_path.write_text(json.dumps(full, indent=2), encoding="utf-8")
    print(f"[metrics] Saved -> {out_path}", file=sys.stderr)

    print_tables(full)


if __name__ == "__main__":
    main()
