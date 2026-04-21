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
        "injection_targets": {
            "circular_import":          ["pretrain.py", "puzzle_dataset.py"],
            "god_module":               ["pretrain.py"],
            "long_method":              ["models/layers.py"],
            "poor_naming":              ["models/layers.py"],
            "layer_boundary_violation": ["utils/functions.py"],
        },
    },
    "computer-use-preview": {
        "name": "computer-use-preview",
        "url": "https://github.com/google-gemini/computer-use-preview.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["agent.py", "main.py"],
            "god_module":               ["agent.py"],
            "long_method":              ["computers/playwright/playwright.py"],
            "poor_naming":              ["computers/playwright/playwright.py"],
            "layer_boundary_violation": ["computers/computer.py"],
        },
    },
    "simple_GRPO": {
        "name": "simple_GRPO",
        "url": "https://github.com/lsdefine/simple_GRPO.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["grpo_vllm_one.py", "ref_server.py"],
            "god_module":               ["Auto_Program/hjy_grpo_program.py"],
            "long_method":              ["grpo_vllm_one.py"],
            "poor_naming":              ["simple_grpo_v1/grpo_ref_split.py"],
            "layer_boundary_violation": ["ref_server.py"],
        },
    },
    "wechat-decrypt": {
        "name": "wechat-decrypt",
        "url": "https://github.com/ylytdeng/wechat-decrypt.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["decrypt_db.py", "config.py"],
            "god_module":               ["monitor_web.py"],
            "long_method":              ["mcp_server.py"],
            "poor_naming":              ["mcp_server.py"],
            "layer_boundary_violation": ["key_utils.py"],
        },
    },
    "android-action-kernel": {
        "name": "android-action-kernel",
        "url": "https://github.com/Action-State-Labs/android-action-kernel.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["config.py", "kernel.py"],
            "god_module":               ["llm_providers.py"],
            "long_method":              ["llm_providers.py"],
            "poor_naming":              ["llm_providers.py"],
            "layer_boundary_violation": ["constants.py"],
        },
    },
    "make-it-heavy": {
        "name": "make-it-heavy",
        "url": "https://github.com/Doriandarko/make-it-heavy.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["make_it_heavy.py", "orchestrator.py"],
            "god_module":               ["orchestrator.py"],
            "long_method":              ["make_it_heavy.py"],
            "poor_naming":              ["make_it_heavy.py"],
            "layer_boundary_violation": ["main.py"],
        },
    },
    "StockTradebyZ": {
        "name": "StockTradebyZ",
        "url": "https://github.com/SebastienZh/StockTradebyZ.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["pipeline/pipeline_io.py", "pipeline/schemas.py"],
            "god_module":               ["pipeline/Selector.py"],
            "long_method":              ["pipeline/Selector.py"],
            "poor_naming":              ["pipeline/Selector.py"],
            "layer_boundary_violation": ["pipeline/io.py"],
        },
    },
    "notebooklm-skill": {
        "name": "notebooklm-skill",
        "url": "https://github.com/PleasePrompto/notebooklm-skill.git",
        "package_subpath": "scripts",
        "import_prefix": "scripts",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["config.py", "browser_utils.py"],
            "god_module":               ["notebook_manager.py"],
            "long_method":              ["notebook_manager.py"],
            "poor_naming":              ["notebook_manager.py"],
            "layer_boundary_violation": ["config.py"],
        },
    },
    "smart-turn": {
        "name": "smart-turn",
        "url": "https://github.com/pipecat-ai/smart-turn.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["train_modal.py", "train.py"],
            "god_module":               ["train.py"],
            "long_method":              ["benchmark.py"],
            "poor_naming":              ["record_and_predict.py"],
            "layer_boundary_violation": ["audio_utils.py"],
        },
    },
    "csm": {
        "name": "csm",
        "url": "https://github.com/SesameAILabs/csm.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["models.py", "generator.py"],
            "god_module":               ["models.py"],
            "long_method":              ["models.py"],
            "poor_naming":              ["generator.py"],
            "layer_boundary_violation": ["generator.py"],
        },
    },
    "GRPO-Zero": {
        "name": "GRPO-Zero",
        "url": "https://github.com/policy-gradient/GRPO-Zero.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["data_types.py", "grpo.py"],
            "god_module":               ["qwen2_model.py"],
            "long_method":              ["qwen2_model.py"],
            "poor_naming":              ["qwen2_model.py"],
            "layer_boundary_violation": ["data_types.py"],
        },
    },
    "SNI-Spoofing": {
        "name": "SNI-Spoofing",
        "url": "https://github.com/patterniha/SNI-Spoofing.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["fake_tcp.py", "injecter.py"],
            "god_module":               ["main.py"],
            "long_method":              ["fake_tcp.py"],
            "poor_naming":              ["fake_tcp.py"],
            "layer_boundary_violation": ["utils/packet_templates.py"],
        },
    },
    "qiaomu-anything-to-notebooklm": {
        "name": "qiaomu-anything-to-notebooklm",
        "url": "https://github.com/joeseesun/qiaomu-anything-to-notebooklm.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["main.py", "check_env.py"],
            "god_module":               ["feishu-read-mcp/src/scraper.py"],
            "long_method":              ["feishu-read-mcp/src/scraper.py"],
            "poor_naming":              ["feishu-read-mcp/src/scraper.py"],
            "layer_boundary_violation": ["feishu-read-mcp/src/server.py"],
        },
    },
    "intelligent-audit-system": {
        "name": "intelligent-audit-system",
        "url": "https://github.com/Ricky-7-Yan/intelligent-audit-system.git",
        "package_subpath": ".",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["config.py", "start.py"],
            "god_module":               ["training/training_pipeline.py"],
            "long_method":              ["training/training_pipeline.py"],
            "poor_naming":              ["training/training_pipeline.py"],
            "layer_boundary_violation": ["config.py"],
        },
    },
    "XiaohongshuSkills": {
        "name": "XiaohongshuSkills",
        "url": "https://github.com/white0dew/XiaohongshuSkills.git",
        "package_subpath": "scripts",
        "import_prefix": "",
        "install_deps": [],
        "platform_suppress_modules": [],
        "injection_targets": {
            "circular_import":          ["chrome_launcher.py", "account_manager.py"],
            "god_module":               ["cdp_publish.py"],
            "long_method":              ["cdp_publish.py"],
            "poor_naming":              ["cdp_publish.py"],
            "layer_boundary_violation": ["feed_explorer.py"],
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
