# IEPI Analytics Engine

Reference implementation of the Information Entropy Performance Indicator (IEPI) for BPMN 2.0 process models with externally specified routing probabilities.

This implementation corresponds to the formulation presented in the associated manuscript and is intended for reproducibility of the reported results.

## Version

v1.0.0 — version used in the study.

## Description

Given a predefined process structure and routing probabilities, the engine computes:

- Construct-level quantities: \(H_N(c)\), \(R(c)\), \(\kappa(c)\), \(f[c]\)
- Block-level quantities: \(U(B)\), \(R(B)\)
- Process-level IEPI score

All computations follow directly from the definitions and composition rules in the manuscript.

## Repository contents

- `metrics.py` — entropy and responsiveness
- `validation.py` — probability checks
- `composition.py` — composition rules
- `iepi_score.py` — violation terms and IEPI
- `engine.py` — execution logic
- `reproduce_results.py` — reproduces the evaluation results

## Reproducibility

Run:

```bash
python reproduce_results.py
