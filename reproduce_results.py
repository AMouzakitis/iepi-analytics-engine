"""
reproduce_results.py

Reproducibility script for the IEPI reference implementation.

This script reproduces the reported Scenario A, B, C, and D results using
the fixed probabilities and threshold configuration defined in the paper.
It also reports the threshold sensitivity results for variation in H_max.
"""

from __future__ import annotations

from typing import Mapping

from engine import Thresholds, run_iepi_engine


def format_float(x: float, digits: int = 6) -> str:
    return f"{x:.{digits}f}"


def average_violation(result: Mapping[str, object]) -> float:
    records = result["C_valid"]
    if not records:
        return 0.0
    return sum(float(r["V"]) for r in records.values()) / len(records)


def violating_constructs(result: Mapping[str, object]) -> str:
    records = result["C_valid"]
    violators = [
        cid for cid, r in records.items()
        if str(r["kappa"]) != "viable"
    ]
    return ", ".join(violators) if violators else "None"


def print_construct_diagnostics(title: str, constructs: Mapping[str, dict]) -> None:
    print(title)
    print("-" * len(title))

    for construct_id in sorted(constructs.keys()):
        record = constructs[construct_id]

        if "H_N" not in record:
            print(f"{construct_id}: INVALID ({record['flags']})")
            continue

        print(
            f"{construct_id}: "
            f"H_N={format_float(record['H_N'], 3)}, "
            f"R={format_float(record['R'], 3)}, "
            f"kappa={record['kappa']}, "
            f"V={format_float(record['V'], 4)}, "
            f"flags=valid"
        )
    print()


def print_process_result(name: str, result: Mapping[str, object]) -> None:
    print(name)
    print("-" * len(name))
    print(f"U = {format_float(result['U'], 3)}")
    print(f"R = {format_float(result['R'], 3)}")
    print(f"|C_valid| = {len(result['C_valid'])}")
    print(f"average V = {format_float(average_violation(result), 4)}")
    print(f"IEPI = {format_float(result['IEPI'], 3)}")
    print()


def make_authorization_chain() -> dict:
    return {
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


def build_scenarios() -> dict:
    scenario_A = make_authorization_chain()

    scenario_B = {
        "type": "xor",
        "id": "G0",
        "children": [
            make_authorization_chain(),
            {"type": "leaf"},
        ],
    }

    scenario_C = {
        "type": "seq",
        "children": [
            {
                "type": "or",
                "id": "G_OR",
                "children": [
                    {"type": "leaf"},
                    {"type": "leaf"},
                ],
            },
            make_authorization_chain(),
        ],
    }

    scenario_D = {
        "type": "seq",
        "children": [
            {
                "type": "loop",
                "id": "LOOP",
                "body": {"type": "leaf"},
            },
            make_authorization_chain(),
        ],
    }

    return {
        "A": scenario_A,
        "B": scenario_B,
        "C": scenario_C,
        "D": scenario_D,
    }


def build_probability_maps() -> dict:
    return {
        "A": {
            "G1": (0.70, 0.30),
            "G2": (0.85, 0.15),
        },
        "B": {
            "G0": (0.60, 0.40),
            "G1": (0.70, 0.30),
            "G2": (0.85, 0.15),
        },
        "C": {
            "G_OR": (0.40, 0.60),
            "G1": (0.70, 0.30),
            "G2": (0.85, 0.15),
        },
        "D": {
            "G1": (0.70, 0.30),
            "G2": (0.85, 0.15),
        },
    }


def build_loop_probability_maps() -> dict:
    return {
        "A": {},
        "B": {},
        "C": {},
        "D": {
            "LOOP": 0.35,
        },
    }


def run_all(thresholds: Thresholds) -> dict:
    scenarios = build_scenarios()
    probability_maps = build_probability_maps()
    loop_probability_maps = build_loop_probability_maps()

    results = {}

    for name in ["A", "B", "C", "D"]:
        results[name] = run_iepi_engine(
            process_block=scenarios[name],
            probability_map=probability_maps[name],
            loop_probability_map=loop_probability_maps[name],
            thresholds=thresholds,
        )

    return results


def print_baseline_results() -> None:
    thresholds = Thresholds(
        H_min=0.30,
        H_max=0.95,
        rho_min=0.20,
    )

    results = run_all(thresholds)

    for name in ["A", "B", "C", "D"]:
        print_construct_diagnostics(
            f"Scenario {name}: Construct Diagnostics",
            results[name]["constructs"],
        )
        print_process_result(f"Scenario {name}", results[name])


def print_threshold_sensitivity() -> None:
    print("Threshold Sensitivity")
    print("---------------------")
    print("Scenario | H_max | Violating Constructs | average V | IEPI")

    for H_max in [0.85, 0.90, 0.95]:
        thresholds = Thresholds(
            H_min=0.30,
            H_max=H_max,
            rho_min=0.20,
        )

        results = run_all(thresholds)

        for name in ["A", "B", "C", "D"]:
            result = results[name]
            print(
                f"{name} | "
                f"{H_max:.2f} | "
                f"{violating_constructs(result)} | "
                f"{average_violation(result):.4f} | "
                f"{result['IEPI']:.3f}"
            )

    print()


def main() -> None:
    print_baseline_results()
    print_threshold_sensitivity()


if __name__ == "__main__":
    main()
