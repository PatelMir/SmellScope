"""
oracle_runner.py - Pylint and Flake8 runner for DriftLens.

Runs static analysis on a snapshot directory, classifies each finding against
the smell maps in config.py, and writes oracle_results.json.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from config import FLAKE8_SMELL_MAP, PYLINT_SMELL_MAP


def install_repo_deps(deps: list) -> None:
    """Install repo dependencies via pip before running the oracle."""
    if not deps:
        return
    print(f"[oracle] Installing deps: {deps}")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--break-system-packages"] + deps,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[oracle] WARNING: dep install non-zero exit.\n{result.stderr}", file=sys.stderr)
    else:
        print("[oracle] Deps installed OK.")


def _run_pylint(snapshot_path: Path) -> list:
    """Run Pylint on snapshot_path and return a list of raw finding dicts."""
    result = subprocess.run(
        [
            sys.executable, "-m", "pylint",
            str(snapshot_path),
            "--output-format=json",
            "--score=n",
            "--disable=C",
            "--enable=E,W,R",
        ],
        capture_output=True,
        text=True,
    )

    stdout = result.stdout.strip()
    if not stdout:
        print("[oracle] Pylint produced no stdout output.", file=sys.stderr)
        return []

    # Pylint sometimes writes non-JSON preamble; strip everything before the first '['.
    bracket_idx = stdout.find("[")
    if bracket_idx > 0:
        stdout = stdout[bracket_idx:]

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        print(f"[oracle] ERROR parsing Pylint JSON: {exc}", file=sys.stderr)
        print(f"[oracle] Raw Pylint stdout (first 500 chars): {stdout[:500]}", file=sys.stderr)
        return []


def _file_contains_marker(path: Path, marker: str) -> bool:
    """Return True if the file at path contains the given marker string."""
    try:
        return marker in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def _classify_pylint(
    findings: list,
    snapshot_path: Path,
    platform_suppress_modules: list,
) -> tuple:
    """
    Split Pylint findings into (smell_relevant, other).

    E0401 and W0611 in files marked [DRIFTLENS:circular_import] are classified as
    circular_import. E0401 for known platform-only modules are dropped entirely.
    """
    smell_relevant = []
    other = []

    for f in findings:
        code = f.get("message-id", "")
        file_rel = f.get("path", "")
        file_abs = snapshot_path / file_rel if not Path(file_rel).is_absolute() else Path(file_rel)
        message = f.get("message", "")

        if code == "E0401" and platform_suppress_modules:
            flagged_module = message.split("'")[1] if "'" in message else ""
            if any(flagged_module == m or flagged_module.startswith(m + ".") for m in platform_suppress_modules):
                continue

        entry = {
            "file": file_rel,
            "line": f.get("line"),
            "col": f.get("column"),
            "code": code,
            "symbol": f.get("symbol", ""),
            "message": message,
            "smell_type": None,
        }

        if code in ("E0401", "W0611") and _file_contains_marker(file_abs, "[DRIFTLENS:circular_import]"):
            entry["smell_type"] = "circular_import"
            smell_relevant.append(entry)
            continue

        if code in PYLINT_SMELL_MAP:
            entry["smell_type"] = PYLINT_SMELL_MAP[code]
            smell_relevant.append(entry)
        else:
            other.append(entry)

    return smell_relevant, other


def _summarize_pylint(findings: list) -> dict:
    """Return a by_category count dict for E/W/R codes."""
    counts = {"E": 0, "W": 0, "R": 0}
    for f in findings:
        code = f.get("message-id", "")
        if code and code[0] in counts:
            counts[code[0]] += 1
    return counts


_FLAKE8_PATTERN = re.compile(r"^(.+):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$")


def _run_flake8(snapshot_path: Path) -> list:
    """Run Flake8 on snapshot_path and return a list of raw finding dicts."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", str(snapshot_path)],
        capture_output=True,
        text=True,
    )

    findings = []
    for line in result.stdout.splitlines():
        match = _FLAKE8_PATTERN.match(line.strip())
        if match:
            findings.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "col": int(match.group(3)),
                "code": match.group(4),
                "message": match.group(5).strip(),
            })
    return findings


def _classify_flake8(findings: list) -> tuple:
    """Split Flake8 findings into (smell_relevant, other)."""
    smell_relevant = []
    other = []
    for f in findings:
        entry = {**f, "smell_type": None}
        code = f.get("code", "")
        if code in FLAKE8_SMELL_MAP:
            entry["smell_type"] = FLAKE8_SMELL_MAP[code]
            smell_relevant.append(entry)
        else:
            other.append(entry)
    return smell_relevant, other


def run_oracle(
    snapshot_path: Path,
    repo_config: dict,
    repo_name: str,
    severity: str,
) -> dict:
    """
    Run Pylint and Flake8 on snapshot_path, classify findings, and write oracle_results.json.

    Returns the results dict.
    """
    print(f"[oracle] Running oracle on {repo_name}/{severity} -> {snapshot_path}")

    suppress_mods = repo_config.get("platform_suppress_modules", [])
    raw_pylint = _run_pylint(snapshot_path)
    pylint_smell, pylint_other = _classify_pylint(raw_pylint, snapshot_path, suppress_mods)
    pylint_by_cat = _summarize_pylint(raw_pylint)

    raw_flake8 = _run_flake8(snapshot_path)
    flake8_smell, flake8_other = _classify_flake8(raw_flake8)

    results = {
        "repo": repo_name,
        "severity": severity,
        "pylint": {
            "raw_count": len(raw_pylint),
            "by_category": pylint_by_cat,
            "smell_relevant": pylint_smell,
            "other": pylint_other,
        },
        "flake8": {
            "raw_count": len(raw_flake8),
            "smell_relevant": flake8_smell,
            "other": flake8_other,
        },
    }

    out_path = snapshot_path / "oracle_results.json"
    try:
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"[oracle] ERROR writing oracle_results.json: {exc}", file=sys.stderr)

    print(
        f"[oracle] {repo_name}/{severity}: pylint={len(raw_pylint)} findings "
        f"(smell={len(pylint_smell)}, other={len(pylint_other)}), "
        f"flake8={len(raw_flake8)} findings "
        f"(smell={len(flake8_smell)}, other={len(flake8_other)}). "
        f"Results -> {out_path}"
    )
    return results
