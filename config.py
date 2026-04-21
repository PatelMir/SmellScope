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
    "airflow": {
        "name": "airflow",
        "url": "https://github.com/apache/airflow.git",
        "package_subpath": "airflow",
        "import_prefix": "airflow",
        "install_deps": ["apache-airflow"],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import": ("models/dag.py", "models/baseoperator.py"),
            "god_module": "models/dag.py",
            "layer_violation": ("utils/helpers.py", "models/dag.py"),
            "long_method": "models/dag.py",
            "poor_naming": "models/dag.py",
        },
    },
    "deeptutor": {
        "name": "deeptutor",
        "url": "https://github.com/HKUDS/DeepTutor.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": ["torch", "numpy", "pandas"],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import": ("main.py", "model.py"),
            "god_module": "model.py",
            "layer_violation": ("utils.py", "main.py"),
            "long_method": "model.py",
            "poor_naming": "model.py",
        },
    },
    "paperless-ngx": {
        "name": "paperless-ngx",
        "url": "https://github.com/paperless-ngx/paperless-ngx.git",
        "package_subpath": "src",
        "import_prefix": "",
        "install_deps": ["django", "django-filter", "psycopg2-binary"],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import": ("documents/models.py", "documents/views.py"),
            "god_module": "documents/models.py",
            "layer_violation": ("paperless/urls.py", "documents/models.py"),
            "long_method": "documents/views.py",
            "poor_naming": "documents/views.py",
        },
    },
    "celery": {
        "name": "celery",
        "url": "https://github.com/celery/celery.git",
        "package_subpath": "celery",
        "import_prefix": "celery",
        "install_deps": ["celery", "kombu", "billiard"],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import": ("app/base.py", "app/task.py"),
            "god_module": "app/base.py",
            "layer_violation": ("utils/log.py", "app/base.py"),
            "long_method": "worker/worker.py",
            "poor_naming": "worker/worker.py",
        },
    },
    "thumbor": {
        "name": "thumbor",
        "url": "https://github.com/thumbor/thumbor.git",
        "package_subpath": "thumbor",
        "import_prefix": "thumbor",
        "install_deps": ["thumbor", "tornado", "pillow"],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import": ("app.py", "context.py"),
            "god_module": "app.py",
            "layer_violation": ("utils.py", "app.py"),
            "long_method": "handlers/__init__.py",
            "poor_naming": "handlers/__init__.py",
        },
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
