"""
iepi_score.py

Violation, classification, and IEPI score computations for the IEPI reference implementation.

Implemented exactly as specified in the paper:

    V(c) = [H_min - H_N]_+ + [H_N - H_max]_+ + [rho_min - R]_+

    IEPI = 1 / (1 + average(V(c)))

where [x]_+ = max(x, 0).

Notes
-----
- IEPI is computed from per-construct diagnostics.
- This module is deterministic and contains no tuning or inference logic.
"""

from __future__ import annotations

from typing import Dict, Mapping


def positive_part(x: float) -> float:
    """
    Compute the positive-part operator:

        [x]_+ = max(x, 0)
    """
    return x if x > 0.0 else 0.0


def classify_construct(
    H_N: float,
    R: float,
    H_min: float,
    H_max: float,
    rho_min: float,
) -> str:
    """
    Classify a routing construct according to the viability rules.

    Returns one of:
    - 'under-responsive'
    - 'under-uncertain'
    - 'over-uncertain'
    - 'viable'
    """
    if R < rho_min:
        return "under-responsive"
    if H_N < H_min:
        return "under-uncertain"
    if H_N > H_max:
        return "over-uncertain"
    return "viable"


def compute_violation(
    H_N: float,
    R: float,
    H_min: float,
    H_max: float,
    rho_min: float,
) -> float:
    """
    Compute the per-construct violation:

        V(c) = [H_min - H_N]_+ + [H_N - H_max]_+ + [rho_min - R]_+
    """
    return (
        positive_part(H_min - H_N)
        + positive_part(H_N - H_max)
        + positive_part(rho_min - R)
    )


def compute_construct_violation_record(
    construct_id: str,
    H_N: float,
    R: float,
    flags: object,
    H_min: float,
    H_max: float,
    rho_min: float,
) -> Dict[str, object]:
    """
    Build a complete deterministic per-construct record including κ(c) and V(c).

    Returns
    -------
    Dict[str, object]
        Record containing:
        - construct_id
        - H_N
        - R
        - kappa
        - flags
        - V
    """
    kappa = classify_construct(
        H_N=H_N,
        R=R,
        H_min=H_min,
        H_max=H_max,
        rho_min=rho_min,
    )

    V = compute_violation(
        H_N=H_N,
        R=R,
        H_min=H_min,
        H_max=H_max,
        rho_min=rho_min,
    )

    return {
        "construct_id": construct_id,
        "H_N": H_N,
        "R": R,
        "kappa": kappa,
        "flags": flags,
        "V": V,
    }


def average_violation(construct_records: Mapping[str, Mapping[str, object]]) -> float:
    """
    Compute the average violation across constructs.

    Returns 0.0 when no valid construct records are provided, consistent with
    the paper's IEPI definition for |C_valid| = 0.
    """
    if not construct_records:
        return 0.0

    total = 0.0
    count = 0

    for record in construct_records.values():
        total += float(record["V"])
        count += 1

    return total / count


def compute_iepi(construct_records: Mapping[str, Mapping[str, object]]) -> float:
    """
    Compute the process-level IEPI score:

        IEPI = 1 / (1 + average(V(c)))

    If no valid construct records are provided, return IEPI = 1.0,
    consistent with the paper.
    """
    avg_v = average_violation(construct_records)
    return 1.0 / (1.0 + avg_v)


def extract_diagnostics_tuple(record: Mapping[str, object]) -> tuple[float, float, str, object]:
    """
    Convenience helper to extract the per-construct diagnostic tuple:

        Π[c] = (H_N(c), R(c), κ(c), f[c])

    Returns
    -------
    tuple[float, float, str, object]
        (H_N, R, kappa, flags)
    """
    return (
        float(record["H_N"]),
        float(record["R"]),
        str(record["kappa"]),
        record["flags"],
    )
