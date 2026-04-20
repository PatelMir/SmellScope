# SmellScope

**GitHub:** https://github.com/PatelMir/SmellScope

SmellScope is a Python CLI research tool that evaluates three strategies for detecting architectural code smells in real open-source Python codebases. It injects five smell categories at four severity tiers, then compares results across: static analysis alone (Pylint + Flake8), an LLM alone (Gemini via AST summary), and LLM-assisted filtering of oracle findings. Output is precision, recall, and F1 per smell category, per severity tier, and per mode.

The experiment is evaluated across 15 Python repositories created after February 2025, selected through automated MSR-based validation using PyDriller commit metrics, Pylint baseline checks, and structural import analysis.

This project was built for CS 6356 (Software Maintenance, Evolution and Re-Engineering) at UT Dallas.

## Smell Categories

Two granularity levels are used to test whether structural context alone is sufficient for detection.

**Coarse-grained** (visible in import graph and module structure):
- `circular_import`: two modules that import from each other, creating a dependency cycle
- `god_module`: a module with an excessive number of classes, functions, or local variables
- `layer_boundary_violation`: a lower-level module importing from a higher-level module, inverting the expected dependency direction

**Fine-grained** (require reading function bodies in theory):
- `long_method`: a function with significantly more lines than its peers
- `poor_naming`: functions or variables with single-character or non-descriptive names

## Severity Tiers

| Tier | Smells injected |
|------|----------------|
| `none` | Clean copy, no injections (baseline) |
| `low` | `circular_import` + `layer_boundary_violation` |
| `medium` | Low + `god_module` |
| `high` | Medium + `long_method` + `poor_naming` |

## Detection Modes

**Mode 1 (Oracle):** Pylint and Flake8 are run on each snapshot. Findings are mapped to smell categories using a fixed code table. Ground truth is always the injection log.

**Mode 2 (LLM):** Each snapshot is summarized via Python's `ast` module and sent to Gemini. The model identifies which smell categories it believes are present. No oracle findings are shared.

**Mode 3 (LLM Judge):** Gemini reviews each oracle finding individually and classifies it as genuine or a false positive. This mode can only improve precision over Mode 1; it cannot recover oracle false negatives.

## Dataset

The 15 repositories used in the full experiment were selected from GitHub via automated MSR metrics: post-February-2025 creation date, at least 5 commits, Python ratio >= 35%, 5-20 non-test Python files, and at least one cross-module import.

**Validated (clean pass):**

| Repo | Description |
|------|-------------|
| `sapientinc/HRM` | Python-based human resource management application for employee and department tracking |
| `google-gemini/computer-use-preview` | Preview implementation of computer-use capabilities for the Gemini model |
| `lsdefine/simple_GRPO` | Minimal implementation of Group Relative Policy Optimization for fine-tuning language models |
| `ylytdeng/wechat-decrypt` | Tool for decrypting WeChat's encrypted local database files |
| `Action-State-Labs/android-action-kernel` | Android automation kernel for executing UI actions from a controller process |

**Warnings only (solo contributor):**

| Repo | Description |
|------|-------------|
| `Doriandarko/make-it-heavy` | Multi-agent orchestration framework modeled on DeepSeek's heavy-thinking reasoning approach |
| `SebastienZh/StockTradebyZ` | Automated stock trading system with configurable buy and sell signal strategies |
| `PleasePrompto/notebooklm-skill` | Claude skill for interacting with Google NotebookLM from within conversations |
| `pipecat-ai/smart-turn` | Real-time end-of-turn detection for voice AI pipelines |
| `SesameAILabs/csm` | Conversational Speech Model from Sesame AI Labs for generating natural dialogue audio |
| `policy-gradient/GRPO-Zero` | Reproduces GRPO reinforcement learning from scratch without pretrained value models |
| `patterniha/SNI-Spoofing` | Proxy tool that spoofs the TLS Server Name Indication field to bypass network filters |
| `joeseesun/qiaomu-anything-to-notebooklm` | Converts web articles, PDFs, and other content into Google NotebookLM sources |
| `Ricky-7-Yan/intelligent-audit-system` | Automated audit system for reviewing documents and flagging compliance issues |
| `white0dew/XiaohongshuSkills` | Claude skills for automating interactions with Xiaohongshu (Little Red Book) |

## Pilot Repositories

Three pre-cutoff repos were used to develop and validate the pipeline before the main experiment:

| Repo | Description | Package path |
|------|-------------|--------------|
| `cookiecutter/cookiecutter` | Mid-size project scaffolding tool | `cookiecutter/` |
| `pallets/click` | Large CLI framework | `src/click/` |
| `serfer2/flask-hexagonal-architecture-api` | Small hexagonal-architecture Flask API | `src/` |

Each repo is cloned once into `repos/` and never modified. All injections happen on isolated copies in `snapshots/`.

## Setup

**Prerequisites:** Python 3.10+, pip, a Gemini API key from [Google AI Studio](https://aistudio.google.com), and a GitHub personal access token (needed only for `repo_finder.py`).

```bash
git clone https://github.com/PatelMir/SmellScope.git
cd SmellScope
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set:
#   GEMINI_API_KEY=your_key_here
#   GITHUB_TOKEN=your_token_here
```

## Usage

```bash
# Full run: clone, inject, oracle, LLM judge, LLM, report
python main.py

# Skip cloning if repos are already present
python main.py --skip-clone

# Skip injection and oracle, re-run LLM and report only
python main.py --skip-clone --skip-inject --skip-oracle

# Regenerate report from existing results without any API calls
python main.py --report-only

# Run on a single repo at specific severity tiers
python main.py --repos cookiecutter --severity low high

# Pass the API key directly instead of via .env
python main.py --gemini-key YOUR_KEY_HERE
```

### All Flags

| Flag | Description |
|------|-------------|
| `--repos` | Space-separated list of repos to run (names from `REPO_CONFIGS` in `config.py`) |
| `--severity` | Space-separated list of tiers: `none`, `low`, `medium`, `high` |
| `--gemini-key` | Gemini API key (falls back to `GEMINI_API_KEY` env var) |
| `--skip-clone` | Skip git clone if repo directories already exist |
| `--skip-inject` | Skip injector, use existing snapshots |
| `--skip-oracle` | Skip Pylint and Flake8 runs |
| `--skip-judge` | Skip LLM judge (Mode 3) calls |
| `--skip-llm` | Skip Gemini LLM interface (Mode 2) calls |
| `--report-only` | Regenerate report from existing results only, skips all other stages |

## Output Files

After a full run, the following files are written:

```
SmellScope/
├── snapshots/
│   └── <repo>/<tier>/
│       ├── injection_log.json    # What was injected and where
│       ├── oracle_results.json   # Pylint + Flake8 findings, classified by smell type
│       ├── judge_results.json    # LLM verdicts on oracle findings (Mode 3)
│       └── llm_results.json      # Gemini detections and parse status (Mode 2)
└── output/
    ├── smellscope_report.json    # Full results with per-tier precision, recall, F1
    └── smellscope_report.md      # Human-readable Markdown report
```

## Pipeline Overview

The pipeline runs in six stages in order.

**Stage 1 (Clone):** each repo is cloned via `gitpython` into `repos/<repo_name>/`. Skipped if the directory already exists.

**Stage 2 (Inject):** for each repo and tier combination, the package directory is copied fresh to `snapshots/<repo>/<tier>/` using `shutil.copytree`. Smell code is appended to target files, guarded with `[SMELLSCOPE:<smell_type>]` comments to prevent double-injection. Each modified file is validated with `ast.parse()` and reverted if a syntax error occurs.

**Stage 3 (Oracle):** Pylint and Flake8 are run on each snapshot. Raw findings are mapped to smell types using two classification tables and written to `oracle_results.json`. E0401 findings for Windows-only modules are suppressed on non-Windows systems.

**Stage 4 (LLM Judge):** for each oracle finding, Gemini is asked to classify it as genuine or a false positive. One call per distinct smell type per snapshot. Results are skip-cached to `judge_results.json`. This is Mode 3.

**Stage 5 (LLM Interface):** each snapshot is summarized via Python's `ast` module (imports, class names, function names, line counts, local variable counts per function). The summary is capped at 12,000 characters and embedded into a structured prompt asking Gemini to identify smells and return JSON. Results are skip-cached so a failed re-run only consumes API quota for missing tiers. This is Mode 2.

**Stage 6 (Report):** all result files are read, set-based precision/recall/F1 is computed per tier for all three modes, and both `smellscope_report.json` and `smellscope_report.md` are written. Metrics use one positive per distinct smell type per snapshot, not per individual finding.

## Preliminary Results (Pilot)

These results are from the three pre-cutoff pilot repos. The full 15-repo experiment is in progress.

| Mode | Avg coarse-grained recall |
|------|--------------------------|
| Mode 1: Oracle (Pylint + Flake8) | 77.4% |
| Mode 2: LLM (Gemini) | 96.3% |

The LLM outperforms the oracle by 18.9 percentage points on the pilot set. The gap is primarily driven by circular import detection: after dependency installation, Pylint's E0401 never fires on injected cross-imports because the stubs are syntactically valid and resolve successfully. The LLM detects circular imports directly from the import list in the AST summary without needing imports to fail at runtime.

| Category | LLM Recall |
|----------|------------|
| Coarse-grained (circular_import, god_module, layer_boundary_violation) | 96.3% |
| Fine-grained (long_method, poor_naming) | 100.0% |

Fine-grained recall is likely a ceiling-effect artifact of the AST methodology. Function line counts and parameter names are directly visible in the summary, so these smells are not subtle signals for the LLM.

## Research Questions

**RQ1:** How does LLM recall (Mode 2) compare to oracle recall (Mode 1) on coarse-grained architectural smells, and does LLM-assisted filtering (Mode 3) improve oracle precision?

**RQ2:** Does the LLM detect coarse-grained smells better or worse than fine-grained smells?

**RQ3:** Does LLM detection accuracy (Mode 2 recall) increase as smell severity increases from low to high?

## Status

The SmellScope pipeline is fully implemented and validated across the three pre-cutoff pilot repositories. Fifteen post-February-2025 repositories have been selected via automated MSR-based validation using PyDriller commit analysis, static baseline checks, and import graph inspection. The full experiment is currently in progress.

## Known Limitations

**AST summaries, not full source.** Gemini receives structural summaries rather than code. This inflates fine-grained recall and may understate LLM capability for smells that require reading function bodies.

**Oracle marker-based reclassification.** Injection metadata is used to post-classify oracle findings. In a production deployment, this classification would require manual labeling rather than injection markers.

**Click baseline noise.** Click's none tier has 62 pre-existing layer boundary violation findings from F401 on `__init__.py`. Click intentionally re-exports its entire public API from `__init__.py`, which Flake8 incorrectly flags as unused imports. These are not real architectural violations.

**Circular import oracle gap.** Injected circular imports do not trigger Pylint R0401 or E0401 after dependency installation because the stubs are syntactically valid. Oracle circular import recall is effectively 0 across all tiers.

**Single LLM evaluated.** All results reflect Gemini only. Generalization to other models requires additional experiments.

**Pilot repo set.** Three pilot repositories limits statistical generalizability of the preliminary results. The 15-repo experiment is designed to address this.
