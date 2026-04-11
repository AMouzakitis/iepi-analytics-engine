"""
validation.py

Validation helpers for the IEPI reference implementation.

Responsibilities
----------------
- Check routing probability-vector constraints.
- Check loop continuation probability constraints.
- Produce deterministic diagnostic records f[c].

This module does not modify probabilities or infer missing values.
It only checks conformance.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence


DEFAULT_TOLERANCE = 1e-9


def check_probability_constraints(
    probabilities: Sequence[float],
    tol: float = DEFAULT_TOLERANCE,
) -> List[str]:
    """
    Check whether a routing probability vector satisfies the required constraints.

    Constraints checked
    -------------------
    1. Vector is not empty.
    2. Vector length is at least 2.
    3. Every probability is finite.
    4. Every probability lies in [0, 1] up to tolerance.
    5. Sum of probabilities equals 1 within tolerance.

    Parameters
    ----------
    probabilities : Sequence[float]
        Probability vector p.
    tol : float, optional
        Numerical tolerance.

    Returns
    -------
    List[str]
        A list of flag strings. Empty list means the vector is valid.
    """
    flags: List[str] = []

    if len(probabilities) == 0:
        flags.append("EMPTY_VECTOR")
        return flags

    if len(probabilities) < 2:
        flags.append("VECTOR_TOO_SHORT")

    total = 0.0
    for i, p in enumerate(probabilities):
        if not math.isfinite(p):
            flags.append(f"NON_FINITE_P_AT_{i}")
            continue

        if p < -tol or p > 1.0 + tol:
            flags.append(f"OUT_OF_RANGE_P_AT_{i}")

        total += p

    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=tol):
        flags.append("SUM_NOT_ONE")

    return flags


def check_loop_probability(
    q: float,
    tol: float = DEFAULT_TOLERANCE,
) -> List[str]:
    """
    Check whether a loop continuation probability q satisfies the required constraints.

    Constraints checked
    -------------------
    1. q is finite.
    2. q lies in [0, 1] up to tolerance.

    Parameters
    ----------
    q : float
        Loop continuation probability.
    tol : float, optional
        Numerical tolerance.

    Returns
    -------
    List[str]
        A list of flag strings. Empty list means q is valid.
    """
    flags: List[str] = []

    if not math.isfinite(q):
        flags.append("NON_FINITE_Q")
        return flags

    if q < -tol or q > 1.0 + tol:
        flags.append("OUT_OF_RANGE_Q")

    return flags


def is_valid_probability_vector(
    probabilities: Sequence[float],
    tol: float = DEFAULT_TOLERANCE,
) -> bool:
    """
    Return True iff the routing probability vector satisfies all constraints.
    """
    return len(check_probability_constraints(probabilities, tol=tol)) == 0


def is_valid_loop_probability(
    q: float,
    tol: float = DEFAULT_TOLERANCE,
) -> bool:
    """
    Return True iff the loop continuation probability satisfies all constraints.
    """
    return len(check_loop_probability(q, tol=tol)) == 0


def build_construct_flags(
    construct_id: str,
    probabilities: Optional[Sequence[float]],
    tol: float = DEFAULT_TOLERANCE,
) -> Dict[str, object]:
    """
    Build the diagnostic record f[c] for an XOR/OR routing construct.

    Parameters
    ----------
    construct_id : str
        Identifier of the construct c.
    probabilities : Optional[Sequence[float]]
        Probability vector assigned to c, or None if missing.
    tol : float, optional
        Numerical tolerance.

    Returns
    -------
    Dict[str, object]
        Dictionary with:
        - 'construct_id': str
        - 'valid': bool
        - 'flags': List[str]
    """
    if probabilities is None:
        flags = ["MISSING_PROBABILITY_ASSIGNMENT"]
    else:
        flags = check_probability_constraints(probabilities, tol=tol)

    return {
        "construct_id": construct_id,
        "valid": len(flags) == 0,
        "flags": flags,
    }


def build_loop_flags(
    construct_id: str,
    q: Optional[float],
    tol: float = DEFAULT_TOLERANCE,
) -> Dict[str, object]:
    """
    Build the diagnostic record f[c] for a LOOP construct.

    Parameters
    ----------
    construct_id : str
        Identifier of the construct c.
    q : Optional[float]
        Loop continuation probability, or None if missing.
    tol : float, optional
        Numerical tolerance.

    Returns
    -------
    Dict[str, object]
        Dictionary with:
        - 'construct_id': str
        - 'valid': bool
        - 'flags': List[str]
    """
    if q is None:
        flags = ["MISSING_PROBABILITY_ASSIGNMENT"]
    else:
        flags = check_loop_probability(q, tol=tol)

    return {
        "construct_id": construct_id,
        "valid": len(flags) == 0,
        "flags": flags,
    }


def validate_probability_map(
    probability_map: Dict[str, Sequence[float]],
    tol: float = DEFAULT_TOLERANCE,
) -> Dict[str, Dict[str, object]]:
    """
    Validate an entire routing probability map P[c] for XOR/OR constructs.

    Parameters
    ----------
    probability_map : Dict[str, Sequence[float]]
        Mapping from construct ID to probability vector.
    tol : float, optional
        Numerical tolerance.

    Returns
    -------
    Dict[str, Dict[str, object]]
        Mapping:
            c -> f[c]
    """
    results: Dict[str, Dict[str, object]] = {}
    for construct_id, probabilities in probability_map.items():
        results[construct_id] = build_construct_flags(
            construct_id=construct_id,
            probabilities=probabilities,
            tol=tol,
        )
    return results
