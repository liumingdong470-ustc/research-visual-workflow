"""Build editable Origin grouped bars, stacks, matrix heatmaps and panels from JSON."""

import argparse
import json
import math
from pathlib import Path
import subprocess

from origin_native import run_job, safe_label

THEMES = {
    "default": ["#202020", "#C4473B", "#386DB1", "#2A8562"],
    "clean": ["#444D5A", "#A78062", "#688094", "#BAC3CD"],
    "skill": ["#176D75", "#B45837", "#527BB2", "#AB8A46"],
}


def numbers(values, *, length=None, missing=False):
    if not isinstance(values, list) or not values or (length is not None and len(values) != length):
        raise ValueError("Numeric arrays must be nonempty and match the declared dimensions.")
    for value in values:
        if value is None and missing:
            continue
        if type(value) not in (int, float) or not math.isfinite(value) or value == -1.23456789e-300:
            raise ValueError("Use finite numbers and JSON null for missing observations.")
    return values


def bounds(value):
    limits = numbers(value, length=2)
    if not limits[0] < limits[1]:
        raise ValueError("Axis and scale limits must be in increasing order.")
    return limits


def grid(values, size):
    axis = numbers(values, length=size)
    step = (axis[-1] - axis[0]) / (size - 1)
    if not math.isfinite(step) or step <= 0 or any(
            not math.isclose(b - a, step, rel_tol=1e-9) for a, b in zip(axis, axis[1:])):
        raise ValueError("Native matrix axes require regularly spaced ascending coordinates.")
    return [axis[0], axis[-1], step]


def label(spec, key, default):
    value = spec.get(key, default)
    if not isinstance(value, str) or len(value) > 72:
        raise ValueError(f"{key} must be plain text of at most 72 characters.")
    return safe_label(value)


def prepare_heatmap(spec, panel):
    matrix = spec.get("matrix")
    if not isinstance(matrix, list) or not 2 <= len(matrix) <= 250 or not isinstance(matrix[0], list) or not 2 <= len(matrix[0]) <= 250:
        raise ValueError("A heatmap requires a rectangular matrix with 2–250 rows and columns.")
    rows, columns = len(matrix), len(matrix[0])
    values = [value for row in matrix for value in numbers(row, length=columns, missing=True) if value is not None]
    if not values:
        raise ValueError("A heatmap requires at least one observed value.")
    if rows * columns - len(values) > 36:
        raise ValueError("Origin 2016 heatmaps in this workflow support up to 36 explicitly labeled missing cells.")
    limits = spec.get("scale")
    if limits is None and min(values) == max(values):
        raise ValueError("Give a nonzero color scale for a constant matrix.")
    limits = bounds([min(values), max(values)] if limits is None else limits)
    if limits[0] > min(values) or limits[1] < max(values):
        raise ValueError("Color scale must contain all observed values.")
    palette = spec.get("palette", "sequential")
    if palette not in ("sequential", "diverging"):
        raise ValueError("Choose a sequential or diverging palette.")
    if palette == "diverging" and not (limits[1] > 0 and math.isclose(limits[0], -limits[1])):
        raise ValueError("A diverging color scale requires symmetric limits around zero.")
    panel.update(matrix=matrix, scale=limits, palette=palette, expected_plots=1,
                 x=grid(spec.get("x", list(range(1, columns + 1))), columns),
                 y=grid(spec.get("y", list(range(1, rows + 1))), rows),
                 z_label=label(spec, "z_label", "Value"))
    return panel


def prepare_series(spec, panel):
    kind = panel["kind"]
    bars = kind in ("grouped-bar", "stacked-bar")
    if bars:
        x = spec.get("categories")
        if not isinstance(x, list) or not x or any(not isinstance(v, str) or not v.strip() for v in x) or len(set(x)) != len(x):
            raise ValueError("Give unique, nonempty category labels in the desired order.")
    else:
        x = numbers(spec.get("x"))
        if len(x) < 2 or any(b <= a for a, b in zip(x, x[1:])):
            raise ValueError("Line and scatter panels require strictly ascending numeric X values.")
    series = spec.get("series")
    if not isinstance(series, list) or not 1 <= len(series) <= 4 or any(not isinstance(s, dict) for s in series):
        raise ValueError("Give one to four series per panel.")
    columns, labels, error_columns, value_columns = [x], [panel["x_label"]], [], []
    errors_present = any("errors" in s for s in series)
    if errors_present and kind != "grouped-bar":
        raise ValueError("Symmetric errors are supported for grouped bars only.")
    uncertainty = label(spec, "error_kind", "") if errors_present else ""
    for item in series:
        name = label(item, "name", "")
        if name in labels:
            raise ValueError("Series names must be unique.")
        values = numbers(item.get("values"), length=len(x), missing=kind != "stacked-bar")
        if all(value is None for value in values):
            raise ValueError("Each series needs an observed value.")
        if kind == "stacked-bar" and any(value < 0 for value in values):
            raise ValueError("Stacked components must be complete and nonnegative.")
        columns.append(values)
        labels.append(name)
        value_columns.append(len(columns))
        if "errors" in item:
            errors = numbers(item["errors"], length=len(x), missing=True)
            if any(error is not None and (error < 0 or value is None) for value, error in zip(values, errors)):
                raise ValueError("Errors must be nonnegative and correspond to observed values.")
            columns.append(errors)
            labels.append(f"{name} {uncertainty}")
            error_columns.append([value_columns[-1], len(columns)])
    limits = bounds(spec["y_range"]) if "y_range" in spec else None
    if limits:
        if kind == "stacked-bar":
            required = [0, *[sum(values) for values in zip(*(columns[i - 1] for i in value_columns))]]
        else:
            required = [v for i in value_columns for v in columns[i - 1] if v is not None]
            for mean, error in error_columns:
                for value, delta in zip(columns[mean - 1], columns[error - 1]):
                    if value is not None and delta is not None:
                        required.extend((value - delta, value + delta))
            if bars:
                required.append(0)
        if min(required) < limits[0] or max(required) > limits[1]:
            raise ValueError("Y range must contain the data, error bars, and zero baseline for bars.")
    panel.update(columns=columns, labels=labels, value_columns=value_columns, error_columns=error_columns,
                 expected_plots=len(series) + len(error_columns), y_range=limits, categorical=bars,
                 uncertainty=uncertainty)
    return panel


def prepare(spec, theme):
    if not isinstance(spec, dict):
        raise ValueError("The plot specification must be a JSON object.")
    if spec.get("kind") == "panels":
        rows, columns, items = spec.get("rows"), spec.get("columns"), spec.get("panels")
        if type(rows) is not int or type(columns) is not int or min(rows, columns) < 1 or not 2 <= rows * columns <= 6:
            raise ValueError("A panel grid must have two to six positions.")
        if not isinstance(items, list) or len(items) != rows * columns:
            raise ValueError("Supply one specification for each panel position.")
    else:
        rows, columns, items = 1, 1, [spec]
    panels = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict) or item.get("kind") not in ("grouped-bar", "stacked-bar", "heatmap", "line", "scatter"):
            raise ValueError("Unsupported panel kind.")
        panel = {"kind": item["kind"], "book": f"Source{index}",
                 "x_label": label(item, "x_label", "X"), "y_label": label(item, "y_label", "Y"),
                 "title": label(item, "title", f"Panel {index}")}
        panels.append(prepare_heatmap(item, panel) if item["kind"] == "heatmap" else prepare_series(item, panel))
    return {"panels": panels, "rows": rows, "columns": columns, "colors": THEMES[theme], "theme": theme}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--theme", choices=THEMES, default="skill")
    parser.add_argument("--powershell", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        job = prepare(json.loads(args.spec.read_text(encoding="utf-8-sig")), args.theme)
        destination = args.output_dir.resolve()
        if destination.exists():
            raise FileExistsError("Choose a new output directory.")
        if args.dry_run:
            print(json.dumps({"layers": len(job["panels"]), "kinds": [p["kind"] for p in job["panels"]],
                              "missing": sum(v is None for p in job["panels"]
                                             for row in p.get("matrix", p.get("columns")) for v in row)}))
            return
        run_job(job, destination, args.powershell, Path(__file__).with_suffix(".ps1"))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
