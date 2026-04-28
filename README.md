# IEPI Analytics Engine

## Overview

This repository provides the reference implementation of the **Information Entropy Performance Indicator (IEPI)** for BPMN 2.0 process models with externally specified routing probabilities.

The implementation corresponds to the analytical formulation presented in the associated research paper and is designed for **clarity, reproducibility, and deterministic evaluation**.

Given a process structure and a set of routing probabilities, the engine computes:

- Construct-level diagnostics  
- Block-level uncertainty propagation  
- Process-level IEPI score  

All outputs are deterministic functions of the provided inputs.

---

## Version

**v1.0.0** — Reference implementation corresponding to the published study.

---

## Computation Framework

The implementation operates across three analytical levels:

### Construct Level
For each routing construct \(c\), the engine computes:
- Normalized entropy \(H_N(c)\)
- Responsiveness \(R(c)\)
- Viability classification \(\kappa(c)\)
- Diagnostic flags \(f[c]\)

These quantities describe the local uncertainty and structural properties of each routing construct.

---

### Block Level
Uncertainty is propagated through the process structure using the composition rules:

- \(U(B)\): propagated uncertainty of the block  
- \(R(B)\): descriptive responsiveness summary  

**Note:** \(R(B)\) is descriptive only and does not participate in IEPI scoring.

---

### Process Level
The IEPI score is computed as:

\[
\mathrm{IEPI} = \frac{1}{1 + \overline{V}}
\]

where \(\overline{V}\) is the average violation across routing constructs.

---

## Repository Structure

- `metrics.py` — entropy and responsiveness functions  
- `validation.py` — probability checks and diagnostic flags  
- `composition.py` — SEQ, XOR, OR, LOOP composition rules  
- `iepi_score.py` — violation computation and IEPI aggregation  
- `engine.py` — main orchestration logic  
- `reproduce_results.py` — script to reproduce paper results  

---

## Reproducibility

To reproduce the results reported in the paper, run:

```bash
python reproduce_results.py
