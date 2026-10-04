"""Independent Decimal references for isolated Vanthoor fruit transport."""

import argparse
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "crop-fruit-transport-decimal-reference-v1"
PROFILE_SHA256 = "09ea5e176bc745361e8e3ec8945b0f8abb0b2b427b4e9c459d0663cf390e9070"


def references(raw_profile):
    assert sha256(raw_profile).hexdigest() == PROFILE_SHA256
    p = json.loads(raw_profile)
    stages = p["parameters"]["nDev"]["value"]
    cases = []
    with localcontext() as context:
        context.prec = 60
        coefficients = {k: Decimal(v["source_value"]) for k, v in p["parameters"].items()}
        for temperature in (17, 20, 23):
            for pattern in ("zero", "first", "last", "multiple", "nearly-equal"):
                numbers = [Decimal(0)] * stages
                carbon = [Decimal(0)] * stages
                if pattern == "first":
                    numbers[0], carbon[0] = Decimal("2.5"), Decimal("123.456")
                elif pattern == "last":
                    numbers[-1], carbon[-1] = Decimal("3.75"), Decimal("321.1234")
                elif pattern == "multiple":
                    for j in range(stages):
                        if j not in (7, 27):
                            numbers[j] = Decimal(j % 7 + 1) / 10
                            carbon[j] = numbers[j] * Decimal(42 + j) / 3
                elif pattern == "nearly-equal":
                    for j in range(stages):
                        numbers[j] = Decimal(10 ** 16 + 2 * (j % 2))
                        carbon[j] = Decimal(10 ** 16 + 4 * (j % 2))
                case_id = f"synthetic-{temperature}C-{pattern}"
                values = {
                    "fruit_number": [{"value": float(v), "unit": "fruits_equivalent/m2_floor"} for v in numbers],
                    "fruit_carbohydrate": [{"value": float(v), "unit": "mg_CH2O/m2_floor"} for v in carbon],
                    "temperature_filtered_24h": {"value": temperature, "unit": "degC"},
                    "temperature_sum": {"value": 1, "unit": "degC_day"},
                }
                rate = coefficients["cDev1"] + coefficients["cDev2"] * temperature
                transfer = coefficients["nDev"] * rate
                expected = {"development_rate": str(rate), "transport_rate": str(transfer)}
                for group in ("fruit_number", "fruit_carbohydrate"):
                    state = [Decimal(str(q["value"])) for q in values[group]]
                    # Decimal evaluation preserves small differences between large states.
                    expected["derivative_" + group] = [
                        str(transfer * ((state[j - 1] if j else Decimal(0)) - state[j]))
                        for j in range(stages)]
                    expected["outflow_" + group] = [str(transfer * v) for v in state]
                    expected["terminal_" + group] = str(transfer * state[-1])
                    expected["total_" + group] = str(sum(state))
                    assert sum(map(Decimal, expected["derivative_" + group])) + Decimal(
                        expected["terminal_" + group]) == 0
                cases.append({"case_id": case_id,
                    "state": {"input_id": case_id, "origin": "synthetic", "values": values},
                    "expected": expected})
    return {"fixture_version": "crop-fruit-transport-reference-cases-v1",
        "scope": "synthetic math only; no cultivar measurements or gate evidence",
        "reference_method": "60-digit Decimal source Eq9.31/9.32/9.34; difference-then-multiply; no product imports",
        "generator_version": VERSION, "generator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "profile_sha256": PROFILE_SHA256, "relative_error_budget": 5e-12,
        "absolute_error_budget": 5e-14, "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
        default=ROOT / "fixtures/crop-fruit-transport-reference-cases-v1.json")
    args = parser.parse_args()
    source = ROOT / "fixtures/crop-fruit-transport-reference-parameters-v1.json"
    if args.output.is_symlink() or args.output.resolve() in (source.resolve(), Path(__file__).resolve()):
        raise ValueError("reference_output_would_replace_input")
    document = references(source.read_bytes())
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    print(f"{VERSION}: {len(document['cases'])} synthetic reference cases")


if __name__ == "__main__":
    main()
