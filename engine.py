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

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

from composition import compose_and, compose_loop, compose_or, compose_seq, compose_xor
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

    Invalid probability inputs are flagged and excluded from V(c) computation.
    """
    records: Dict[str, Dict[str, object]] = {}

    for construct_id, probabilities in probability_map.items():
        flags_record = build_construct_flags(construct_id, probabilities)

        if not flags_record["valid"]:
            records[construct_id] = {
                "construct_id": construct_id,
                "flags": flags_record,
            }
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
    from composition import binary_entropy

    records: Dict[str, Dict[str, object]] = {}

    for construct_id, q in loop_probability_map.items():
        flags_record = build_loop_flags(construct_id, q)

        if not flags_record["valid"]:
            records[construct_id] = {
                "construct_id": construct_id,
                "flags": flags_record,
            }
            continue

        H_N = binary_entropy(q) / __import__("math").log(2.0)
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


def evaluate_block(
    block: Mapping[str, object],
    probability_map: Mapping[str, Sequence[float]],
    loop_probability_map: Mapping[str, float],
) -> Tuple[float, float]:
    """
    Recursively evaluate a block and return (U, R).

    Block schema
    ------------
    leaf:
        {"type": "leaf"}

    seq / and:
        {"type": "seq", "children": [...]}
        {"type": "and", "children": [...]}

    xor / or:
        {
            "type": "xor",
            "id": "G1",
            "children": [...]
        }

        {
            "type": "or",
            "id": "G2",
            "children": [...]
        }

    loop:
        {
            "type": "loop",
            "id": "L1",
            "body": {...}
        }
    """
    block_type = block["type"]

    if block_type == "leaf":
        return 0.0, 0.0

    if block_type in {"seq", "and"}:
        children = block.get("children", [])
        child_utilities: List[float] = []
        child_responsiveness: List[float] = []

        for child in children:
            U_child, R_child = evaluate_block(child, probability_map, loop_probability_map)
            child_utilities.append(U_child)
            child_responsiveness.append(R_child)

        if block_type == "seq":
            return compose_seq(child_utilities, child_responsiveness)
        return compose_and(child_utilities, child_responsiveness)

    if block_type == "xor":
        construct_id = block["id"]
        probabilities = probability_map[construct_id]
        children = block["children"]

        child_utilities = [
            evaluate_block(child, probability_map, loop_probability_map)[0]
            for child in children
        ]
        return compose_xor(probabilities, child_utilities)

    if block_type == "or":
        construct_id = block["id"]
        probabilities = probability_map[construct_id]
        children = block["children"]

        child_utilities = [
            evaluate_block(child, probability_map, loop_probability_map)[0]
            for child in children
        ]
        return compose_or(probabilities, child_utilities)

    if block_type == "loop":
        construct_id = block["id"]
        q = loop_probability_map[construct_id]
        body = block["body"]

        body_utility, _ = evaluate_block(body, probability_map, loop_probability_map)
        return compose_loop(q, body_utility)

    raise ValueError(f"Unsupported block type: {block_type}")


def run_iepi_engine(
    process_block: Mapping[str, object],
    probability_map: Mapping[str, Sequence[float]],
    thresholds: Thresholds,
    loop_probability_map: Mapping[str, float] | None = None,
) -> Dict[str, object]:
    """
    Run the complete IEPI computation for a process.

    Returns
    -------
    Dict[str, object]
        {
            "constructs": ...,
            "C_valid": ...,
            "U": ...,
            "R": ...,
            "IEPI": ...
        }
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

    U_process, R_process = evaluate_block(
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
