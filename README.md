# SmellScope

SmellScope is a Python CLI tool for evaluating how well static analysis tools and large language models detect architectural code smells. It injects five categories of code smell into open-source Python repositories at four severity tiers, then measures detection precision, recall, and F1 across three independent detection modes. Ground truth is the injection log, not human annotation.

---

## Smell Types

| Type | Category |
|---|---|
| `circular_import` | Coarse |
| `god_module` | Coarse |
| `layer_boundary_violation` | Coarse |
| `long_method` | Fine-grained |
| `poor_naming` | Fine-grained |

## Severity Tiers

| Tier | Injected smells |
|---|---|
| `none` | None (clean baseline) |
| `low` | circular_import + layer_boundary_violation |
| `medium` | low + god_module |
| `high` | medium + long_method + poor_naming |

---

## Detection Modes

**Mode 1 — Static Analysis Tools (SATs):** Runs Pylint and Flake8 on each snapshot. Findings are classified against a smell-code map defined in `config/config.py`. No LLM involved.

**Mode 2 — LLM:** Builds a structural AST summary of the snapshot (imports, classes, functions, line counts) and sends it to Gemini with a structured prompt. The model reports which of the five smell types it detects and why.

**Mode 3 — Judge:** Sends each SAT finding to Gemini one at a time and asks whether it is a genuine smell or a false positive. Only validates what Mode 1 flagged; it does not recover oracle false negatives. The goal is higher precision at the cost of recall.

---

## Requirements

- Python 3.10 or later
- Gemini API key (`GEMINI_API_KEY`)
- Git (for cloning target repositories)

Python dependencies:

```
pylint
flake8
gitpython
google-genai
python-dotenv
```

---

## Installation

```bash
git clone https://github.com/PatelMir/SmellScope.git
cd SmellScope
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here
```

---

## Running the Pipeline

Run all six stages for all repos and tiers:

```bash
python main.py
```

Run for specific repos and tiers:

```bash
python main.py --repos HRM make-it-heavy --severity low high
```

Pass the model name explicitly:

```bash
python main.py --model gemini-3.1-flash-lite-preview
```

---

## Skipping Stages

Each stage is independently skippable. Use this when rerunning after a partial failure or when iterating on a single stage.

| Flag | Skips |
|---|---|
| `--skip-clone` | Git clone |
| `--skip-inject` | Smell injection |
| `--skip-oracle` | Pylint + Flake8 |
| `--skip-judge` | LLM judge (Mode 3) |
| `--skip-llm` | LLM interface (Mode 2) |
| `--report-only` | All pipeline stages; regenerates report from existing result files |

Example: rerun only the LLM judge stage, then regenerate the report:

```bash
python main.py --skip-clone --skip-inject --skip-oracle --skip-llm
python main.py --report-only
```

The judge stage caches results per snapshot: if `judge_results.json` already exists for a given repo/tier, that snapshot is skipped automatically.

---

## Generating Charts

After running the pipeline, generate evaluation charts from `output/full_metrics.json`:

```bash
python src/generate_charts.py
```

Writes four PNGs to `output/`:

- `overall_results.png` — precision, recall, F1 per mode
- `recall_by_severity.png` — recall across tiers per mode
- `precision_by_severity.png` — precision across tiers per mode
- `f1_by_smell.png` — F1 per smell type per mode

---

## Repository Structure

```
SmellScope/
├── main.py                  # CLI entry point
├── requirements.txt
├── README.md
├── REPLICATION.md
├── .env.example
├── config/
│   ├── __init__.py          # Re-exports all config symbols
│   └── config.py            # REPO_CONFIGS, smell maps, tier/type lists
├── src/
│   ├── injector.py          # Snapshot creation and smell injection
│   ├── oracle_runner.py     # Pylint + Flake8 runner and classifier
│   ├── llm_interface.py     # AST summarizer and Gemini Mode 2 caller
│   ├── llm_judge.py         # Gemini Mode 3 per-finding validator
│   ├── reporter.py          # Precision/recall report generation
│   ├── full_metrics.py      # Standalone per-mode metrics script
│   ├── generate_charts.py   # Matplotlib chart generation
│   ├── repo_finder.py       # GitHub API search for candidate repos
│   └── repo_validator.py    # MSR-based repo validation (PyDriller)
├── data/
│   ├── candidates.json
│   ├── candidates_expanded.json
│   ├── repo_selection_log.json
│   └── repo_selection_log_expanded.json
├── output/
│   ├── smellscope_report.json
│   ├── smellscope_report.md
│   ├── full_metrics.json
│   └── *.png
├── snapshots/               # Per-repo, per-tier snapshot dirs (gitignored)
│   └── <repo>/<tier>/
│       ├── injection_log.json
│       ├── oracle_results.json
│       ├── llm_results.json
│       └── judge_results.json
└── repos/                   # Cloned source repos (gitignored)
```

---

## Repository Selection

The dataset uses 15 open-source Python repositories selected through an automated MSR validation pipeline (`src/repo_validator.py` and `src/repo_finder.py`).

**Hard criteria (failure on any one):**

- First commit date after February 1, 2025
- At least 5 commits
- Between 5 and 20 Python source files
- Python-to-total file ratio of at least 35%
- At least one inter-module import (evidence of multi-module structure)

**Soft warnings (noted but not disqualifying):**

- Single contributor
- Pre-existing smell categories detected at baseline by Pylint

Candidate repositories are sourced from the GitHub API filtered to Python, sorted by recent push date, and deduplicated before validation.
