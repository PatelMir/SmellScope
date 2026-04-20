"""
reporter.py - Metrics computation and report generation for SmellScope.

Reads injection_log.json, oracle_results.json, and llm_results.json for all
repos/tiers, computes precision/recall/F1, and writes smellscope_report.json
and smellscope_report.md to the output/ directory.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import SEVERITY_TIERS, SMELL_TYPES


def _load_json(path: Path) -> dict | None:
    """Load and return a JSON file, or None if missing/invalid."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[reporter] WARNING: could not load {path}: {exc}", file=sys.stderr)
        return None


def _load_tier_data(snapshots_dir: Path, repo_name: str, severity: str) -> dict:
    """Load all result files for one repo/tier combination."""
    tier_dir = snapshots_dir / repo_name / severity
    return {
        "injection_log": _load_json(tier_dir / "injection_log.json"),
        "oracle": _load_json(tier_dir / "oracle_results.json"),
        "llm": _load_json(tier_dir / "llm_results.json"),
        "judge": _load_json(tier_dir / "judge_results.json"),
    }


def _injected_smell_types(injection_log: dict) -> list:
    """Return the list of injected smell_type strings from an injection log."""
    if not injection_log:
        return []
    return [entry["smell_type"] for entry in injection_log.get("injections", [])]


def _count_by_smell(smell_entries: list) -> dict:
    """Return a dict counting occurrences of each smell_type in a findings list."""
    counts = {s: 0 for s in SMELL_TYPES}
    for entry in smell_entries:
        st = entry.get("smell_type")
        if st and st in counts:
            counts[st] += 1
    return counts


def _compute_metrics(detected_types: list, injected_types: list) -> dict:
    """
    Compute precision, recall, and F1 given detected and injected smell type lists.

    Each injected_types entry is one ground-truth positive instance.
    """
    if not injected_types:
        return {
            "precision": None,
            "recall": None,
            "f1": None,
            "notes": "baseline tier, no injections",
        }

    injected_set = set(injected_types)
    detected_set = set(detected_types)

    tp = len(detected_set & injected_set)
    fp = len(detected_set - injected_set)
    fn = len(injected_set - detected_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall) else None

    notes = f"{fp} pre-existing smell type(s) counted as FP" if fp > 0 else ""

    return {
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4) if f1 is not None else None,
        "notes": notes,
    }


def _build_oracle_tier(oracle: dict | None, injection_log: dict | None) -> dict:
    """Build oracle metrics for one repo/tier."""
    injected = _injected_smell_types(injection_log)

    if oracle is None:
        return {
            "total_smell_relevant": 0,
            "by_smell": {s: 0 for s in SMELL_TYPES},
            "injected_types": injected,
            "precision": None,
            "recall": None,
            "f1": None,
            "notes": "oracle_results.json missing",
        }

    all_smell = (
        oracle.get("pylint", {}).get("smell_relevant", [])
        + oracle.get("flake8", {}).get("smell_relevant", [])
    )
    by_smell = _count_by_smell(all_smell)
    detected_types = list({e["smell_type"] for e in all_smell if e.get("smell_type")})
    metrics = _compute_metrics(detected_types, injected)

    return {
        "total_smell_relevant": len(all_smell),
        "by_smell": by_smell,
        "injected_types": injected,
        **metrics,
    }


def _build_llm_tier(llm: dict | None, injection_log: dict | None) -> dict:
    """Build LLM metrics for one repo/tier."""
    injected = _injected_smell_types(injection_log)

    if llm is None:
        return {
            "total_detected": 0,
            "by_smell": {s: 0 for s in SMELL_TYPES},
            "injected_types": injected,
            "precision": None,
            "recall": None,
            "f1": None,
            "parse_error": False,
            "notes": "llm_results.json missing",
        }

    detected_smells = llm.get("detected_smells", [])
    by_smell = _count_by_smell(detected_smells)
    detected_types = list({e["smell_type"] for e in detected_smells if e.get("smell_type")})
    metrics = _compute_metrics(detected_types, injected)

    return {
        "total_detected": len(detected_smells),
        "by_smell": by_smell,
        "injected_types": injected,
        "parse_error": llm.get("parse_error", False),
        **metrics,
    }


def _build_judge_tier(judge: dict | None, injection_log: dict | None) -> dict:
    """Build LLM judge (Mode 3) metrics for one repo/tier."""
    injected = _injected_smell_types(injection_log)

    if judge is None:
        return {
            "total_validated": 0,
            "by_smell": {s: 0 for s in SMELL_TYPES},
            "injected_types": injected,
            "precision": None,
            "recall": None,
            "f1": None,
            "notes": "judge_results.json missing",
        }

    validated = judge.get("validated", [])
    by_smell = _count_by_smell(validated)
    detected_types = list({e["smell_type"] for e in validated if e.get("smell_type")})
    metrics = _compute_metrics(detected_types, injected)

    return {
        "total_validated": len(validated),
        "by_smell": by_smell,
        "injected_types": injected,
        **metrics,
    }


_COARSE_SMELLS = {"circular_import", "god_module", "layer_boundary_violation"}
_FINE_SMELLS = {"long_method", "poor_naming"}


def _build_rq_summaries(repo_results: list) -> dict:
    """Build RQ1/RQ2/RQ3 summary dicts from all repo tier records."""
    all_tiers_by_severity: dict = {t: [] for t in SEVERITY_TIERS}
    for repo in repo_results:
        for tier in repo["tiers"]:
            all_tiers_by_severity[tier["severity"]].append(tier)

    def avg_recall(tool_key: str, tiers: list) -> float | None:
        vals = [t[tool_key]["recall"] for t in tiers if t[tool_key].get("recall") is not None]
        return round(sum(vals) / len(vals) * 100, 1) if vals else None

    def category_avg_recall(tool_key: str, tiers: list, category: set) -> float | None:
        recalls = []
        for t in tiers:
            injected_in_cat = set(t[tool_key].get("injected_types", [])) & category
            if not injected_in_cat:
                continue
            detected_in_cat = {s for s in injected_in_cat if t[tool_key]["by_smell"].get(s, 0) > 0}
            recalls.append(len(detected_in_cat) / len(injected_in_cat))
        return round(sum(recalls) / len(recalls) * 100, 1) if recalls else None

    non_none = [t for tiers in all_tiers_by_severity.values() for t in tiers if t["severity"] != "none"]
    oracle_coarse = avg_recall("oracle", non_none)
    llm_coarse = avg_recall("llm", non_none)
    gap = round(oracle_coarse - llm_coarse, 1) if (oracle_coarse and llm_coarse) else None

    def avg_precision(tool_key: str, tiers: list) -> float | None:
        vals = [t[tool_key]["precision"] for t in tiers if t[tool_key].get("precision") is not None]
        return round(sum(vals) / len(vals) * 100, 1) if vals else None

    judge_coarse_recall = avg_recall("judge", non_none)
    judge_coarse_precision = avg_precision("judge", non_none)

    by_tier = {
        sv: None if sv == "none" else avg_recall("llm", tiers)
        for sv, tiers in all_tiers_by_severity.items()
    }

    return {
        "RQ1": {
            "description": (
                "LLM vs oracle on coarse-grained smells "
                "(circular_import, god_module, layer_boundary_violation)"
            ),
            "oracle_coarse_recall": oracle_coarse,
            "llm_coarse_recall": llm_coarse,
            "gap": gap,
            "judge_coarse_recall": judge_coarse_recall,
            "judge_coarse_precision": judge_coarse_precision,
        },
        "RQ2": {
            "description": "LLM fine-grained vs coarse-grained detection",
            "llm_coarse_recall": category_avg_recall("llm", non_none, _COARSE_SMELLS),
            "llm_fine_recall": category_avg_recall("llm", non_none, _FINE_SMELLS),
        },
        "RQ3": {
            "description": "LLM recall by severity tier",
            "by_tier": by_tier,
        },
    }


def _pct(val: float | None) -> str:
    """Format a recall value as a percentage string."""
    if val is None:
        return "N/A"
    if isinstance(val, float) and val <= 1.0:
        return f"{val * 100:.1f}%"
    return f"{val}%"


def _build_markdown(report: dict) -> str:
    """Render the smellscope_report.md from the JSON report dict."""
    ts = report["generated_at"]
    rqs = report["rq_summary"]
    r1 = rqs["RQ1"]
    r2 = rqs["RQ2"]
    r3 = rqs["RQ3"]

    oracle_r = _pct(r1["oracle_coarse_recall"])
    llm_r = _pct(r1["llm_coarse_recall"])
    gap_str = f"{r1['gap']}%" if r1["gap"] is not None else "N/A"
    judge_r = _pct(r1.get("judge_coarse_recall"))
    judge_p = _pct(r1.get("judge_coarse_precision"))

    lines = [
        "# SmellScope: Preliminary Results Report",
        "",
        "## Overview",
        "SmellScope evaluates LLM awareness of architectural smells in Python codebases by "
        "injecting smells at four severity levels and comparing detection rates between "
        "Gemini 3 Flash Preview and static analysis oracles (Pylint + Flake8).",
        "",
        "**Repos evaluated:** cookiecutter, click, flask-hexagonal  ",
        "**Tiers evaluated:** None, Low, Medium, High  ",
        f"**Generated:** {ts}",
        "",
        "---",
        "",
        "## RQ1: LLM vs Oracle -- Coarse-Grained Smell Detection",
        "",
        f"Across all repos and non-baseline tiers, the static analysis oracle achieved "
        f"an average coarse-grained smell recall of {oracle_r}, while Gemini 3 Flash Preview "
        f"achieved {llm_r} (gap: {gap_str}). Mode 3 (LLM judge) achieved a recall of "
        f"{judge_r} and a precision of {judge_p} by filtering oracle findings. "
        f"The oracle benefits from precise pattern matching on known Pylint/Flake8 codes, "
        f"whereas the LLM infers smells from structural summaries alone.",
        "",
        "| Repo | Tier | Oracle Recall | LLM Recall | Judge Precision | Judge Recall |",
        "|---|---|---|---|---|---|",
    ]

    for repo in report["repos"]:
        for tier in repo["tiers"]:
            lines.append(
                f"| {repo['name']} | {tier['severity']} "
                f"| {_pct(tier['oracle'].get('recall'))} "
                f"| {_pct(tier['llm'].get('recall'))} "
                f"| {_pct(tier['judge'].get('precision'))} "
                f"| {_pct(tier['judge'].get('recall'))} |"
            )

    by_tier = r3["by_tier"]
    lines += [
        "",
        "---",
        "",
        "## RQ2: LLM Fine-Grained vs Coarse-Grained Detection",
        "",
        "The LLM receives only AST structural summaries (imports, function line counts, "
        "local variable counts) rather than full source code. Coarse-grained smells "
        "(circular imports, god modules, layer violations) are visible in the import graph "
        "and class/function sizes, while fine-grained smells (long methods, poor naming) "
        "require function-body analysis. This limits fine-grained recall.",
        "",
        "| Category | LLM Recall (avg across repos and tiers) |",
        "|---|---|",
        f"| Coarse-grained | {_pct(r2['llm_coarse_recall'])} |",
        f"| Fine-grained | {_pct(r2['llm_fine_recall'])} |",
        "",
        "---",
        "",
        "## RQ3: LLM Detection Accuracy by Severity",
        "",
        "As severity increases, more smells are injected, providing more signal for the LLM "
        "to detect. The table below shows average LLM recall across all repos per tier.",
        "",
        "| Tier | Avg LLM Recall (all repos) |",
        "|---|---|",
        "| None | N/A (baseline) |",
        f"| Low | {_pct(by_tier.get('low'))} |",
        f"| Medium | {_pct(by_tier.get('medium'))} |",
        f"| High | {_pct(by_tier.get('high'))} |",
        "",
        "---",
        "",
        "## Limitations",
        "",
        "The following limitations apply to these results and should be disclosed in the final report:",
        "",
        "1. **AST summaries, not full source:** Gemini receives per-file structural summaries "
        "rather than complete source code. This may understate LLM detection capability for "
        "smells that require reading function bodies.",
        "2. **Pre-existing baseline noise:** Cookiecutter's none tier contains pre-existing "
        "Pylint smell-relevant findings (god_module), which inflate false positive counts for "
        "the oracle at low severity.",
        "3. **Circular import detection gap:** Injected circular imports at Low tier did not "
        "trigger Pylint R0401 (cyclic-import) because stubs are syntactically valid standalone "
        "functions. Oracle detection of circular imports relies on W0611 (unused-import) as a "
        "proxy signal.",
        "4. **Single LLM evaluated:** Results reflect Gemini 3 Flash Preview only. Generalization "
        "to other models requires additional experiments.",
        "5. **Small repo set:** Three repos limits statistical generalizability.",
    ]

    return "\n".join(lines) + "\n"


def generate_report(snapshots_dir: Path, output_dir: Path, repo_names: list) -> dict:
    """Read all result files, compute metrics, and write JSON and Markdown reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    repo_results = []
    parse_errors = 0

    for repo_name in repo_names:
        tiers_out = []
        for severity in SEVERITY_TIERS:
            data = _load_tier_data(snapshots_dir, repo_name, severity)
            oracle_tier = _build_oracle_tier(data["oracle"], data["injection_log"])
            llm_tier = _build_llm_tier(data["llm"], data["injection_log"])
            judge_tier = _build_judge_tier(data["judge"], data["injection_log"])
            if llm_tier.get("parse_error"):
                parse_errors += 1
            tiers_out.append({
                "severity": severity,
                "oracle": oracle_tier,
                "llm": llm_tier,
                "judge": judge_tier,
            })
        repo_results.append({"name": repo_name, "tiers": tiers_out})

    report = {
        "generated_at": ts,
        "repos": repo_results,
        "rq_summary": _build_rq_summaries(repo_results),
    }

    json_path = output_dir / "smellscope_report.json"
    md_path = output_dir / "smellscope_report.md"

    try:
        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[reporter] JSON report -> {json_path}")
    except OSError as exc:
        print(f"[reporter] ERROR writing JSON report: {exc}", file=sys.stderr)

    try:
        md_path.write_text(_build_markdown(report), encoding="utf-8")
        print(f"[reporter] Markdown report -> {md_path}")
    except OSError as exc:
        print(f"[reporter] ERROR writing Markdown report: {exc}", file=sys.stderr)

    if parse_errors > 2:
        print(
            f"[reporter] WARNING: {parse_errors} of 12 LLM calls had parse_error=true.",
            file=sys.stderr,
        )

    return report
