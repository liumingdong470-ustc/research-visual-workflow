"""Render a local CSV as a PNG or SVG without changing source data."""
import argparse
import csv
import json
import math
from pathlib import Path

from visual_suite import DEFAULTS, _profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--x", required=True)
    parser.add_argument("--y", required=True, action="append")
    parser.add_argument("--x-label", required=True)
    parser.add_argument("--y-label", required=True)
    parser.add_argument("--kind", choices=("line", "scatter"), default="line")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.suffix.lower() not in {".png", ".svg", ".pdf"}:
        parser.error("Output extension must be .png, .svg or .pdf.")
    if args.output.exists():
        parser.error("Choose a new output filename.")
    columns = [args.x, *args.y]
    if len(set(columns)) != len(columns):
        parser.error("Use different columns for X and each series.")
    values = {key: [] for key in columns}
    with args.csv.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers) or any(c not in headers for c in columns):
            parser.error("CSV headings must be unique and include all selected columns.")
        for index, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                parser.error(f"Row {index} has a different number of fields.")
            for key in columns:
                value = row[key].strip()
                if not value and key != args.x:
                    values[key].append(float("nan"))
                    continue
                try:
                    number = float(value)
                except ValueError:
                    parser.error(f"Row {index}, column {key} is not a number.")
                if not math.isfinite(number):
                    parser.error(f"Row {index}, column {key} is non-finite.")
                values[key].append(number)
    if not values[args.x] or any(not any(math.isfinite(v) for v in values[key]) for key in args.y):
        parser.error("Each series must contain observations.")
    profile = json.loads(args.profile.read_text(encoding="utf-8")) if args.profile else {"schema_version": "1.0", "palette": DEFAULTS}
    colors, _, _ = _profile(profile)
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.6), layout="constrained")
    fig.patch.set_facecolor(colors["background"])
    ax.set_facecolor(colors["background"])
    markers = ["o", "s", "^", "D", "v", "P", "X"]
    lines = ["-", "--", "-.", ":"]
    series_colors = [colors["primary"], colors["accent"], colors["text"]]
    for index, key in enumerate(args.y):
        ax.plot(values[args.x], values[key], label=key, color=series_colors[index % len(series_colors)],
                marker=markers[index % len(markers)], markersize=4,
                linestyle=lines[index % len(lines)] if args.kind == "line" else "none", linewidth=1.5)
    ax.set_xlabel(args.x_label, color=colors["text"])
    ax.set_ylabel(args.y_label, color=colors["text"])
    ax.tick_params(colors=colors["text"], direction="in")
    for spine in ax.spines.values():
        spine.set_color(colors["text"])
    ax.legend(frameon=False, labelcolor=colors["text"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as output:
        fig.savefig(output, format=args.output.suffix[1:].lower(), dpi=300)
    print(args.output)


if __name__ == "__main__":
    main()
