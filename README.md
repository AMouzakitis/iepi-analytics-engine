# IEPI Analytics Engine

Reference implementation of the Information Entropy Performance Indicator (IEPI) for BPMN 2.0 process models with externally specified routing probabilities. This implementation corresponds to the formulation presented in the associated manuscript and is intended solely for reproducibility of the reported results. Version v1.0.0 is the version used in the study.

Given a predefined process structure and routing probabilities, the engine computes construct-level quantities \(H_N(c)\), \(R(c)\), \(\kappa(c)\), and \(f[c]\), propagates block-level quantities \(U(B)\) and \(R(B)\), and produces a process-level IEPI score. All computations follow directly from the definitions and composition rules in the manuscript. The implementation is fully deterministic.

The repository contains the core computation modules (metrics, validation, composition rules, and IEPI scoring), a simple execution layer, and a script (reproduce_results.py) that reproduces the results reported in the paper. Running this script yields the construct-level diagnostics, propagated quantities, and IEPI scores for the evaluation scenarios.

The engine requires as input a process structure (block representation), routing probability assignments, and threshold parameters \((H_{\min}, H_{\max}, \rho_{\min})\). Routing probabilities must be provided explicitly and are not estimated or inferred. The ordering of probabilities must correspond to the ordering of branches in the process structure.

The implementation is intentionally minimal and restricted to deterministic evaluation. It does not include BPMN parsing, probability estimation from data, or simulation and optimization features.

Apostolos Mouzakitis  
ORCID: 0009-0000-4863-7287
