# DriftLens: Preliminary Results Report

## Overview
DriftLens evaluates LLM awareness of architectural smells in Python codebases by injecting smells at four severity levels and comparing detection rates between Gemini 3 Flash Preview and static analysis oracles (Pylint + Flake8).

**Repos evaluated:** cookiecutter, click, flask-hexagonal  
**Tiers evaluated:** None, Low, Medium, High  
**Generated:** 2026-03-29T17:15:51Z

---

## RQ1: LLM vs Oracle -- Coarse-Grained Smell Detection

Across all repos and non-baseline tiers, the static analysis oracle achieved an average coarse-grained smell recall of 77.4%, while Gemini 3 Flash Preview achieved 96.3% (gap: -18.9%). The oracle benefits from precise pattern matching on known Pylint/Flake8 codes, whereas the LLM infers smells from structural summaries alone.

| Repo | Tier | Oracle Recall | LLM Recall |
|---|---|---|---|
| cookiecutter | none | N/A | N/A |
| cookiecutter | low | 50.0% | 100.0% |
| cookiecutter | medium | 66.7% | 100.0% |
| cookiecutter | high | 40.0% | 100.0% |
| click | none | N/A | N/A |
| click | low | 100.0% | 100.0% |
| click | medium | 100.0% | 100.0% |
| click | high | 60.0% | 100.0% |
| flask-hexagonal | none | N/A | N/A |
| flask-hexagonal | low | 100.0% | 100.0% |
| flask-hexagonal | medium | 100.0% | 66.7% |
| flask-hexagonal | high | 80.0% | 100.0% |

---

## RQ2: LLM Fine-Grained vs Coarse-Grained Detection

The LLM receives only AST structural summaries (imports, function line counts, local variable counts) rather than full source code. Coarse-grained smells (circular imports, god modules, layer violations) are visible in the import graph and class/function sizes, while fine-grained smells (long methods, poor naming) require function-body analysis. This limits fine-grained recall.

| Category | LLM Recall (avg across repos and tiers) |
|---|---|
| Coarse-grained | 96.3% |
| Fine-grained | 100.0% |

---

## RQ3: LLM Detection Accuracy by Severity

As severity increases, more smells are injected, providing more signal for the LLM to detect. The table below shows average LLM recall across all repos per tier.

| Tier | Avg LLM Recall (all repos) |
|---|---|
| None | N/A (baseline) |
| Low | 100.0% |
| Medium | 88.9% |
| High | 100.0% |

---

## Limitations

The following limitations apply to these results and should be disclosed in the final report:

1. **AST summaries, not full source:** Gemini receives per-file structural summaries rather than complete source code. This may understate LLM detection capability for smells that require reading function bodies.
2. **Pre-existing baseline noise:** Cookiecutter's none tier contains pre-existing Pylint smell-relevant findings (god_module), which inflate false positive counts for the oracle at low severity.
3. **Circular import detection gap:** Injected circular imports at Low tier did not trigger Pylint R0401 (cyclic-import) because stubs are syntactically valid standalone functions. Oracle detection of circular imports relies on W0611 (unused-import) as a proxy signal.
4. **Single LLM evaluated:** Results reflect Gemini 3 Flash Preview only. Generalization to other models requires additional experiments.
5. **Small repo set:** Three repos limits statistical generalizability.
