# SmellScope: Preliminary Results Report

## Overview
SmellScope evaluates LLM awareness of architectural smells in Python codebases by injecting smells at four severity levels and comparing detection rates between Gemini 3 Flash Preview and static analysis oracles (Pylint + Flake8).

**Repos evaluated:** cookiecutter, click, flask-hexagonal  
**Tiers evaluated:** None, Low, Medium, High  
**Generated:** 2026-04-21T05:07:26Z

---

## RQ1: LLM vs Oracle -- Coarse-Grained Smell Detection

Across all repos and non-baseline tiers, the static analysis oracle achieved an average coarse-grained smell recall of 86.7%, while Gemini 3 Flash Preview achieved 20.0% (gap: 66.7%). Mode 3 (LLM judge) achieved a recall of 86.7% and a precision of 88.9% by filtering oracle findings. The oracle benefits from precise pattern matching on known Pylint/Flake8 codes, whereas the LLM infers smells from structural summaries alone.

| Repo | Tier | Oracle Recall | LLM Recall | Judge Precision | Judge Recall |
|---|---|---|---|---|---|
| HRM | none | N/A | N/A | N/A | N/A |
| HRM | low | N/A | N/A | N/A | N/A |
| HRM | medium | N/A | N/A | N/A | N/A |
| HRM | high | N/A | N/A | N/A | N/A |
| computer-use-preview | none | N/A | N/A | N/A | N/A |
| computer-use-preview | low | N/A | N/A | N/A | N/A |
| computer-use-preview | medium | N/A | N/A | N/A | N/A |
| computer-use-preview | high | N/A | N/A | N/A | N/A |
| simple_GRPO | none | N/A | N/A | N/A | N/A |
| simple_GRPO | low | N/A | N/A | N/A | N/A |
| simple_GRPO | medium | N/A | N/A | N/A | N/A |
| simple_GRPO | high | N/A | N/A | N/A | N/A |
| wechat-decrypt | none | N/A | N/A | N/A | N/A |
| wechat-decrypt | low | N/A | N/A | N/A | N/A |
| wechat-decrypt | medium | N/A | N/A | N/A | N/A |
| wechat-decrypt | high | N/A | N/A | N/A | N/A |
| android-action-kernel | none | N/A | N/A | N/A | N/A |
| android-action-kernel | low | N/A | N/A | N/A | N/A |
| android-action-kernel | medium | N/A | N/A | N/A | N/A |
| android-action-kernel | high | N/A | N/A | N/A | N/A |
| make-it-heavy | none | N/A | N/A | N/A | N/A |
| make-it-heavy | low | N/A | N/A | N/A | N/A |
| make-it-heavy | medium | N/A | N/A | N/A | N/A |
| make-it-heavy | high | N/A | N/A | N/A | N/A |
| StockTradebyZ | none | N/A | N/A | N/A | N/A |
| StockTradebyZ | low | N/A | N/A | N/A | N/A |
| StockTradebyZ | medium | N/A | N/A | N/A | N/A |
| StockTradebyZ | high | N/A | N/A | N/A | N/A |
| notebooklm-skill | none | N/A | N/A | N/A | N/A |
| notebooklm-skill | low | N/A | N/A | N/A | N/A |
| notebooklm-skill | medium | N/A | N/A | N/A | N/A |
| notebooklm-skill | high | N/A | N/A | N/A | N/A |
| smart-turn | none | N/A | N/A | N/A | N/A |
| smart-turn | low | N/A | N/A | N/A | N/A |
| smart-turn | medium | N/A | N/A | N/A | N/A |
| smart-turn | high | N/A | N/A | N/A | N/A |
| csm | none | N/A | N/A | N/A | N/A |
| csm | low | N/A | N/A | N/A | N/A |
| csm | medium | N/A | N/A | N/A | N/A |
| csm | high | N/A | N/A | N/A | N/A |
| GRPO-Zero | none | N/A | N/A | N/A | N/A |
| GRPO-Zero | low | N/A | N/A | N/A | N/A |
| GRPO-Zero | medium | N/A | N/A | N/A | N/A |
| GRPO-Zero | high | N/A | N/A | N/A | N/A |
| SNI-Spoofing | none | N/A | N/A | N/A | N/A |
| SNI-Spoofing | low | N/A | N/A | N/A | N/A |
| SNI-Spoofing | medium | N/A | N/A | N/A | N/A |
| SNI-Spoofing | high | N/A | N/A | N/A | N/A |
| qiaomu-anything-to-notebooklm | none | N/A | N/A | N/A | N/A |
| qiaomu-anything-to-notebooklm | low | N/A | N/A | N/A | N/A |
| qiaomu-anything-to-notebooklm | medium | N/A | N/A | N/A | N/A |
| qiaomu-anything-to-notebooklm | high | N/A | N/A | N/A | N/A |
| intelligent-audit-system | none | N/A | N/A | N/A | N/A |
| intelligent-audit-system | low | N/A | N/A | N/A | N/A |
| intelligent-audit-system | medium | N/A | N/A | N/A | N/A |
| intelligent-audit-system | high | N/A | N/A | N/A | N/A |
| airflow | none | N/A | N/A | N/A | N/A |
| airflow | low | N/A | N/A | N/A | N/A |
| airflow | medium | N/A | N/A | N/A | N/A |
| airflow | high | N/A | N/A | N/A | N/A |
| deeptutor | none | N/A | N/A | N/A | N/A |
| deeptutor | low | N/A | N/A | N/A | N/A |
| deeptutor | medium | N/A | N/A | N/A | N/A |
| deeptutor | high | N/A | N/A | N/A | N/A |
| paperless-ngx | none | N/A | N/A | N/A | N/A |
| paperless-ngx | low | 100.0% | 0.0% | 66.7% | 100.0% |
| paperless-ngx | medium | 100.0% | 0.0% | 100.0% | 100.0% |
| paperless-ngx | high | 60.0% | 0.0% | 100.0% | 60.0% |
| celery | none | N/A | N/A | N/A | N/A |
| celery | low | 100.0% | 0.0% | 66.7% | 100.0% |
| celery | medium | 100.0% | 0.0% | 100.0% | 100.0% |
| celery | high | 60.0% | 80.0% | 100.0% | 60.0% |
| thumbor | none | N/A | N/A | N/A | N/A |
| thumbor | low | 100.0% | 0.0% | 66.7% | 100.0% |
| thumbor | medium | 100.0% | 100.0% | 100.0% | 100.0% |
| thumbor | high | 60.0% | 0.0% | 100.0% | 60.0% |
| XiaohongshuSkills | none | N/A | N/A | N/A | N/A |
| XiaohongshuSkills | low | N/A | N/A | N/A | N/A |
| XiaohongshuSkills | medium | N/A | N/A | N/A | N/A |
| XiaohongshuSkills | high | N/A | N/A | N/A | N/A |

---

## RQ2: LLM Fine-Grained vs Coarse-Grained Detection

The LLM receives only AST structural summaries (imports, function line counts, local variable counts) rather than full source code. Coarse-grained smells (circular imports, god modules, layer violations) are visible in the import graph and class/function sizes, while fine-grained smells (long methods, poor naming) require function-body analysis. This limits fine-grained recall.

| Category | LLM Recall (avg across repos and tiers) |
|---|---|
| Coarse-grained | 18.5% |
| Fine-grained | 33.3% |

---

## RQ3: LLM Detection Accuracy by Severity

As severity increases, more smells are injected, providing more signal for the LLM to detect. The table below shows average LLM recall across all repos per tier.

| Tier | Avg LLM Recall (all repos) |
|---|---|
| None | N/A (baseline) |
| Low | 0.0% |
| Medium | 33.3% |
| High | 26.7% |

---

## Limitations

The following limitations apply to these results and should be disclosed in the final report:

1. **AST summaries, not full source:** Gemini receives per-file structural summaries rather than complete source code. This may understate LLM detection capability for smells that require reading function bodies.
2. **Pre-existing baseline noise:** Cookiecutter's none tier contains pre-existing Pylint smell-relevant findings (god_module), which inflate false positive counts for the oracle at low severity.
3. **Circular import detection gap:** Injected circular imports at Low tier did not trigger Pylint R0401 (cyclic-import) because stubs are syntactically valid standalone functions. Oracle detection of circular imports relies on W0611 (unused-import) as a proxy signal.
4. **Single LLM evaluated:** Results reflect Gemini 3 Flash Preview only. Generalization to other models requires additional experiments.
5. **Small repo set:** Three repos limits statistical generalizability.
