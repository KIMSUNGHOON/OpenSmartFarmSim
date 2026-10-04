"""Independent Decimal conservation examples for the explicit-entry policy."""

import argparse
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "crop-fruit-allocation-decimal-policy-reference-v1"
POLICY = "explicit-entry-fruit-allocation-research-v1"


def references():
    cases = []
    data = (
        ("zero", "0", "0", "0", {1: "0"}),
        ("entry-only", "6", "2", "3", {1: "100"}),
        ("tail-only", "10", "0", "0", {1: "1", 2: "2", 50: "3"}),
        ("mixed", "10", "2", "1", {1: "1", 2: "2", 50: "3"}),
        ("single-tail", "10", "2", "1", {1: "10", 37: "5"}),
        ("large-first-demand", "10", "2", "1", {1: "1e30", 2: "2", 50: "3"}),
        ("empty-tail", "10", "2", "1", {1: "1"}),
        ("empty-all", "10", "0", "0", {}),
        ("entry-budget", "1", "2", "1", {2: "5"}),
        ("zero-entry-mass", "1", "2", "0", {2: "5"}),
    )
    with localcontext() as context:
        context.prec = 60
        for name, f, s, mass, demand in data:
            F, S, W1 = map(Decimal, (f, s, mass))
            weights = [Decimal(demand.get(j, "0")) for j in range(1, 51)]
            entry, denominator = S * W1, sum(weights[1:])
            remaining = F - entry
            hold = ("FRUIT_ENTRY_STATE_HOLD" if S > 0 and W1 == 0 else
                    "FRUIT_ENTRY_BUDGET_HOLD" if remaining < 0 else
                    "EMPTY_FRUIT_SINK_HOLD" if remaining > 0 and denominator == 0 else None)
            case = {"case_id": "synthetic-" + name, "origin": "synthetic",
                    "F": f, "S": s, "W1": mass, "demand": list(map(str, weights)),
                    "expected_hold": hold}
            if hold is None:
                allocation = [entry] + [remaining * w / denominator if remaining else Decimal(0)
                                       for w in weights[1:]]
                number = [S] + [Decimal(0)] * 49
                assert sum(allocation) == F and sum(number) == S
                case.update({"expected_allocation": list(map(str, allocation)),
                             "expected_number_inflow": list(map(str, number)),
                             "carbon_sum": str(sum(allocation)), "number_sum": str(sum(number))})
                if sum(weights) > 0 and remaining > 0:
                    original_sum = entry + remaining * sum(weights[1:]) / sum(weights)
                    epsilon_sum = entry + remaining * denominator / (denominator + Decimal("1e-9"))
                    case["printed_original_sum"] = str(original_sum)
                    case["greenhouses_epsilon_sum"] = str(epsilon_sum)
                    assert original_sum < F and epsilon_sum < F
            cases.append(case)
    return {"evidence_version": VERSION, "policy_id": POLICY,
            "scope": "synthetic policy arithmetic only; product implementation and actual fruit modelling not accepted",
            "method": "60-digit Decimal; no product imports; exact conservation; original and epsilon counterexamples",
            "generator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "contract_sha256": sha256((ROOT / 'contracts/crop-fruit-allocation-v1.md').read_bytes()).hexdigest(),
            "source_register_sha256": sha256((ROOT / 'research/crop-fruit-allocation-source-register.json').read_bytes()).hexdigest(),
            "cases": cases, "normal_cases": sum(c["expected_hold"] is None for c in cases),
            "hold_cases": sum(c["expected_hold"] is not None for c in cases),
            "gates_opened": [], "actual_crop_runs": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
        default=ROOT / 'research/artifacts/crop-fruit-allocation-policy-reference-20261005.json')
    args = parser.parse_args()
    protected = (Path(__file__).resolve(), (ROOT / 'contracts/crop-fruit-allocation-v1.md').resolve(),
                 (ROOT / 'research/crop-fruit-allocation-source-register.json').resolve())
    if args.output.is_symlink() or args.output.resolve() in protected:
        raise ValueError('reference_output_would_replace_input')
    document = references()
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'normal': document['normal_cases'], 'holds': document['hold_cases'],
                      'policy_id': POLICY, 'product_imports': False}))


if __name__ == '__main__':
    main()
