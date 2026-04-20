"""
llm_judge.py - LLM-as-judge module for SmellScope (Mode 3).

Reads oracle_results.json for a snapshot, asks Gemini to validate each
smell-relevant finding as genuine or false positive, and writes judge_results.json.
"""

import json
import sys
from pathlib import Path

_PROMPT_TEMPLATE = """\
You are reviewing a static analysis finding on a Python codebase.

Finding:
- Smell type: {smell_type}
- File: {file}
- Tool: {tool}
- Code: {code}
- Message: "{message}"

Is this a genuine code smell or a false positive?
Respond in JSON only:
{{"verdict": "genuine" | "false_positive", "reason": "<one sentence>"}}"""


def _build_prompt(finding: dict) -> str:
    """Return the filled prompt for a single oracle finding."""
    return _PROMPT_TEMPLATE.format(
        smell_type=finding.get("smell_type", "unknown"),
        file=finding.get("file", "unknown"),
        tool=finding.get("tool", "unknown"),
        code=finding.get("code", "N/A"),
        message=finding.get("message", ""),
    )


def _parse_verdict(raw_text: str) -> tuple:
    """
    Parse the LLM response as JSON and extract verdict/reason.

    Returns (verdict_str, reason_str, parse_error_bool).
    """
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    text = text.strip()
    try:
        parsed = json.loads(text)
        verdict = parsed.get("verdict", "")
        reason = parsed.get("reason", "")
        if verdict not in ("genuine", "false_positive"):
            return None, reason, True
        return verdict, reason, False
    except json.JSONDecodeError:
        return None, "", True


def _call_gemini_judge(prompt: str, model: str, api_key: str) -> tuple:
    """
    Send one prompt to Gemini and return (verdict, reason, parse_error).

    Retries once on parse failure, then defaults to genuine to avoid silent drops.
    """
    try:
        from google import genai
    except ImportError:
        print("[judge] ERROR: google-genai not installed. Run: pip install google-genai", file=sys.stderr)
        return "genuine", "import_error", True

    client = genai.Client(api_key=api_key)

    for attempt in range(2):
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            raw_text = response.text
        except Exception as exc:
            print(f"[judge] API call failed (attempt {attempt + 1}): {exc}", file=sys.stderr)
            continue

        verdict, reason, error = _parse_verdict(raw_text)
        if not error:
            return verdict, reason, False

        if attempt == 0:
            print("[judge] Parse error on first attempt, retrying...", file=sys.stderr)

    print("[judge] Defaulting to genuine after parse failure.", file=sys.stderr)
    return "genuine", "parse_error", True


def _collect_findings(oracle: dict) -> list:
    """
    Collect all smell-relevant findings from oracle results, tagged with tool name.

    Returns a flat list with a 'tool' field added to each entry.
    """
    findings = []
    for tool in ("pylint", "flake8"):
        for entry in oracle.get(tool, {}).get("smell_relevant", []):
            findings.append({**entry, "tool": tool})
    return findings


def _deduplicate_by_smell_type(findings: list) -> list:
    """Return one representative finding per distinct smell_type (first occurrence)."""
    seen = set()
    unique = []
    for f in findings:
        st = f.get("smell_type")
        if st and st not in seen:
            seen.add(st)
            unique.append(f)
    return unique


def run_judge(snapshot_dir: Path, model: str, api_key: str) -> dict:
    """
    Validate oracle findings for a snapshot using Gemini and write judge_results.json.

    Returns the judge results dict.
    """
    oracle_path = snapshot_dir / "oracle_results.json"
    if not oracle_path.exists():
        print(f"[judge] oracle_results.json missing at {snapshot_dir} - skipping.", file=sys.stderr)
        return {}

    try:
        oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[judge] ERROR reading oracle_results.json: {exc}", file=sys.stderr)
        return {}

    repo = oracle.get("repo", snapshot_dir.parent.name)
    severity = oracle.get("severity", snapshot_dir.name)

    all_findings = _collect_findings(oracle)
    unique_findings = _deduplicate_by_smell_type(all_findings)

    results = {
        "repo": repo,
        "severity": severity,
        "model": model,
        "validated": [],
        "rejected": [],
    }

    if not unique_findings:
        print(f"[judge] No smell-relevant findings for {repo}/{severity} - writing empty results.")
        out_path = snapshot_dir / "judge_results.json"
        try:
            out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        except OSError as exc:
            print(f"[judge] ERROR writing judge_results.json: {exc}", file=sys.stderr)
        return results

    print(f"[judge] Judging {repo}/{severity}: {len(unique_findings)} unique smell type(s).")

    for finding in unique_findings:
        smell_type = finding.get("smell_type", "unknown")
        prompt = _build_prompt(finding)
        verdict, reason, _ = _call_gemini_judge(prompt, model, api_key)

        entry = {
            "smell_type": smell_type,
            "file": finding.get("file", ""),
            "tool": finding.get("tool", ""),
            "code": finding.get("code", ""),
            "verdict": verdict,
            "reason": reason,
        }

        if verdict == "genuine":
            results["validated"].append(entry)
        else:
            results["rejected"].append(entry)

        print(f"[judge]   {smell_type}: {verdict}")

    out_path = snapshot_dir / "judge_results.json"
    try:
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"[judge] ERROR writing judge_results.json: {exc}", file=sys.stderr)

    print(
        f"[judge] {repo}/{severity}: {len(results['validated'])} validated, "
        f"{len(results['rejected'])} rejected. Results -> {out_path}"
    )
    return results
