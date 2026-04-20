"""
config.py - Repository configurations and smell classification maps for SmellScope.
"""

REPO_CONFIGS = {
    "HRM": {
        "name": "HRM",
        "url": "https://github.com/sapientinc/HRM.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "computer-use-preview": {
        "name": "computer-use-preview",
        "url": "https://github.com/google-gemini/computer-use-preview.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "simple_GRPO": {
        "name": "simple_GRPO",
        "url": "https://github.com/lsdefine/simple_GRPO.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "wechat-decrypt": {
        "name": "wechat-decrypt",
        "url": "https://github.com/ylytdeng/wechat-decrypt.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "android-action-kernel": {
        "name": "android-action-kernel",
        "url": "https://github.com/Action-State-Labs/android-action-kernel.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "make-it-heavy": {
        "name": "make-it-heavy",
        "url": "https://github.com/Doriandarko/make-it-heavy.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "StockTradebyZ": {
        "name": "StockTradebyZ",
        "url": "https://github.com/SebastienZh/StockTradebyZ.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "notebooklm-skill": {
        "name": "notebooklm-skill",
        "url": "https://github.com/PleasePrompto/notebooklm-skill.git",
        "package_subpath": "scripts",
        "import_prefix": "scripts",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "smart-turn": {
        "name": "smart-turn",
        "url": "https://github.com/pipecat-ai/smart-turn.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "csm": {
        "name": "csm",
        "url": "https://github.com/SesameAILabs/csm.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "GRPO-Zero": {
        "name": "GRPO-Zero",
        "url": "https://github.com/policy-gradient/GRPO-Zero.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "SNI-Spoofing": {
        "name": "SNI-Spoofing",
        "url": "https://github.com/patterniha/SNI-Spoofing.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "qiaomu-anything-to-notebooklm": {
        "name": "qiaomu-anything-to-notebooklm",
        "url": "https://github.com/joeseesun/qiaomu-anything-to-notebooklm.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "intelligent-audit-system": {
        "name": "intelligent-audit-system",
        "url": "https://github.com/Ricky-7-Yan/intelligent-audit-system.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
    },
    "XiaohongshuSkills": {
        "name": "XiaohongshuSkills",
        "url": "https://github.com/white0dew/XiaohongshuSkills.git",
        "package_subpath": "scripts",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {},
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
