"""
llm_interface.py - AST-based code summarizer and Gemini LLM interface for SmellScope.

Generates a structural summary of a snapshot directory, sends it to Gemini,
and parses the detected smells from the JSON response.
"""

import ast
import json
import sys
import time
from pathlib import Path

_MODEL_NAME = "gemini-3.1-flash-lite-preview"


def _count_locals(func_node: ast.FunctionDef) -> int:
    """Count local variables assigned in a function (excludes parameters)."""
    count = 0
    params = {arg.arg for arg in func_node.args.args}
    for node in ast.walk(func_node):
        if isinstance(node, (ast.Assign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id not in params:
                    count += 1
    return count


def _summarize_file(path: Path) -> dict | None:
    """Parse a Python file and return a structural summary dict, or None on failure."""
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        print(f"[llm] WARNING: cannot parse {path.name}: {exc}", file=sys.stderr)
        return None

    total_lines = len(source.splitlines())

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_lines = (node.end_lineno or node.lineno) - node.lineno + 1
            functions.append({
                "name": node.name,
                "line_count": func_lines,
                "local_var_count": _count_locals(node),
            })

    return {
        "file": path.name,
        "total_lines": total_lines,
        "imports": imports,
        "classes": classes,
        "functions": functions,
    }


def _format_summary_block(summary: dict) -> str:
    """Format a single file summary as a compact text block."""
    lines = [f"FILE: {summary['file']} ({summary['total_lines']} lines)"]
    imports_str = ", ".join(summary["imports"]) if summary["imports"] else "(none)"
    lines.append(f"IMPORTS: {imports_str}")
    classes_str = ", ".join(summary["classes"]) if summary["classes"] else "(none)"
    lines.append(f"CLASSES: {classes_str}")
    if summary["functions"]:
        lines.append("FUNCTIONS:")
        for fn in summary["functions"]:
            lines.append(
                f"  - {fn['name']}(...) [{fn['line_count']} lines, {fn['local_var_count']} locals]"
            )
    else:
        lines.append("FUNCTIONS: (none)")
    return "\n".join(lines)


def build_codebase_summary(snapshot_path: Path, max_chars: int = 12000) -> tuple:
    """
    Build a codebase summary string for all .py files in snapshot_path.

    Returns (summary_str, files_dropped_count).
    """
    py_files = sorted(snapshot_path.rglob("*.py"), key=lambda p: p.stat().st_size, reverse=True)

    summaries = []
    for f in py_files:
        s = _summarize_file(f)
        if s is not None:
            summaries.append(s)

    summaries.sort(key=lambda s: s["total_lines"], reverse=True)
    blocks = [_format_summary_block(s) for s in summaries]
    combined = "\n\n".join(blocks)

    if len(combined) <= max_chars:
        return combined, 0

    dropped = 0
    while len(combined) > max_chars and len(blocks) > 1:
        blocks.pop()
        dropped += 1
        combined = "\n\n".join(blocks)

    print(
        f"[llm] Summary truncated: dropped {dropped} file(s) to fit {max_chars} char limit.",
        file=sys.stderr,
    )
    return combined, dropped


_PROMPT_TEMPLATE = """\
You are a software architecture expert. Below is a structural summary of a Python codebase extracted via AST analysis. Each file shows its imports, classes, functions, and local variable counts.

<codebase_summary>
{summary}
</codebase_summary>

Analyze this codebase for the following architectural smells. For each smell you detect, report the smell type, the files involved, and a one-sentence explanation.

Smell types to check:
- circular_import: two or more modules that import from each other, creating a dependency cycle
- god_module: a single module with an excessive number of functions, classes, or local variables relative to its peers
- layer_boundary_violation: a lower-level module (utility, domain, data) importing from a higher-level module (controller, CLI, orchestrator)
- long_method: a function with significantly more lines than the average function in the codebase
- poor_naming: functions or variables with single-character or non-descriptive names

Respond ONLY in the following JSON format. Do not include any text outside the JSON block. Do not wrap in markdown code fences.

{{
  "detected_smells": [
    {{
      "smell_type": "<one of the five types above>",
      "files": ["<file1.py>", "<file2.py>"],
      "explanation": "<one sentence>"
    }}
  ]
}}

If no smells are detected, return: {{"detected_smells": []}}"""


def _build_prompt(summary: str) -> str:
    """Return the filled prompt string for a given codebase summary."""
    return _PROMPT_TEMPLATE.format(summary=summary)


def _parse_llm_response(raw_text: str) -> tuple:
    """Attempt to parse the LLM response as JSON. Returns (parsed_dict, parse_error_bool)."""
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    text = text.strip()
    try:
        return json.loads(text), False
    except json.JSONDecodeError:
        return None, True


def call_gemini(prompt: str, api_key: str) -> tuple:
    """
    Send one prompt to Gemini and return (parsed_result, raw_text).

    No retries -- each call costs one RPD slot and the daily limit is tight.
    """
    try:
        from google import genai
    except ImportError:
        print("[llm] ERROR: google-genai not installed. Run: pip install google-genai", file=sys.stderr)
        return {"detected_smells": [], "parse_error": True, "raw_response": ""}, ""

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
        raw_text = response.text
    except Exception as exc:
        print(f"[llm] API call failed: {exc}", file=sys.stderr)
        return {"detected_smells": [], "parse_error": True, "raw_response": ""}, ""

    parsed, error = _parse_llm_response(raw_text)
    if not error:
        return parsed, raw_text

    return {
        "detected_smells": [],
        "parse_error": True,
        "raw_response": raw_text[:500],
    }, raw_text


def run_llm(snapshot_path: Path, repo_name: str, severity: str, api_key: str) -> dict:
    """Build a codebase summary, query Gemini, parse results, and write llm_results.json."""
    out_path = snapshot_path / "llm_results.json"
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            if not existing.get("parse_error", True):
                print(f"[llm] Skipping {repo_name}/{severity} -- already successful.")
                return existing
        except (OSError, json.JSONDecodeError):
            pass

    print(f"[llm] Running LLM on {repo_name}/{severity} -> {snapshot_path}")

    summary, files_dropped = build_codebase_summary(snapshot_path)
    prompt = _build_prompt(summary)

    time.sleep(5)

    parsed, _ = call_gemini(prompt, api_key)
    parse_error = parsed.get("parse_error", False)
    detected_smells = parsed.get("detected_smells", [])

    results = {
        "repo": repo_name,
        "severity": severity,
        "model": _MODEL_NAME,
        "detected_smells": detected_smells,
        "parse_error": parse_error,
        "summary_char_count": len(summary),
        "files_dropped": files_dropped,
    }
    if parse_error and "raw_response" in parsed:
        results["raw_response"] = parsed["raw_response"]

    out_path = snapshot_path / "llm_results.json"
    try:
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"[llm] ERROR writing llm_results.json: {exc}", file=sys.stderr)

    status = "parse_error" if parse_error else f"{len(detected_smells)} smell(s) detected"
    print(f"[llm] {repo_name}/{severity}: {status}. Results -> {out_path}")
    return results