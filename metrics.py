"""
metrics.py

Core deterministic metric functions for the IEPI reference implementation.

Definitions implemented exactly as specified in the paper:

1. Entropy:
   H(p) = -Σ p_i log p_i

2. Normalized entropy:
   H_N(p) = H(p) / log(k)

3. Responsiveness:
   R(p) = 1 - Σ p_i^2

Notes
-----
- Natural logarithm is used throughout.
- Terms with p_i = 0 contribute 0 to entropy by continuity.
- Validation of probability vectors is intentionally kept outside this module.
"""

from __future__ import annotations

import math
from typing import Sequence


def _check_finite(probabilities: Sequence[float]) -> None:
    """Reject non-finite numeric inputs."""
    for p in probabilities:
        if not math.isfinite(p):
            raise ValueError("Probability vector contains a non-finite value.")


def entropy(probabilities: Sequence[float]) -> float:
    """
    Compute Shannon entropy:

        H(p) = -Σ p_i log p_i

    Parameters
    ----------
    probabilities : Sequence[float]
        Probability vector p.

    Returns
    -------
    float
        Entropy value using natural logarithm.
    """
    _check_finite(probabilities)

    h = 0.0
    for p in probabilities:
        if p > 0.0:
            h -= p * math.log(p)
    return h


def normalized_entropy(probabilities: Sequence[float]) -> float:
    """
    Compute normalized entropy:

        H_N(p) = H(p) / log(k)

    where k is the number of branches / outcomes.

    Parameters
    ----------
    probabilities : Sequence[float]
        Probability vector p.

    Returns
    -------
    float
        Normalized entropy.

    Raises
    ------
    ValueError
        If k < 2, since log(1) = 0 makes normalization undefined.
    """
    k = len(probabilities)
    if k < 2:
        raise ValueError(
            "Normalized entropy is undefined for probability vectors of length < 2."
        )
    return entropy(probabilities) / math.log(k)


def responsiveness(probabilities: Sequence[float]) -> float:
    """
    Compute responsiveness:

        R(p) = 1 - Σ p_i^2

    Parameters
    ----------
    probabilities : Sequence[float]
        Probability vector p.

    Returns
    -------
    float
        Responsiveness value.
    """
    _check_finite(probabilities)
    return 1.0 - sum(p * p for p in probabilities)


def branching_cardinality(probabilities: Sequence[float]) -> int:
    """
    Return the branching cardinality k.

    Parameters
    ----------
    probabilities : Sequence[float]
        Probability vector p.

    Returns
    -------
    int
        Number of outcomes / branches.
    """
    return len(probabilities)


def entropy_responsiveness_bound(probabilities: Sequence[float]) -> float:
    """
    Compute the collision-entropy lower bound:

        -log(1 - R(p))

    used in the paper as a diagnostic coherence check.

    Parameters
    ----------
    probabilities : Sequence[float]
        Probability vector p.

    Returns
    -------
    float
        Lower bound associated with responsiveness.
    """
    r = responsiveness(probabilities)
    if r >= 1.0:
        raise ValueError("Responsiveness must be < 1 for the logarithmic bound.")
    return -math.log(1.0 - r)
