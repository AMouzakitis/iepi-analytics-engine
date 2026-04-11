"""
reproduce_results.py

Reproducibility script for the IEPI reference implementation.

This script reproduces the reported Scenario A and Scenario B results
using the fixed probabilities and threshold configuration defined in the paper.
"""

from __future__ import annotations

from typing import Mapping

from engine import Thresholds, run_iepi_engine


def format_float(x: float, digits: int = 6) -> str:
    """Format a float for reproducible console output."""
    return f"{x:.{digits}f}"


def print_construct_diagnostics(title: str, constructs: Mapping[str, dict]) -> None:
    """Print per-construct diagnostics for valid construct records."""
    print(title)
    print("-" * len(title))

    for construct_id in sorted(constructs.keys()):
        record = constructs[construct_id]
        if "H_N" not in record:
            print(f"{construct_id}: INVALID ({record['flags']})")
            continue

        print(
            f"{construct_id}: "
            f"H_N={format_float(record['H_N'])}, "
            f"R={format_float(record['R'])}, "
            f"kappa={record['kappa']}, "
            f"V={format_float(record['V'])}"
        )
    print()


def print_process_result(name: str, result: Mapping[str, object]) -> None:
    """Print process-level outputs."""
    print(name)
    print("-" * len(name))
    print(f"U = {format_float(result['U'])}")
    print(f"R = {format_float(result['R'])}")
    print(f"IEPI = {format_float(result['IEPI'])}")
    print(f"|C_valid| = {len(result['C_valid'])}")
    print()


def main() -> None:
    # ------------------------------------------------------------------
    # Fixed probabilities from the paper
    # ------------------------------------------------------------------
    probability_map_A = {
        "G1": (0.70, 0.30),
        "G2": (0.60, 0.40),
    }

    probability_map_B = {
        "G0": (0.85, 0.15),
        "G1": (0.70, 0.30),
        "G2": (0.60, 0.40),
    }

    thresholds = Thresholds(
        H_min=0.30,
        H_max=0.95,
        rho_min=0.20,
    )

    # ------------------------------------------------------------------
    # Scenario A
    #
    # Paper-consistent structure:
    # G1 routes either to rejection (leaf) or to G2
    # G2 then routes to approval / rejection
    #
    # This yields:
    #   U_A = H(p_G1) + p_G1^pass * H(p_G2)
    #   R_A = R(p_G1) + R(p_G2)
    # ------------------------------------------------------------------
    scenario_A = {
        "type": "xor",
        "id": "G1",
        "children": [
            {
                "type": "xor",
                "id": "G2",
                "children": [
                    {"type": "leaf"},
                    {"type": "leaf"},
                ],
            },
            {"type": "leaf"},
        ],
    }

    result_A = run_iepi_engine(
        process_block=scenario_A,
        probability_map=probability_map_A,
        thresholds=thresholds,
    )

    # ------------------------------------------------------------------
    # Scenario B
    #
    # Paper-consistent structure:
    # G0 routes either to rejection (leaf) or to the Scenario A approval chain
    #
    # This yields:
    #   U_B = H(p_G0) + p_G0^pass * [H(p_G1) + p_G1^pass * H(p_G2)]
    #   R_B = R(p_G0) + R(p_G1) + R(p_G2)
    # ------------------------------------------------------------------
    scenario_B = {
        "type": "xor",
        "id": "G0",
        "children": [
            {
                "type": "xor",
                "id": "G1",
                "children": [
                    {
                        "type": "xor",
                        "id": "G2",
                        "children": [
                            {"type": "leaf"},
                            {"type": "leaf"},
                        ],
                    },
                    {"type": "leaf"},
                ],
            },
            {"type": "leaf"},
        ],
    }

    result_B = run_iepi_engine(
        process_block=scenario_B,
        probability_map=probability_map_B,
        thresholds=thresholds,
    )

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    print_construct_diagnostics("Scenario A: Construct Diagnostics", result_A["constructs"])
    print_process_result("Scenario A", result_A)

    print_construct_diagnostics("Scenario B: Construct Diagnostics", result_B["constructs"])
    print_process_result("Scenario B", result_B)


if __name__ == "__main__":
    main()
