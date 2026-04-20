"""
repo_validator.py - MSR-based repository validation for SmellScope dataset expansion.

Clones each candidate from candidates.json, computes PyDriller and static
analysis metrics, and writes repo_selection_log.json with pass/fail verdicts.

Usage:
    python3 repo_validator.py --candidates candidates.json \
        --output repo_selection_log.json
    python3 repo_validator.py --candidates candidates.json \
        --output repo_selection_log.json --python-min 5 --python-max 20 --stop-at 15
"""

import argparse
import ast
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import git

try:
    from pydriller import Repository as PyDrillerRepo
except ImportError:
    print(
        "ERROR: pydriller is not installed. Run: pip install pydriller",
        file=sys.stderr,
    )
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from config import PYLINT_SMELL_MAP

_COMMIT_CUTOFF = date(2025, 2, 1)
_MIN_COMMITS = 5
_MIN_RATIO = 0.35

_EXCLUDED_DIRS = {
    "tests", "test", "docs", "migrations",
    "__pycache__", ".git", "node_modules", "venv", "env",
}

def _clone(clone_url: str, dest: Path) -> None:
    """Shallow clone with depth=5 into dest."""
    git.Repo.clone_from(clone_url, dest, depth=5)

def _is_excluded(path: Path, root: Path) -> bool:
    """Return True if any path component is in _EXCLUDED_DIRS."""
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in _EXCLUDED_DIRS for part in parts)

def _py_files(root: Path) -> list[Path]:
    return [
        p for p in root.rglob("*.py")
        if p.is_file() and not _is_excluded(p, root)
    ]

def _all_files(root: Path) -> list[Path]:
    """Return all files not inside hidden directories."""
    result = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            parts = p.relative_to(root).parts
        except ValueError:
            continue
        if not any(part.startswith(".") for part in parts):
            result.append(p)
    return result

def _pydriller_metrics(repo_path: Path) -> dict:
    """Traverse commits and return date/count/contributor metrics."""
    count = 0
    earliest: date | None = None
    emails: set[str] = set()

    for commit in PyDrillerRepo(str(repo_path)).traverse_commits():
        count += 1
        if commit.author.email:
            emails.add(commit.author.email)
        if commit.author_date:
            d = commit.author_date.date()
            if earliest is None or d < earliest:
                earliest = d

    return {
        "first_commit_date": earliest.isoformat() if earliest else None,
        "commit_count": f">={_MIN_COMMITS}" if count >= _MIN_COMMITS else count,
        "contributor_count": len(emails),
    }

def _top_level_imports(source: str) -> list[str]:
    """Return the top-level module name from each import statement in source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.append(node.module.split(".")[0])
    return names

def _check_module_imports(files: list[Path], module_names: set[str]) -> bool:
    """Return True if any file imports another module that exists in the repo."""
    for p in files:
        try:
            source = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for imported in _top_level_imports(source):
            if imported in module_names and imported != p.stem:
                return True
    return False

def _baseline_dirty_smells(repo_path: Path) -> set[str]:
    """
    Run Pylint on repo_path and return smell categories already present.

    Uses PYLINT_SMELL_MAP from config.py. Returns an empty set on timeout
    or parse failure.
    """
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "pylint",
                str(repo_path),
                "--disable=C",
                "--output-format=json",
                "--recursive=y",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        raw = result.stdout.strip()
        if not raw:
            return set()
        findings = json.loads(raw)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return set()

    categories: set[str] = set()
    for f in findings:
        code = f.get("message-id", "")
        if code in PYLINT_SMELL_MAP:
            categories.add(PYLINT_SMELL_MAP[code])
    return categories

def _compute_metrics(repo_path: Path) -> dict:
    """Compute and return all seven metrics for a cloned repo."""
    pd = _pydriller_metrics(repo_path)

    files = _py_files(repo_path)
    py_count = len(files)
    total_count = len(_all_files(repo_path))
    ratio = round(py_count / total_count, 4) if total_count > 0 else 0.0

    module_names = {p.stem for p in files}
    has_imports = _check_module_imports(files, module_names)

    dirty = _baseline_dirty_smells(repo_path)

    return {
        "first_commit_date": pd["first_commit_date"],
        "commit_count": pd["commit_count"],
        "contributor_count": pd["contributor_count"],
        "python_file_count": py_count,
        "python_ratio": ratio,
        "has_module_imports": has_imports,
        "baseline_dirty_smells": len(dirty),
        "_dirty_categories": sorted(dirty),
    }

def _hard_fail(metrics: dict, py_min: int, py_max: int) -> str | None:
    """Return a failure reason string, or None if all hard checks pass."""
    raw_date = metrics.get("first_commit_date")
    if raw_date is None:
        return "first_commit_date could not be determined"
    if date.fromisoformat(raw_date) <= _COMMIT_CUTOFF:
        return f"first_commit_date={raw_date} on or before 2025-02-01"

    count = metrics["commit_count"]
    if isinstance(count, int) and count < _MIN_COMMITS:
        return f"commit_count={count} below minimum {_MIN_COMMITS}"

    pfc = metrics["python_file_count"]
    if pfc < py_min:
        return f"python_file_count={pfc} below minimum {py_min}"
    if pfc > py_max:
        return f"python_file_count={pfc} above maximum {py_max}"

    if metrics["python_ratio"] < _MIN_RATIO:
        return f"python_ratio={metrics['python_ratio']:.2f} below minimum {_MIN_RATIO}"

    if not metrics["has_module_imports"]:
        return "has_module_imports=False (no inter-module structure detected)"

    return None


def _soft_warnings(metrics: dict) -> list[str]:
    """Return soft warning strings (do not cause rejection)."""
    warnings = []
    if metrics["contributor_count"] == 1:
        warnings.append("contributor_count=1")
    cats = metrics.get("_dirty_categories", [])
    if cats:
        warnings.append(f"baseline_dirty_smells: {', '.join(cats)}")
    return warnings


def _clean(metrics: dict) -> dict:
    return {k: v for k, v in metrics.items() if not k.startswith("_")}

def _validate_one(
    candidate: dict, py_min: int, py_max: int
) -> tuple[str, dict, str | None, list[str]]:
    """
    Clone, measure, evaluate one candidate.

    Returns (status, metrics, fail_reason, warnings).
    status is 'pass', 'warn', or 'fail'.
    Cleans up temp clone before returning.
    """
    tmp = Path(tempfile.mkdtemp(prefix="smellscope_"))
    try:
        try:
            _clone(candidate["clone_url"], tmp)
        except Exception as exc:
            return "fail", {}, f"clone failed: {exc}", []

        metrics = _compute_metrics(tmp)
        reason = _hard_fail(metrics, py_min, py_max)
        warnings = _soft_warnings(metrics)

        if reason:
            return "fail", metrics, reason, warnings
        if warnings:
            return "warn", metrics, None, warnings
        return "pass", metrics, None, []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def validate_repos(
    candidates_path: Path,
    output_path: Path,
    python_file_min: int = 5,
    python_file_max: int = 20,
    stop_at: int = 15,
) -> dict:
    """
    Validate each candidate repo and write repo_selection_log.json.

    Stops once stop_at repos have passed (clean or with warnings).
    Returns the results dict.
    """
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))

    validated: list[dict] = []
    rejected: list[dict] = []
    warnings_only: list[dict] = []
    passed = 0

    for candidate in candidates:
        if passed >= stop_at:
            print(f"[repo_validator] Reached {stop_at} passing repos — stopping early.")
            break

        full_name = candidate["full_name"]
        print(f"[repo_validator] Checking {full_name}...")

        status, metrics, reason, warns = _validate_one(
            candidate, python_file_min, python_file_max
        )
        m = _clean(metrics)

        pfc = m.get("python_file_count", "?")
        ratio = m.get("python_ratio", "?")
        commits = m.get("commit_count", "?")
        contribs = m.get("contributor_count", "?")

        if status == "fail":
            rejected.append({
                "full_name": full_name,
                "clone_url": candidate.get("clone_url", ""),
                "fail_reason": reason,
                "metrics": m,
            })
            print(f"  [FAIL] {full_name} — {reason}")

        elif status == "warn":
            warnings_only.append({
                "full_name": full_name,
                "clone_url": candidate.get("clone_url", ""),
                "warnings": warns,
                "metrics": m,
            })
            passed += 1
            print(
                f"  [WARN] {full_name} — PASS with warnings: {'; '.join(warns)}"
                f" | {pfc} py files, {ratio} ratio, {commits} commits,"
                f" {contribs} contributors"
            )

        else:
            validated.append({
                "full_name": full_name,
                "clone_url": candidate.get("clone_url", ""),
                "metrics": m,
                "warnings": [],
            })
            passed += 1
            print(
                f"  [PASS] {full_name} — {pfc} py files, {ratio} ratio,"
                f" {commits} commits, {contribs} contributors"
            )

    results = {
        "validated": validated,
        "rejected": rejected,
        "warnings_only": warnings_only,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(
        f"\n[repo_validator] Done: {len(validated)} clean pass,"
        f" {len(warnings_only)} pass-with-warnings,"
        f" {len(rejected)} rejected. Log -> {output_path}"
    )
    return results

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SmellScope: validate candidate repos for dataset expansion."
    )
    parser.add_argument(
        "--candidates",
        required=True,
        type=Path,
        help="Path to candidates.json from repo_finder.py.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write repo_selection_log.json.",
    )
    parser.add_argument(
        "--python-min",
        dest="python_file_min",
        type=int,
        default=5,
        metavar="N",
        help="Minimum .py file count (default: 5).",
    )
    parser.add_argument(
        "--python-max",
        dest="python_file_max",
        type=int,
        default=20,
        metavar="N",
        help="Maximum .py file count (default: 20).",
    )
    parser.add_argument(
        "--stop-at",
        dest="stop_at",
        type=int,
        default=15,
        metavar="N",
        help="Stop after this many repos pass validation (default: 15).",
    )
    return parser.parse_args()

def main() -> None:
    args = _parse_args()
    validate_repos(
        args.candidates,
        args.output,
        args.python_file_min,
        args.python_file_max,
        args.stop_at,
    )

if __name__ == "__main__":
    main()