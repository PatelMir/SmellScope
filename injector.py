"""
injector.py - Smell injection module for DriftLens.

Copies a package directory to a snapshot path and injects code smells based on
severity tier. Never modifies the original source.

Tier summary:
  none   - clean copy, no injections
  low    - circular_import + layer_boundary_violation
  medium - low + god_module
  high   - medium + long_method + poor_naming
"""

import ast
import json
import shutil
import sys
from pathlib import Path

from config import REPO_CONFIGS


def _read_file(path: Path) -> str:
    """Read and return the text contents of a file."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[injector] ERROR reading {path}: {exc}", file=sys.stderr)
        raise


def _write_file(path: Path, content: str) -> None:
    """Write text content to a file."""
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"[injector] ERROR writing {path}: {exc}", file=sys.stderr)
        raise


def _validate_syntax(path: Path, content: str) -> bool:
    """Return True if content parses as valid Python, False otherwise."""
    try:
        ast.parse(content)
        return True
    except SyntaxError as exc:
        print(f"[injector] Syntax error in {path.name}: {exc}", file=sys.stderr)
        return False


def _safe_append(path: Path, original: str, addition: str, warnings: list) -> bool:
    """Append addition to original content, validate syntax, revert on failure."""
    new_content = original + addition
    if not _validate_syntax(path, new_content):
        msg = f"SyntaxError after injection into {path.name} - reverted."
        print(f"[injector] WARNING: {msg}", file=sys.stderr)
        warnings.append({"file": str(path.name), "warning": msg})
        _write_file(path, original)
        return False
    _write_file(path, new_content)
    return True


def _file_to_module(filename: str, import_prefix: str) -> str:
    """Convert a relative file path like 'services/foo.py' to dotted module 'services.foo'."""
    module = Path(filename).with_suffix("").as_posix().replace("/", ".")
    if import_prefix:
        return f"{import_prefix}.{module}"
    return module


def _inject_circular_import(
    dest_path: Path, repo_config: dict, injections: list, warnings: list
) -> None:
    """Inject circular_import: mutual stubs and cross-imports between two files."""
    targets = repo_config.get("injection_targets", {}).get("circular_import")
    if not targets or len(targets) != 2:
        warnings.append({"warning": "circular_import: no valid injection_targets defined."})
        return

    file_a, file_b = targets
    prefix = repo_config.get("import_prefix", "")
    module_a = _file_to_module(file_a, prefix)
    module_b = _file_to_module(file_b, prefix)
    stub_a = f"_driftlens_{Path(file_a).stem}_stub"
    stub_b = f"_driftlens_{Path(file_b).stem}_stub"

    path_a = dest_path / file_a
    path_b = dest_path / file_b

    if not path_a.exists() or not path_b.exists():
        msg = f"circular_import: target file(s) not found ({file_a}, {file_b}) - skipping."
        print(f"[injector] WARNING: {msg}", file=sys.stderr)
        warnings.append({"warning": msg})
        return

    guard = "[DRIFTLENS:circular_import]"
    orig_a = _read_file(path_a)
    orig_b = _read_file(path_b)

    if guard in orig_a or guard in orig_b:
        warnings.append({"warning": "circular_import guard already present - skipping."})
        return

    add_a = (
        f"\n\n# [DRIFTLENS:circular_import] injected stub\n"
        f"def {stub_a}():\n    pass\n"
        f"\n\n# [DRIFTLENS:circular_import] injected\n"
        f"from {module_b} import {stub_b}  # noqa\n"
    )
    add_b = (
        f"\n\n# [DRIFTLENS:circular_import] injected stub\n"
        f"def {stub_b}():\n    pass\n"
        f"\n\n# [DRIFTLENS:circular_import] injected\n"
        f"from {module_a} import {stub_a}  # noqa\n"
    )

    ok_a = _safe_append(path_a, orig_a, add_a, warnings)
    ok_b = _safe_append(path_b, orig_b, add_b, warnings)

    if ok_a or ok_b:
        modified = ([file_a] if ok_a else []) + ([file_b] if ok_b else [])
        injections.append({
            "smell_type": "circular_import",
            "files_modified": modified,
            "description": (
                f"Mutual stubs {stub_a}/{stub_b} with cross-imports between "
                f"{file_a} and {file_b}."
            ),
        })


def _inject_layer_violation(
    dest_path: Path, repo_config: dict, injections: list, warnings: list
) -> None:
    """Inject layer_boundary_violation: lower module imports stub from upper module."""
    targets = repo_config.get("injection_targets", {}).get("layer_violation")
    if not targets or len(targets) != 2:
        warnings.append({"warning": "layer_violation: no valid injection_targets defined."})
        return

    lower_file, upper_file = targets
    prefix = repo_config.get("import_prefix", "")
    upper_module = _file_to_module(upper_file, prefix)
    stub_name = "_driftlens_orchestrator_stub"

    lower_path = dest_path / lower_file
    upper_path = dest_path / upper_file

    if not lower_path.exists() or not upper_path.exists():
        msg = f"layer_violation: target file(s) not found ({lower_file}, {upper_file}) - skipping."
        print(f"[injector] WARNING: {msg}", file=sys.stderr)
        warnings.append({"warning": msg})
        return

    guard = "[DRIFTLENS:layer_violation]"
    upper_orig = _read_file(upper_path)
    lower_orig = _read_file(lower_path)

    if guard in upper_orig or guard in lower_orig:
        warnings.append({"warning": "layer_violation guard already present - skipping."})
        return

    add_upper = (
        f"\n\n# [DRIFTLENS:layer_violation] injected stub\n"
        f"def {stub_name}():\n    pass\n"
    )
    ok_upper = _safe_append(upper_path, upper_orig, add_upper, warnings)
    if not ok_upper:
        return

    add_lower = (
        f"\n\n# [DRIFTLENS:layer_violation] injected - imports from higher layer"
        f" (inverted dependency)\n"
        f"from {upper_module} import {stub_name} as _driftlens_orchestrator_ref  # noqa\n"
    )
    ok_lower = _safe_append(lower_path, lower_orig, add_lower, warnings)

    if ok_lower:
        modified = ([upper_file] if ok_upper else []) + ([lower_file] if ok_lower else [])
        injections.append({
            "smell_type": "layer_boundary_violation",
            "files_modified": modified,
            "description": (
                f"{lower_file} imports from {upper_file}, inverting the expected "
                "dependency direction."
            ),
        })


def _inject_god_module(
    dest_path: Path, repo_config: dict, injections: list, warnings: list
) -> None:
    """Inject god_module: class with 8 attributes (R0902) and function with 16 locals (R0914)."""
    target = repo_config.get("injection_targets", {}).get("god_module")
    if not target:
        warnings.append({"warning": "god_module: no injection_target defined."})
        return
    if isinstance(target, tuple):
        target = target[0]

    path = dest_path / target
    if not path.exists():
        msg = f"god_module: target file not found ({target}) - skipping."
        print(f"[injector] WARNING: {msg}", file=sys.stderr)
        warnings.append({"warning": msg})
        return

    guard = "[DRIFTLENS:god_module]"
    orig = _read_file(path)
    if guard in orig:
        warnings.append({"warning": "god_module guard already present - skipping."})
        return

    addition = (
        "\n\n# [DRIFTLENS:god_module] injected - class with too many instance attributes\n"
        "class _DriftLensGodClass:  # noqa\n"
        "    def __init__(self):\n"
        "        self.attr_a = 1\n"
        "        self.attr_b = 2\n"
        "        self.attr_c = 3\n"
        "        self.attr_d = 4\n"
        "        self.attr_e = 5\n"
        "        self.attr_f = 6\n"
        "        self.attr_g = 7\n"
        "        self.attr_h = 8\n"
        "\n\n# [DRIFTLENS:god_module] injected - function with too many local variables\n"
        "def _driftlens_god_function():  # noqa\n"
        "    v1 = v2 = v3 = v4 = 0\n"
        "    v5 = v6 = v7 = v8 = 0\n"
        "    v9 = v10 = v11 = v12 = 0\n"
        "    v13 = v14 = v15 = v16 = 0\n"
        "    return (v1 + v2 + v3 + v4 + v5 + v6 + v7 + v8\n"
        "            + v9 + v10 + v11 + v12 + v13 + v14 + v15 + v16)\n"
    )

    ok = _safe_append(path, orig, addition, warnings)
    if ok:
        injections.append({
            "smell_type": "god_module",
            "files_modified": [target],
            "description": (
                f"Injected _DriftLensGodClass (8 attrs) and _driftlens_god_function"
                f" (16 locals) into {target}."
            ),
        })


def _inject_long_method(
    dest_path: Path, repo_config: dict, injections: list, warnings: list
) -> None:
    """Inject long_method: a function with ~55 statements."""
    target = repo_config.get("injection_targets", {}).get("long_method")
    if not target:
        warnings.append({"warning": "long_method: no injection_target defined."})
        return
    if isinstance(target, tuple):
        target = target[0]

    path = dest_path / target
    if not path.exists():
        msg = f"long_method: target file not found ({target}) - skipping."
        print(f"[injector] WARNING: {msg}", file=sys.stderr)
        warnings.append({"warning": msg})
        return

    guard = "[DRIFTLENS:long_method]"
    orig = _read_file(path)
    if guard in orig:
        warnings.append({"warning": "long_method guard already present - skipping."})
        return

    body_lines = [
        "\n\n# [DRIFTLENS:long_method] injected - intentionally long function\n",
        "def _driftlens_long_function():  # noqa\n",
        "    result = 0\n",
    ]
    for i in range(1, 53):
        body_lines.append(f"    step_{i:02d} = result + {i}\n")
        if i % 8 == 0:
            body_lines.append(f"    result = step_{i:02d}\n")
    body_lines.append("    return result\n")

    ok = _safe_append(path, orig, "".join(body_lines), warnings)
    if ok:
        injections.append({
            "smell_type": "long_method",
            "files_modified": [target],
            "description": f"Injected _driftlens_long_function (~55 statements) into {target}.",
        })


def _inject_poor_naming(
    dest_path: Path, repo_config: dict, injections: list, warnings: list
) -> None:
    """Inject poor_naming: function with single-character parameter and variable names."""
    target = repo_config.get("injection_targets", {}).get("poor_naming")
    if not target:
        warnings.append({"warning": "poor_naming: no injection_target defined."})
        return
    if isinstance(target, tuple):
        target = target[0]

    path = dest_path / target
    if not path.exists():
        msg = f"poor_naming: target file not found ({target}) - skipping."
        print(f"[injector] WARNING: {msg}", file=sys.stderr)
        warnings.append({"warning": msg})
        return

    guard = "[DRIFTLENS:poor_naming]"
    orig = _read_file(path)
    if guard in orig:
        warnings.append({"warning": "poor_naming guard already present - skipping."})
        return

    addition = (
        "\n\n# [DRIFTLENS:poor_naming] injected - non-descriptive single-char names\n"
        "def _driftlens_poorly_named(a, b, c, d):  # noqa\n"
        "    x = a + b\n"
        "    y = x * c\n"
        "    z = y - d\n"
        "    r = z / (a + 1) if (a + 1) != 0 else z\n"
        "    return r\n"
    )

    ok = _safe_append(path, orig, addition, warnings)
    if ok:
        injections.append({
            "smell_type": "poor_naming",
            "files_modified": [target],
            "description": (
                f"Injected _driftlens_poorly_named with single-char params/vars into {target}."
            ),
        })


def _inject_none(dest_path: Path, repo_name: str) -> dict:
    """Produce a clean (no-injection) snapshot and return the injection log."""
    return {"repo": repo_name, "severity": "none", "injections": [], "warnings": []}


def _inject_low(dest_path: Path, repo_name: str, repo_config: dict) -> dict:
    """Inject circular_import + layer_boundary_violation (Low tier)."""
    injections: list = []
    warnings: list = []
    _inject_circular_import(dest_path, repo_config, injections, warnings)
    _inject_layer_violation(dest_path, repo_config, injections, warnings)
    return {"repo": repo_name, "severity": "low", "injections": injections, "warnings": warnings}


def _inject_medium(dest_path: Path, repo_name: str, repo_config: dict) -> dict:
    """Inject Low smells + god_module (Medium tier)."""
    injections: list = []
    warnings: list = []
    _inject_circular_import(dest_path, repo_config, injections, warnings)
    _inject_layer_violation(dest_path, repo_config, injections, warnings)
    _inject_god_module(dest_path, repo_config, injections, warnings)
    return {"repo": repo_name, "severity": "medium", "injections": injections, "warnings": warnings}


def _inject_high(dest_path: Path, repo_name: str, repo_config: dict) -> dict:
    """Inject Medium smells + long_method + poor_naming (High tier)."""
    injections: list = []
    warnings: list = []
    _inject_circular_import(dest_path, repo_config, injections, warnings)
    _inject_layer_violation(dest_path, repo_config, injections, warnings)
    _inject_god_module(dest_path, repo_config, injections, warnings)
    _inject_long_method(dest_path, repo_config, injections, warnings)
    _inject_poor_naming(dest_path, repo_config, injections, warnings)
    return {"repo": repo_name, "severity": "high", "injections": injections, "warnings": warnings}


def inject_snapshot(
    package_path: Path,
    severity: str,
    dest_path: Path,
    repo_name: str,
    repo_config: dict = None,
) -> dict:
    """
    Copy package_path to dest_path and inject smells appropriate to severity.

    Returns the injection log dict (also written to dest_path/injection_log.json).
    """
    if repo_config is None:
        repo_config = REPO_CONFIGS.get(repo_name, {})

    if dest_path.exists():
        shutil.rmtree(dest_path)

    try:
        shutil.copytree(package_path, dest_path)
    except OSError as exc:
        print(f"[injector] ERROR copying tree: {exc}", file=sys.stderr)
        raise

    dispatch = {
        "none": _inject_none,
        "low": lambda d, n: _inject_low(d, n, repo_config),
        "medium": lambda d, n: _inject_medium(d, n, repo_config),
        "high": lambda d, n: _inject_high(d, n, repo_config),
    }

    if severity in dispatch:
        log = dispatch[severity](dest_path, repo_name)
    else:
        print(f"[injector] WARNING: unknown severity '{severity}'", file=sys.stderr)
        log = {
            "repo": repo_name,
            "severity": severity,
            "injections": [],
            "warnings": [{"warning": f"Unknown severity '{severity}'."}],
        }

    log_path = dest_path / "injection_log.json"
    try:
        log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"[injector] ERROR writing injection_log.json: {exc}", file=sys.stderr)

    print(
        f"[injector] {repo_name}/{severity}: {len(log['injections'])} injection(s), "
        f"{len(log['warnings'])} warning(s). Log -> {log_path}"
    )
    return log
