"""Create self-contained, editable Origin projects and graph files on Windows."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from plot_csv import read_columns
from visual_suite import _profile


X_LABELS = {"xrd": "2Theta (deg)", "raman": "Raman shift (cm^-1)",
            "ftir": "Wavenumber (cm^-1)"}
PALETTE = {"primary": "#006D83", "accent": "#B44826", "text": "#19313C", "background": "#FFFFFF"}


def safe_label(text):
    # Labels enter LabTalk commands. Restrict command and substitution characters.
    if not text or re.search(r'[\r\n";{}$\\]', text) or re.search(r'%[^\s)]', text):
        raise ValueError("Use plain labels without LabTalk commands or substitutions.")
    return text


def prepare(args):
    data = read_columns(args.csv, args.x, args.y)
    x = data[args.x]
    pairs = list(zip(x, x[1:]))
    if not pairs or not (all(a < b for a, b in pairs) or all(a > b for a, b in pairs)):
        raise ValueError("X must contain at least two strictly monotonic observations.")
    limits = tuple(args.x_range or (min(x), max(x)))
    if not min(x) <= limits[0] < limits[1] <= max(x):
        raise ValueError("X range must be increasing and within the recorded domain.")
    if not math.isfinite(args.offset):
        raise ValueError("Offset must be finite.")
    palette = _profile(json.loads(args.profile.read_text(encoding="utf-8-sig")))[0] if args.profile else PALETTE
    columns = [x, *[data[name] for name in args.y]]
    display_start = 1
    if args.offset:
        display_start = len(columns)
        shifted = [[value + index * args.offset for value in data[name]] for index, name in enumerate(args.y)]
        if any(math.isinf(value) for values in shifted for value in values):
            raise ValueError("Display offset overflows the numeric range.")
        columns.extend(shifted)
    labels = [safe_label(args.x), *[safe_label(name) for name in args.y]]
    if args.offset:
        labels.extend(safe_label(f"{name} ({index * args.offset:+g})") for index, name in enumerate(args.y))
    return {
        "schema_version": "1.0", "columns": [[None if math.isnan(v) else v for v in col] for col in columns],
        "labels": labels, "display_start": display_start, "series_count": len(args.y),
        "x_label": safe_label(args.x_label or X_LABELS.get(args.kind, args.x)),
        "y_label": safe_label(args.y_label + (f" (offset {args.offset:g} per series)" if args.offset else "")),
        "x_limits": limits[::-1] if (args.x_direction or ("descending" if args.kind == "ftir" else "ascending")) == "descending" else limits,
        "plot_id": 201 if args.kind == "scatter" else 200,
        "colors": [palette["primary"], palette["accent"], palette["text"]],
    }


def run_job(job, destination, powershell, script):
    if os.name != "nt":
        raise RuntimeError("Native export requires Windows with licensed Origin and its registered COM server.")
    powershell = powershell or Path(os.environ["WINDIR"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    if destination.exists():
        raise FileExistsError("Choose a new output directory.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".origin-native-", dir=destination.parent))
    try:
        if re.search(r'[";{}%$\r\n]', str(staging)):
            raise ValueError("Output directory contains unsupported LabTalk path characters.")
        payload = staging / "job.json"
        payload.write_text(json.dumps(job, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        command = [str(powershell), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                   "-File", str(script), "-JobPath", str(payload)]
        result = subprocess.run(command, capture_output=True, timeout=240)
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip() or "Origin native export failed.")
        for name in ("figure.opj", "figure.ogg", "preview.png", "verification.json"):
            if not (staging / name).is_file() or (staging / name).stat().st_size == 0:
                raise RuntimeError(f"Origin did not produce {name}.")
        payload.unlink()
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    print(destination / "figure.opj")
    print(destination / "figure.ogg")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--x", required=True)
    parser.add_argument("--y", required=True, action="append")
    parser.add_argument("--kind", choices=("line", "scatter", "xrd", "raman", "ftir"), default="line")
    parser.add_argument("--x-label")
    parser.add_argument("--y-label", required=True)
    parser.add_argument("--x-range", type=float, nargs=2)
    parser.add_argument("--x-direction", choices=("ascending", "descending"))
    parser.add_argument("--offset", type=float, default=0)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path, help="New directory for figure.opj, figure.ogg and preview.png.")
    parser.add_argument("--powershell", type=Path, help="PowerShell executable matching the registered Origin COM server.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        job = prepare(args)
        destination = args.output_dir.resolve()
        if destination.exists():
            raise FileExistsError("Choose a new output directory.")
        if args.dry_run:
            print(json.dumps({"rows": len(job["columns"][0]), "series": job["series_count"],
                              "output_dir": str(destination), "formats": ["opj", "ogg", "png"],
                              "missing_values": sum(v is None for col in job["columns"] for v in col)}, indent=2))
            return
        run_job(job, destination, args.powershell, Path(__file__).with_suffix(".ps1"))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
