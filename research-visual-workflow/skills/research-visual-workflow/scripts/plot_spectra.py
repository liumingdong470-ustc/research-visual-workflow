"""Redraw XRD, Raman or FTIR spectra from CSV without processing their signal."""

import argparse
import json
import math
from pathlib import Path

from plot_csv import read_columns
from visual_suite import _profile


X_LABELS = {
    "xrd": "2θ (°)",
    "raman": "Raman shift (cm⁻¹)",
    "ftir": "Wavenumber (cm⁻¹)",
}
PALETTE = {
    "background": "#FFFFFF", "text": "#162C3B", "primary": "#006D83", "accent": "#B44826",
}
LINESTYLES = ["-", (0, (6, 2.4)), "-.", ":"]


def draw_spectra(ax, x, traces, *, kind, y_label, limits, descending=False,
                 x_label=None, marks=(), offset=0.0, palette=None):
    colors = PALETTE if palette is None else palette
    ax.set_facecolor(colors["background"])
    series_colors = [colors["primary"], colors["accent"], colors["text"]]
    for index, (name, values) in enumerate(traces.items()):
        shift = index * offset
        label = f"{name} ({shift:+.6g})" if shift else name
        plotted = [value + shift for value in values] if shift else values
        ax.plot(x, plotted, label=label, color=series_colors[index % len(series_colors)],
                lw=1.15, ls=LINESTYLES[index % len(LINESTYLES)], zorder=3)
    ax.set_xlim(limits[::-1] if descending else limits)
    ax.set_xlabel(x_label or X_LABELS[kind], color=colors["text"])
    ax.set_ylabel(f"{y_label} (offset)" if offset else y_label, color=colors["text"])
    ax.spines[["top", "right"]].set_visible(False)
    for name in ("left", "bottom"):
        ax.spines[name].set(color=colors["text"], linewidth=0.65)
    ax.tick_params(colors=colors["text"], direction="out", width=0.65)
    for position in marks:
        ax.axvline(position, color=colors["text"], lw=0.65, ls=":", alpha=0.65, zorder=1)
        ax.annotate(f"{position:.8g}", (position, 1), xycoords=ax.get_xaxis_transform(),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                    fontsize=7, color=colors["text"], annotation_clip=False)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.16 if marks else 1.02),
              ncol=min(len(traces), 3), borderaxespad=0, frameon=False,
              labelcolor=colors["text"], fontsize=7, handlelength=2.5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--kind", required=True, choices=tuple(X_LABELS))
    parser.add_argument("--x", required=True)
    parser.add_argument("--y", required=True, action="append")
    parser.add_argument("--x-label", help="Override the default only with the verified quantity and unit.")
    parser.add_argument("--y-label", required=True, help="Verified quantity and unit from the instrument.")
    parser.add_argument("--x-direction", choices=("ascending", "descending"))
    parser.add_argument("--x-range", type=float, nargs=2, metavar=("LOW", "HIGH"))
    parser.add_argument("--mark", action="append", type=float, default=[], help="Known reference position. Repeat as needed.")
    parser.add_argument("--offset", type=float, default=0, help="Vertical increment in original Y units per series.")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--width-mm", type=float, default=120)
    parser.add_argument("--height-mm", type=float, default=80)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    fmt = args.output.suffix.lower().lstrip(".")
    if fmt not in {"png", "svg", "pdf"} or args.output.exists():
        parser.error("Choose a new output filename ending in .png, .svg or .pdf.")
    if not all(math.isfinite(size) and size > 0 for size in (args.width_mm, args.height_mm)):
        parser.error("Figure dimensions must be finite and positive.")
    if not math.isfinite(args.offset):
        parser.error("Offset must be finite.")
    try:
        values = read_columns(args.csv, args.x, args.y)
        palette = _profile(json.loads(args.profile.read_text(encoding="utf-8-sig")))[0] if args.profile else PALETTE
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    x = values[args.x]
    pairs = list(zip(x, x[1:]))
    if not pairs or not (all(a < b for a, b in pairs) or all(a > b for a, b in pairs)):
        parser.error("X needs at least two strictly monotonic observations. Verify scan boundaries and duplicate X values.")
    limits = tuple(args.x_range or (min(x), max(x)))
    low, high = limits
    if not (min(x) <= low < high <= max(x)):
        parser.error("X range must be increasing and within the recorded domain.")
    if any(not low <= mark <= high for mark in args.mark):
        parser.error("Marked positions must be within the displayed X range.")
    if len(set(args.mark)) != len(args.mark):
        parser.error("Marked positions must be unique.")
    descending = (args.x_direction or ("descending" if args.kind == "ftir" else "ascending")) == "descending"

    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    with plt.rc_context({"font.family": "sans-serif",
                         "font.sans-serif": ["DejaVu Sans", "Microsoft YaHei", "Noto Sans CJK SC"],
                         "font.size": 8, "pdf.fonttype": 42, "svg.fonttype": "none"}):
        fig, ax = plt.subplots(figsize=(args.width_mm / 25.4, args.height_mm / 25.4), layout="constrained")
        fig.patch.set_facecolor(palette["background"])
        draw_spectra(ax, x, {name: values[name] for name in args.y}, kind=args.kind,
                     y_label=args.y_label, limits=limits, descending=descending,
                     x_label=args.x_label, marks=args.mark, offset=args.offset, palette=palette)
        # Measure the layout with the preview renderer's glyph fallback before vector export.
        fig.canvas.draw()
        fig.set_layout_engine("none")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as output:
            fig.savefig(output, format=fmt, dpi=400)
        plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
