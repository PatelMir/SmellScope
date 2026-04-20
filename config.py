"""
config.py - Repository configurations and smell classification maps for SmellScope.
"""

REPO_CONFIGS = {
    "cookiecutter": {
        "name": "cookiecutter",
        "url": "https://github.com/cookiecutter/cookiecutter.git",
        "package_subpath": "cookiecutter",
        "import_prefix": "cookiecutter",
        "install_deps": [
            "cookiecutter",
            "jinja2",
            "binaryornot",
            "rich",
            "arrow",
            "python-slugify",
        ],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import": ("main.py", "generate.py"),
            "god_module": "main.py",
            "layer_violation": ("utils.py", "main.py"),
            "long_method": "generate.py",
            "poor_naming": "generate.py",
        },
    },
    "click": {
        "name": "click",
        "url": "https://github.com/pallets/click.git",
        "package_subpath": "src/click",
        "import_prefix": "click",
        "install_deps": ["click"],
        # msvcrt, winreg, _winapi, _winreg are Windows-only guards that always
        # produce E0401 on non-Windows systems.
        "platform_suppress_modules": ["msvcrt", "winreg", "_winapi", "_winreg"],
        "injection_targets": {
            "circular_import": ("decorators.py", "core.py"),
            "god_module": "core.py",
            "layer_violation": ("utils.py", "core.py"),
            "long_method": "core.py",
            "poor_naming": "core.py",
        },
    },
    "flask-hexagonal": {
        "name": "flask-hexagonal",
        "url": "https://github.com/serfer2/flask-hexagonal-architecture-api.git",
        "package_subpath": "src",
        "import_prefix": "",
        "install_deps": ["flask", "sqlalchemy"],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import": (
                "application/services/anonymize_txt_file.py",
                "controller/app.py",
            ),
            "god_module": "controller/app.py",
            "layer_violation": ("domain/models/report.py", "controller/app.py"),
            "long_method": "controller/app.py",
            "poor_naming": "controller/app.py",
        },
    },
}

SEVERITY_TIERS = ["none", "low", "medium", "high"]

SMELL_TYPES = [
    "circular_import",
    "god_module",
    "layer_boundary_violation",
    "long_method",
    "poor_naming",
]

PYLINT_SMELL_MAP = {
    "R0914": "god_module",               # too-many-locals
    "R0912": "god_module",               # too-many-branches
    "R0915": "god_module",               # too-many-statements
    "R0902": "god_module",               # too-many-instance-attributes
    "E0401": "circular_import",          # import-error (post-injection only)
    "R0401": "circular_import",          # cyclic-import
    "C0301": "long_method",              # line-too-long (disabled by --disable=C)
    "W0611": "layer_boundary_violation", # unused-import (when injected)
}

# E501 (line-too-long) is intentionally excluded: it fires on pre-existing lines in
# real codebases and makes baseline counts uninterpretable. Long method smell is
# instead detectable via AST function line counts in the LLM summary.
FLAKE8_SMELL_MAP = {
    "F401": "layer_boundary_violation", # imported but unused
    "F811": "circular_import",          # redefinition of unused name
    "W605": "poor_naming",              # invalid escape sequence
    "E722": "god_module",               # bare except
}
