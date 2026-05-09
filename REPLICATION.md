# Replication Guide

This document describes the exact setup used to produce the SmellScope results and provides step-by-step commands to reproduce them from scratch.

---

## Experiment Configuration

| Parameter | Value |
|---|---|
| Repositories | 15 |
| Smell types | 5 |
| Severity tiers | 4 (none, low, medium, high) |
| Snapshots | 60 (15 repos × 4 tiers) |
| LLM model | `gemini-3.1-flash-lite-preview` |
| LLM inter-call delay | 4 seconds (Mode 2), none (Mode 3) |
| Rate-limit backoff | Exponential: 10s, 20s, 40s on 429 or 503 |
| Metrics | Set-based TP/FP/FN per distinct smell type per snapshot |

### Repositories

```
HRM                             computer-use-preview
simple_GRPO                     wechat-decrypt
android-action-kernel           make-it-heavy
StockTradebyZ                   notebooklm-skill
smart-turn                      csm
GRPO-Zero                       SNI-Spoofing
qiaomu-anything-to-notebooklm   intelligent-audit-system
XiaohongshuSkills
```

All repositories have a first commit date after February 1, 2025. Clone URLs are in `config/config.py` under `REPO_CONFIGS`.

---

## Prerequisites

```bash
python --version   # 3.10 or later required
pip install -r requirements.txt
```

Set your Gemini API key:

```bash
cp .env.example .env
# Add: GEMINI_API_KEY=your_key_here
```

---

## Step-by-Step Reproduction

### Step 1: Clone all 15 repositories

```bash
python main.py --skip-inject --skip-oracle --skip-judge --skip-llm
```

Clones land in `repos/`. This step requires internet access and takes several minutes. The reporter runs at the end and produces empty output — that is expected at this stage.

### Step 2: Inject smells into all snapshots

```bash
python main.py --skip-clone --skip-oracle --skip-judge --skip-llm
```

Creates 60 snapshot directories under `snapshots/<repo>/<tier>/`. Each directory contains the injected source and `injection_log.json`.

### Step 3: Run static analysis (Mode 1)

```bash
python main.py --skip-clone --skip-inject --skip-judge --skip-llm
```

Runs Pylint (`--disable=C --enable=E,W,R`) and Flake8 on each snapshot. Writes `oracle_results.json` per snapshot.

### Step 4: Run LLM judge (Mode 3)

```bash
python main.py --skip-clone --skip-inject --skip-oracle --skip-llm --model gemini-3.1-flash-lite-preview
```

Sends one Gemini request per distinct smell type found by the oracle in each snapshot. Writes `judge_results.json` per snapshot. Skips snapshots where `judge_results.json` already exists.

### Step 5: Run LLM interface (Mode 2)

```bash
python main.py --skip-clone --skip-inject --skip-oracle --skip-judge --model gemini-3.1-flash-lite-preview
```

Builds an AST structural summary of each snapshot and sends one request to Gemini. Applies a 4-second inter-call delay. Writes `llm_results.json` per snapshot. Skips snapshots with existing successful results.

### Step 6: Generate the report

```bash
python main.py --report-only
```

Reads all result JSON files and writes:

- `output/smellscope_report.json`
- `output/smellscope_report.md`
- `output/full_metrics.json`

### Step 7: Generate charts

```bash
python src/generate_charts.py
```

Reads `output/full_metrics.json` and writes four PNG files to `output/`.

### Full pipeline (single command)

To run all steps in sequence with no caching:

```bash
python main.py --model gemini-3.1-flash-lite-preview
```

Expect runtime of 30+ minutes depending on API latency and rate limits.

---

## Expected Output Files

After full reproduction, `output/` contains:

| File | Description |
|---|---|
| `smellscope_report.json` | Per-repo, per-tier detection results for all three modes |
| `smellscope_report.md` | Human-readable Markdown summary with RQ tables |
| `full_metrics.json` | TP, FP, FN, precision, recall, F1 aggregated four ways per mode |
| `overall_results.png` | Grouped bar chart: precision/recall/F1 per mode |
| `recall_by_severity.png` | Line chart: recall across tiers per mode |
| `precision_by_severity.png` | Line chart: precision across tiers per mode |
| `f1_by_smell.png` | Grouped bar chart: F1 per smell type per mode |

---

## Verifying Results Against full_metrics.json

Run `src/full_metrics.py` standalone to recompute metrics from the stored result files and print a formatted table:

```bash
python src/full_metrics.py
```

Expected overall results:

| Mode | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Mode 1 Oracle | 135 | 33 | 15 | 80.4% | 90.0% | 84.9% |
| Mode 2 LLM | 150 | 58 | 0 | 72.1% | 100.0% | 83.8% |
| Mode 3 Judge | 74 | 15 | 76 | 83.2% | 49.3% | 61.9% |

Per-tier precision and recall:

| Tier | Oracle P | Oracle R | LLM P | LLM R | Judge P | Judge R |
|---|---|---|---|---|---|---|
| low | 55.6% | 100.0% | 46.9% | 100.0% | 50.0% | 50.0% |
| medium | 83.3% | 100.0% | 65.2% | 100.0% | 100.0% | 62.2% |
| high | 100.0% | 80.0% | 100.0% | 100.0% | 100.0% | 41.3% |

Per-smell recall:

| Smell | Oracle | LLM | Judge |
|---|---|---|---|
| circular_import | 100% | 100% | 20% |
| god_module | 100% | 100% | 96.7% |
| layer_boundary_violation | 100% | 100% | 80% |
| long_method | 100% | 100% | 0% |
| poor_naming | 0% | 100% | 0% |

If your numbers differ from these, check that all 60 `judge_results.json` and `llm_results.json` files exist and have no `parse_error: true` entries before filing a discrepancy.

---

## Known Threats to Validity

**Single model and version.** All LLM results come from `gemini-3.1-flash-lite-preview`. Results may not generalize to other models, providers, or future versions of the same model.

**Injection-based ground truth.** The ground truth is the injection log, not independent human review. The tool measures whether detectors find what was injected, not whether they find real smells in the wild. Injected code is synthetic and may be easier or harder to detect than naturally occurring smells.

**Pre-existing baseline contamination.** Nine of the 15 repositories have pre-existing Pylint findings that match the smell-code map at the `none` (clean) tier. For coarse smells, this means both the oracle and the LLM detect smells that were present before injection. The set-based metric cannot distinguish a TP caused by injection from a TP caused by a pre-existing smell of the same type. This inflates recall for coarse smells across all modes and tiers.

**Oracle limitations for fine-grained smells.** The oracle achieves 0% recall on `poor_naming` because Pylint 4.x accepts single-character names under the default `snake_case` naming style (no minimum length enforced), and all C-category codes are disabled by the `--disable=C` flag. The injected `poor_naming` function is syntactically valid under Pylint's rules, so no finding is ever produced.

**LLM prompt sensitivity.** Mode 2 and Mode 3 results depend on the exact prompt templates in `src/llm_interface.py` and `src/llm_judge.py`. Small wording changes may alter verdicts, especially for borderline cases like `circular_import`, where Mode 3 achieves only 20% recall because Gemini frequently classifies the injected `E0401` findings as false positives (missing dependency rather than circular import).

**Dataset size.** Fifteen repositories and 60 snapshots is a small sample. Per-repo coarse metrics are stable because all repos produce the same structural pattern, but per-smell fine-grained results (especially `poor_naming` and `long_method` in Mode 3) have high variance and limited generalizability.
