# iepi-analytics-engine

OVERVIEW

This repository contains a reference implementation of the Information Entropy Performance Indicator (IEPI) for BPMN 2.0 process models with externally defined routing probabilities.

The objective is to provide a clear and reproducible implementation of what is described in the paper. Given a process structure and a set of routing probabilities, the engine computes: construct-level diagnostics, block-level uncertainty propagation, and a process-level IEPI score.

Everything is deterministic and follows directly from the definitions and rules in the submitted manuscript.

--------------------------------------------------

WHAT THE ENGINE COMPUTES

The implementation operates across three levels:

1. CONSTRUCT LEVEL

For each routing construct c, the engine computes:

- Normalized entropy H_N(c)
- Responsiveness R(c)
- Viability classification κ(c)
- Diagnostic flags f[c]

These quantities describe the local uncertainty and structural properties of each routing point.

--------------------------------------------------

2. BLOCK LEVEL

Uncertainty is propagated through the process structure using the composition rules.

This produces:

- U(B): propagated uncertainty of the block
- R(B): a descriptive responsiveness summary of the block

Note:
R(B) is descriptive only and is not used in IEPI scoring.

--------------------------------------------------

3. PROCESS LEVEL

The final IEPI score is computed over all constructs:

IEPI = 1 / (1 + average(V(c)))

where V(c) represents the violation of entropy and responsiveness constraints.

--------------------------------------------------

REPOSITORY STRUCTURE

metrics.py              - entropy and responsiveness functions  
validation.py           - probability checks and diagnostic flags  
composition.py          - SEQ, XOR, OR, LOOP composition rules  
iepi_score.py           - violation computation and IEPI score  
engine.py               - main orchestration logic  
reproduce_results.py    - script to reproduce the paper results  

--------------------------------------------------

RUNNING THE EXAMPLE

To reproduce the results from the paper, run:

python reproduce_results.py

This will output:

- Construct-level diagnostics
- Propagated uncertainty values
- IEPI scores for Scenario A and Scenario B

--------------------------------------------------

INPUTS

The engine expects:

1. A process structure (as a nested block dictionary)
2. A mapping from routing constructs to probability vectors
3. Threshold values:
   (H_min, H_max, rho_min)

Important:
- Routing probabilities must be provided explicitly
- The implementation does NOT estimate or infer them

--------------------------------------------------

IMPORTANT NOTES

- The order of probabilities must match the order of branches in the process structure
- R(B) values are descriptive and are not used in IEPI scoring
- The implementation is fully deterministic:
  same inputs always produce the same outputs

--------------------------------------------------

SCOPE

This is a minimal reference implementation designed for:

- Reproducibility
- Clarity
- Alignment with the academic formulation

It does NOT include:

- BPMN XML parsing
- Probability estimation from data
- Optimization or simulation features
