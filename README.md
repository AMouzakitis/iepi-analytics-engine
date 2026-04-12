## The Information Entropy Performance Indicator (IEPI)
### A Deterministic Analytics Engine for Quantifying Routing Uncertainty in BPMN Process Models

This repository contains a reference implementation of the Information Entropy Performance Indicator (IEPI) for BPMN 2.0 process models with externally defined routing probabilities. The objective is to provide a clear and reproducible implementation of what is described in the paper. Given a process structure and a set of routing probabilities, the engine computes: construct-level diagnostics, block-level uncertainty propagation, and a process-level IEPI score. Everything is deterministic and follows directly from the definitions and rules in the submitted manuscript.

Computation

The implementation operates across three levels: Construct Level, Block Level, and Process Level

1. Construct Level: For each routing construct c, the engine computes: i) Normalized entropy H_N(c); ii) Responsiveness R(c); iii) Viability classification κ(c); iv) Diagnostic flags f[c]. These quantities describe the local uncertainty and structural properties of each routing point.
2. Block Level: Uncertainty is propagated through the process structure using the composition rules. This produces: i) U(B): propagated uncertainty of the block; ii) R(B): a descriptive responsiveness summary of the block. Note that R(B) is descriptive only and is not used in IEPI scoring.
3. Process Level: The final IEPI score is computed over all constructs as: IEPI = 1 / (1 + average(V(c))),where V(c ) represents the violation of entropy and responsiveness constraints.

Repository Structure

metrics.py              - entropy and responsiveness functions  
validation.py           - probability checks and diagnostic flags  
composition.py          - SEQ, XOR, OR, LOOP composition rules  
iepi_score.py           - violation computation and IEPI score  
engine.py               - main orchestration logic  
reproduce_results.py    - script to reproduce the paper results  

To reproduce the results from the paper, run: python reproduce_results.py. This will output: i) Construct-level diagnostics; ii) Propagated uncertainty values;
iii) IEPI scores for Scenario A and Scenario B

As an input, the engine expects:

1. A process structure (as a nested block dictionary)
2. A mapping from routing constructs to probability vectors
3. Threshold values: (H_min, H_max, rho_min)

However, the routing probabilities must be provided explicitly as the implementation does NOT estimate or infer them.

Note that: i) The order of probabilities must match the order of branches in the process structure; ii) R(B) values are descriptive and are not used in IEPI scoring; iii) The implementation is fully deterministic, meaning that the same inputs always produce the same outputs.

Regarding the Scope: This is a minimal reference implementation designed for reproducibility, clarity, and alignment with the academic formulation.
It does NOT include: i) BPMN XML parsing; ii) Probability estimation from data; iii) Optimization or simulation features.

Author: Apostolos Mouzakitis (ORCID: 0009-0000-4863-7287), PhD Candidate, University of Greater Manchester (formerly University of Bolton), UK; New York College, Athens, Greece; Correspondence: amouzakitis@nyc.gr
