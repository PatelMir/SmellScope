# DriftLens

DriftLens is a Python CLI research tool that evaluates whether a large language model can detect architectural smells in real open-source Python codebases as accurately as traditional static analysis tools. It injects smells at four severity levels, runs Pylint and Flake8 as ground-truth oracles, queries Gemini through its API, and outputs a structured comparison report with precision, recall, and F1 scores per tier.

This project was built for CS 6356 (Software Maintenance, Evolution & Re-Engineering) at UT Dallas.

---

## Repositories Evaluated

Three open-source Python projects were selected to cover a range of sizes and architectural styles.

| Repo | Description | Package path |
|------|-------------|--------------|
| `cookiecutter/cookiecutter` | Mid-size project scaffolding tool | `cookiecutter/` |
| `pallets/click` | Large CLI framework | `src/click/` |
| `serfer2/flask-hexagonal-architecture-api` | Small hexagonal-architecture Flask API | `src/` |

Each repo is cloned once into `repos/` and never modified. All injections happen on isolated copies in `snapshots/`.

---

## Smell Types

Two granularity levels are used to test whether AST-level structural context is sufficient for detection.

**Coarse-grained** (visible in import graph and module structure):
- `circular_import`: two modules that import from each other, creating a dependency cycle
- `god_module`: a module with an excessive number of classes, functions, or local variables
- `layer_boundary_violation`: a lower-level module importing from a higher-level module, inverting the expected dependency direction

**Fine-grained** (require function-body reading in theory):
- `long_method`: a function with significantly more lines than its peers
- `poor_naming`: functions or variables with single-character or non-descriptive names

---

## Severity Tiers

| Tier | Smells injected |
|------|----------------|
| `none` | Clean copy, no injections (baseline) |
| `low` | `circular_import` + `layer_boundary_violation` |
| `medium` | Low + `god_module` |
| `high` | Medium + `long_method` + `poor_naming` |

---

## Prerequisites

- Python 3.10+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com)
- pip

---

## Installation

```bash
git clone https://github.com/PatelMir/DriftLens.git
cd driftlens
pip install -r requirements.txt
cp .env.example .env
# Open .env and set GEMINI_API_KEY=your_key_here
```

---

## Usage

```bash
# Full run: clone, inject, oracle, LLM, report
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
| `--repos` | Space-separated list of repos to run (`cookiecutter`, `click`, `flask-hexagonal`, or `all`) |
| `--severity` | Space-separated list of tiers (`none`, `low`, `medium`, `high`, or `all`) |
| `--gemini-key` | Gemini API key (falls back to `GEMINI_API_KEY` env var) |
| `--skip-clone` | Skip git clone if repo directories already exist |
| `--skip-inject` | Skip injector, use existing snapshots |
| `--skip-oracle` | Skip Pylint and Flake8 runs |
| `--skip-llm` | Skip Gemini API calls |
| `--report-only` | Regenerate report from existing results only |

---

## Output Files

After a full run, the following files are written:

```
driftlens/
├── snapshots/
│   └── <repo>/<tier>/
│       ├── injection_log.json    # What was injected and where
│       ├── oracle_results.json   # Pylint + Flake8 findings, classified by smell type
│       └── llm_results.json      # Gemini detections and parse status
└── output/
    ├── driftlens_report.json     # Full results with per-tier precision, recall, F1
    ├── driftlens_report.md       # Human-readable Markdown report
    └── audit_report.txt          # Six-check methodological audit (if run)
```

---

## Pipeline Overview

The pipeline runs in five stages in order.

**Stage 1 (Clone):** each repo is cloned via `gitpython` into `repos/<repo_name>/`. Skipped if the directory already exists.

**Stage 2 (Inject):** for each repo and tier combination, the package directory is copied fresh to `snapshots/<repo>/<tier>/` using `shutil.copytree`. Smell code is appended to target files, guarded with `[DRIFTLENS:<smell_type>]` comments to prevent double-injection. Each modified file is validated with `ast.parse()` and reverted if a syntax error occurs.

**Stage 3 (Oracle):** Pylint and Flake8 are run on each snapshot. Raw findings are mapped to smell types using two classification tables and written to `oracle_results.json`. E0401 findings for Windows-only modules are suppressed on non-Windows systems.

**Stage 4 (LLM Interface):** each snapshot is summarized via Python's `ast` module (imports, class names, function names, line counts, local variable counts per function). The summary is capped at 12,000 characters and embedded into a structured prompt asking Gemini to identify smells and return JSON. Results are skip-cached so a failed re-run only consumes API quota for missing tiers.

**Stage 5 (Report):** all result files are read, set-based precision/recall/F1 is computed per tier, and both `driftlens_report.json` and `driftlens_report.md` are written. Metrics use one positive per distinct smell type per snapshot, not per individual finding.

---

## Results Summary

| Tool | Avg recall (low/medium/high tiers) |
|------|------------------------------------|
| Oracle (Pylint + Flake8) | 77.4% |
| LLM (Gemini) | 96.3% |

The LLM outperforms the oracle by 18.9 percentage points. The gap is primarily driven by circular import detection: after dependency installation, Pylint's E0401 never fires on injected cross-imports because the stubs are syntactically valid and resolve successfully. The LLM detects circular imports directly from the import list in the AST summary without needing imports to fail at runtime.

| Category | LLM Recall |
|----------|------------|
| Coarse-grained (circular_import, god_module, layer_boundary_violation) | 96.3% |
| Fine-grained (long_method, poor_naming) | 100.0% |

Note: fine-grained recall is likely a ceiling-effect artifact of the AST methodology. Function line counts and parameter names are directly visible in the summary, so these smells are not subtle signals for the LLM.

---

## Known Limitations

**AST summaries, not full source.** Gemini receives structural summaries rather than code. This inflates fine-grained recall and may understate LLM capability for smells that require reading function bodies.

**Oracle marker-based reclassification.** Injection metadata is used to post-classify oracle findings. In a production deployment, this classification would require manual labeling rather than injection markers.

**Click baseline noise.** Click's none tier has 62 pre-existing layer boundary violation findings from F401 on `__init__.py`. Click intentionally re-exports its entire public API from `__init__.py`, which Flake8 incorrectly flags as unused imports. These are not real architectural violations.

**Circular import oracle gap.** Injected circular imports do not trigger Pylint R0401 or E0401 after dependency installation because the stubs are syntactically valid. Oracle circular import recall is effectively 0 across all tiers.

**Single LLM evaluated.** All results reflect Gemini only. Generalization to other models requires additional experiments.

**Small repo set.** Three repositories limits statistical generalizability. Results are preliminary.

---

## Research Questions

- **RQ1:** How does LLM recall compare to oracle recall on coarse-grained architectural smells?
- **RQ2:** Does the LLM detect coarse-grained smells better or worse than fine-grained smells?
- **RQ3:** Does LLM detection accuracy increase as smell severity increases?