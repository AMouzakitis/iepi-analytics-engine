"""
composition.py

Deterministic composition rules for the IEPI reference implementation.

Implemented exactly as specified in the paper:

1. XOR composition
   U = H(p) + Σ p_i U(child_i)
   R = 1 - Σ p_i^2

2. SEQ / AND composition
   U = Σ U(child_i)
   R = Σ R(child_i)

3. OR composition
   U = H2(p) + Σ p_i U(child_i)
   H2(p) = -log(Σ p_i^2)
   R = 1 - Σ p_i^2

4. LOOP composition
   U = H(q) + (q / (1 - q)) * U(body)
   R = q(1 - q)

Notes
-----
- Natural logarithm is used throughout.
- This module assumes probabilities have already been validated.
- No inference, tuning, or external modeling logic is included.
"""

from __future__ import annotations

import math
from typing import Sequence

from metrics import entropy, responsiveness


def _check_finite(values: Sequence[float], name: str) -> None:
    """Reject non-finite numeric inputs."""
    for i, value in enumerate(values):
        if not math.isfinite(value):
            raise ValueError(f"{name} contains a non-finite value at index {i}.")


def renyi2_entropy(probabilities: Sequence[float]) -> float:
    """
    Compute Rényi-2 entropy:

        H2(p) = -log(Σ p_i^2)
    """
    _check_finite(probabilities, "probabilities")

    sum_sq = sum(p * p for p in probabilities)
    if sum_sq <= 0.0:
        raise ValueError("Rényi-2 entropy is undefined when sum(p_i^2) <= 0.")
    return -math.log(sum_sq)


def binary_entropy(q: float) -> float:
    """
    Compute binary entropy:

        H(q) = -q log q - (1-q) log(1-q)
    """
    if not math.isfinite(q):
        raise ValueError("Loop probability q must be finite.")

    h = 0.0
    if q > 0.0:
        h -= q * math.log(q)
    if (1.0 - q) > 0.0:
        h -= (1.0 - q) * math.log(1.0 - q)
    return h


def compose_xor(
    probabilities: Sequence[float],
    child_utilities: Sequence[float],
) -> tuple[float, float]:
    """
    XOR composition:

        U = H(p) + Σ p_i U(child_i)
        R = 1 - Σ p_i^2
    """
    if len(probabilities) != len(child_utilities):
        raise ValueError("probabilities and child_utilities must have the same length.")

    _check_finite(probabilities, "probabilities")
    _check_finite(child_utilities, "child_utilities")

    expected_child_u = sum(p * u for p, u in zip(probabilities, child_utilities))
    U = entropy(probabilities) + expected_child_u
    R = responsiveness(probabilities)
    return U, R


def compose_seq(
    child_utilities: Sequence[float],
    child_responsiveness: Sequence[float],
) -> tuple[float, float]:
    """
    SEQ composition:

        U = Σ U(child_i)
        R = Σ R(child_i)
    """
    if len(child_utilities) != len(child_responsiveness):
        raise ValueError("child_utilities and child_responsiveness must have the same length.")

    _check_finite(child_utilities, "child_utilities")
    _check_finite(child_responsiveness, "child_responsiveness")

    U = sum(child_utilities)
    R = sum(child_responsiveness)
    return U, R


def compose_and(
    child_utilities: Sequence[float],
    child_responsiveness: Sequence[float],
) -> tuple[float, float]:
    """
    AND composition:

        U = Σ U(child_i)
        R = Σ R(child_i)

    Identical to SEQ under the IEPI composition rules.
    """
    return compose_seq(child_utilities, child_responsiveness)


def compose_or(
    probabilities: Sequence[float],
    child_utilities: Sequence[float],
) -> tuple[float, float]:
    """
    OR composition:

        U = H2(p) + Σ p_i U(child_i)
        R = 1 - Σ p_i^2
    """
    if len(probabilities) != len(child_utilities):
        raise ValueError("probabilities and child_utilities must have the same length.")

    _check_finite(probabilities, "probabilities")
    _check_finite(child_utilities, "child_utilities")

    expected_child_u = sum(p * u for p, u in zip(probabilities, child_utilities))
    U = renyi2_entropy(probabilities) + expected_child_u
    R = responsiveness(probabilities)
    return U, R


def compose_loop(q: float, body_utility: float) -> tuple[float, float]:
    """
    LOOP composition:

        U = H(q) + (q / (1 - q)) * U(body)
        R = q(1 - q)
    """
    if not math.isfinite(q):
        raise ValueError("Loop probability q must be finite.")
    if not math.isfinite(body_utility):
        raise ValueError("body_utility must be finite.")
    if q >= 1.0:
        raise ValueError("LOOP composition is undefined for q >= 1.")
    if q < 0.0:
        raise ValueError("LOOP composition is undefined for q < 0.")

    U = binary_entropy(q) + (q / (1.0 - q)) * body_utility
    R = q * (1.0 - q)
    return U, R
