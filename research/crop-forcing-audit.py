"""Inspect unchanged AGC Reference CSV bytes; never produce model forcing."""
import argparse
import csv
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
from pathlib import Path

VERSION = "agc-reference-raw-qc-v1"
FILES = [f"Reference/{name}.csv" for name in ["CropParameters", "GreenhouseClimate",
    "GrodanSens", "LabAnalysis", "Production", "Resources", "TomQuality"]] + ["Weather/Weather.csv"]


def inspect_file(path: Path):
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("audit_file_size_limit")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream)
        raw_header = next(rows)
        header = [n.strip().lstrip("%") if i == 0 else n.strip() for i, n in enumerate(raw_header)]
        columns = [{"name": n, "missing": 0, "non_numeric": 0, "finite": 0,
            "minimum": None, "maximum": None} for n in header]
        count = included = malformed = 0
        malformed_examples, invalid_time_lines = [], []
        times, deltas = [], {}
        previous = None
        physical = {"negative_co2": 0, "relative_humidity_outside_0_100": 0,
            "negative_PAR": 0, "negative_Tair": 0, "missing_CO2_Tair_PAR_joint": 0}
        out_of_trial_lines = []
        for line, row in enumerate(rows, 2):
            if not row or all(not cell.strip() for cell in row):
                continue
            count += 1
            if count > 100000:
                raise ValueError("audit_row_limit")
            try:
                at = Decimal(row[0].strip())
                if not at.is_finite() or not Decimal(1) <= at <= Decimal(100000):
                    raise ValueError("invalid_excel_candidate")
                times.append(at)
                if previous is not None:
                    delta = str(at - previous)
                    deltas[delta] = deltas.get(delta, 0) + 1
                previous = at
                if path.name == "Production.csv" and not Decimal(43815) <= at <= Decimal(43980):
                    out_of_trial_lines.append(line)
            except (InvalidOperation, ValueError):
                invalid_time_lines.append(line)
            if len(row) != len(header):
                malformed += 1
                if len(malformed_examples) < 20:
                    malformed_examples.append({"line": line, "columns": len(row)})
                continue
            included += 1
            values = {}
            for column, cell in zip(columns, row):
                try:
                    number = float(cell.strip())
                except ValueError:
                    column["non_numeric"] += 1
                    continue
                values[column["name"]] = number
                if not math.isfinite(number):
                    column["missing"] += 1
                    continue
                column["finite"] += 1
                column["minimum"] = number if column["minimum"] is None else min(number, column["minimum"])
                column["maximum"] = number if column["maximum"] is None else max(number, column["maximum"])
            if path.name == "GreenhouseClimate.csv":
                def present(key):
                    return key in values and math.isfinite(values[key])
                physical["negative_co2"] += present("CO2air") and values["CO2air"] < 0
                physical["relative_humidity_outside_0_100"] += present("Rhair") and not 0 <= values["Rhair"] <= 100
                physical["negative_PAR"] += present("Tot_PAR") and values["Tot_PAR"] < 0
                physical["negative_Tair"] += present("Tair") and values["Tair"] < 0
                physical["missing_CO2_Tair_PAR_joint"] += any(not present(k) for k in ["CO2air", "Tair", "Tot_PAR"])
    minimum, maximum = (min(times), max(times)) if times else (None, None)
    epoch = datetime(1899, 12, 30)
    return {"bytes": path.stat().st_size, "raw_sha256": sha256(path.read_bytes()).hexdigest(),
        "rows": count, "schema_valid_rows": included, "raw_header": raw_header, "header": header,
        "columns": columns, "column_count_mismatches": malformed,
        "malformed_examples": malformed_examples, "invalid_time_lines": invalid_time_lines,
        "time": {"representation": "Excel_serial; epoch_candidate_1899_12_30; timezone_unknown",
            "minimum_raw": str(minimum) if minimum is not None else None,
            "maximum_raw": str(maximum) if maximum is not None else None,
            "duplicate_or_backward_deltas": {d: n for d, n in deltas.items() if Decimal(d) <= 0},
            "delta_days_counts": deltas,
            "naive_minimum_if_1899_12_30": (epoch + timedelta(days=float(minimum))).isoformat() if minimum is not None else None,
            "naive_maximum_if_1899_12_30": (epoch + timedelta(days=float(maximum))).isoformat() if maximum is not None else None},
        "physical_counts": physical if path.name == "GreenhouseClimate.csv" else None,
        "production_outside_2019_12_16_to_2020_05_29_lines": out_of_trial_lines if path.name == "Production.csv" else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    paths = [root / name for name in FILES]
    if any(not p.is_file() or p.is_symlink() for p in paths) or sum(p.stat().st_size for p in paths) > 32 * 1024 * 1024:
        raise ValueError("audit_inputs_invalid")
    if args.output.is_symlink() or args.output.resolve() in {p.resolve() for p in paths}:
        raise ValueError("audit_output_would_replace_source")
    report = {"inspector_version": VERSION, "status": "research_QC_not_G0_approval",
        "source_mutated": False, "utc_forcing_created": False,
        "statistics_rows": "schema-valid rows only; malformed rows remain rejected",
        "files": {name: inspect_file(root / name) for name in FILES}}
    clock = report["files"]["Reference/GreenhouseClimate.csv"]["time"]
    serial_days = Decimal(clock["maximum_raw"]) - Decimal(clock["minimum_raw"])
    report["source_capacity_arithmetic"] = {"serial_days": str(serial_days),
        "seconds_if_uniform_serial_clock": str(serial_days * 86400),
        "minimum_steps_if_uniform_clock_and_10_seconds": int((serial_days * 86400 / 10).to_integral_value(rounding="ROUND_CEILING")),
        "actual_UTC_solver_plan": False, "source_timezone_DST_and_extra_boundaries_unresolved": True}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"{VERSION}: inspected {len(FILES)} unchanged CSV files; no model input produced")


if __name__ == "__main__":
    main()
