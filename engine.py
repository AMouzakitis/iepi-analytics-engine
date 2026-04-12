"""
engine.py

Orchestrator for the IEPI reference implementation.

Responsibilities
----------------
- Validate routing probability inputs
- Compute per-construct diagnostics:
    Π[c] = (H_N(c), R(c), κ(c), f[c])
- Evaluate block-level quantities:
    U(B), R(B)
- Compute process-level IEPI:
    IEPI = 1 / (1 + average(V(c))) over C_valid

Design
------
This is a deterministic reference implementation for reproducibility.
It does not perform:
- inference
- optimization
- simulation
- parameter tuning

Supported block types
---------------------
1. leaf
   Deterministic terminal block:
       U = 0
       R = 0

2. seq
   Sequential composition:
       U = Σ U(child_i)
       R = Σ R(child_i)

3. and
   Parallel composition under the same IEPI rule as seq:
       U = Σ U(child_i)
       R = Σ R(child_i)

4. xor
   Exclusive routing composition:
       U = H(p) + Σ p_i U(child_i)
       R = 1 - Σ p_i^2

5. or
   Inclusive routing composition:
       U = H2(p) + Σ p_i U(child_i)
       R = 1 - Σ p_i^2

6. loop
   Loop composition:
       U = H(q) + (q / (1 - q)) * U(body)
       R = q(1 - q)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Mapping, Sequence, Tuple

from composition import binary_entropy, compose_loop, compose_or, compose_xor
from iepi_score import compute_construct_violation_record, compute_iepi
from metrics import normalized_entropy, responsiveness
from validation import build_construct_flags, build_loop_flags


@dataclass(frozen=True)
class Thresholds:
    """Threshold container for IEPI scoring."""
    H_min: float
    H_max: float
    rho_min: float


def compute_construct_diagnostics(
    probability_map: Mapping[str, Sequence[float]],
    thresholds: Thresholds,
) -> Dict[str, Dict[str, object]]:
    """
    Compute per-construct diagnostics and violations for XOR/OR constructs.
    """
    records: Dict[str, Dict[str, object]] = {}

    for construct_id, probabilities in probability_map.items():
        flags_record = build_construct_flags(construct_id, probabilities)

        if not flags_record["valid"]:
            records[construct_id] = dict(flags_record)
            continue

        H_N = normalized_entropy(probabilities)
        R = responsiveness(probabilities)

        records[construct_id] = compute_construct_violation_record(
            construct_id=construct_id,
            H_N=H_N,
            R=R,
            flags=flags_record,
            H_min=thresholds.H_min,
            H_max=thresholds.H_max,
            rho_min=thresholds.rho_min,
        )

    return records


def compute_loop_diagnostics(
    loop_probability_map: Mapping[str, float],
    thresholds: Thresholds,
) -> Dict[str, Dict[str, object]]:
    """
    Compute per-construct diagnostics and violations for LOOP constructs.
    """
    records: Dict[str, Dict[str, object]] = {}

    for construct_id, q in loop_probability_map.items():
        flags_record = build_loop_flags(construct_id, q)

        if not flags_record["valid"]:
            records[construct_id] = dict(flags_record)
            continue

        H_N = binary_entropy(q) / math.log(2.0)
        R = q * (1.0 - q)

        records[construct_id] = compute_construct_violation_record(
            construct_id=construct_id,
            H_N=H_N,
            R=R,
            flags=flags_record,
            H_min=thresholds.H_min,
            H_max=thresholds.H_max,
            rho_min=thresholds.rho_min,
        )

    return records


def extract_valid_construct_records(
    construct_records: Mapping[str, Mapping[str, object]],
) -> Dict[str, Dict[str, object]]:
    """
    Return the valid construct subset C_valid used for IEPI aggregation.
    """
    valid: Dict[str, Dict[str, object]] = {}

    for construct_id, record in construct_records.items():
        if "H_N" in record and "R" in record and "V" in record:
            valid[construct_id] = dict(record)

    return valid


def evaluate_block_utility(
    block: Mapping[str, object],
    probability_map: Mapping[str, Sequence[float]],
    loop_probability_map: Mapping[str, float],
) -> float:
    """
    Recursively evaluate block-level uncertainty U(B).
    """
    block_type = block["type"]

    if block_type == "leaf":
        return 0.0

    if block_type in {"seq", "and"}:
        children = block.get("children", [])
        return sum(
            evaluate_block_utility(child, probability_map, loop_probability_map)
            for child in children
        )

    if block_type == "xor":
        construct_id = block["id"]
        probabilities = probability_map[construct_id]
        children = block["children"]
        child_utilities = [
            evaluate_block_utility(child, probability_map, loop_probability_map)
            for child in children
        ]
        U, _ = compose_xor(probabilities, child_utilities)
        return U

    if block_type == "or":
        construct_id = block["id"]
        probabilities = probability_map[construct_id]
        children = block["children"]
        child_utilities = [
            evaluate_block_utility(child, probability_map, loop_probability_map)
            for child in children
        ]
        U, _ = compose_or(probabilities, child_utilities)
        return U

    if block_type == "loop":
        construct_id = block["id"]
        q = loop_probability_map[construct_id]
        body = block["body"]
        body_utility = evaluate_block_utility(body, probability_map, loop_probability_map)
        U, _ = compose_loop(q, body_utility)
        return U

    raise ValueError(f"Unsupported block type: {block_type}")


def evaluate_block_responsiveness(
    block: Mapping[str, object],
    probability_map: Mapping[str, Sequence[float]],
    loop_probability_map: Mapping[str, float],
) -> float:
    """
    Recursively evaluate the descriptive block-level responsiveness summary R(B).

    In this reference implementation, the reported process-level R is the sum of
    local routing responsiveness values across routing constructs appearing in
    the process structure, consistent with the paper's reported Scenario A/B
    block-level summaries.
    """
    block_type = block["type"]

    if block_type == "leaf":
        return 0.0

    if block_type in {"seq", "and"}:
        children = block.get("children", [])
        return sum(
            evaluate_block_responsiveness(child, probability_map, loop_probability_map)
            for child in children
        )

    if block_type == "xor":
        construct_id = block["id"]
        local_r = responsiveness(probability_map[construct_id])
        children = block["children"]
        child_r = sum(
            evaluate_block_responsiveness(child, probability_map, loop_probability_map)
            for child in children
        )
        return local_r + child_r

    if block_type == "or":
        construct_id = block["id"]
        local_r = responsiveness(probability_map[construct_id])
        children = block["children"]
        child_r = sum(
            evaluate_block_responsiveness(child, probability_map, loop_probability_map)
            for child in children
        )
        return local_r + child_r

    if block_type == "loop":
        construct_id = block["id"]
        q = loop_probability_map[construct_id]
        local_r = q * (1.0 - q)
        body = block["body"]
        body_r = evaluate_block_responsiveness(body, probability_map, loop_probability_map)
        return local_r + body_r

    raise ValueError(f"Unsupported block type: {block_type}")


def run_iepi_engine(
    process_block: Mapping[str, object],
    probability_map: Mapping[str, Sequence[float]],
    thresholds: Thresholds,
    loop_probability_map: Mapping[str, float] | None = None,
) -> Dict[str, object]:
    """
    Run the complete IEPI computation for a process.
    """
    if loop_probability_map is None:
        loop_probability_map = {}

    xor_or_records = compute_construct_diagnostics(
        probability_map=probability_map,
        thresholds=thresholds,
    )

    loop_records = compute_loop_diagnostics(
        loop_probability_map=loop_probability_map,
        thresholds=thresholds,
    )

    construct_records: Dict[str, Dict[str, object]] = {}
    construct_records.update(xor_or_records)
    construct_records.update(loop_records)

    valid_construct_records = extract_valid_construct_records(construct_records)

    U_process = evaluate_block_utility(
        process_block,
        probability_map=probability_map,
        loop_probability_map=loop_probability_map,
    )

    R_process = evaluate_block_responsiveness(
        process_block,
        probability_map=probability_map,
        loop_probability_map=loop_probability_map,
    )

    iepi_value = compute_iepi(valid_construct_records)

    return {
        "constructs": construct_records,
        "C_valid": valid_construct_records,
        "U": U_process,
        "R": R_process,
        "IEPI": iepi_value,
    }
