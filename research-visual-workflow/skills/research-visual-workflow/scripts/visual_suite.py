"""Small, local helpers shared by the Visual Figure Suite skills."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


DEFAULTS = {
    "background": "#F8F5EF",
    "text": "#17304B",
    "primary": "#356B8C",
    "accent": "#D7794A",
}


def _rgb_hex(rgb):
    return "#" + "".join(f"{int(channel):02X}" for channel in rgb[:3])


def _rgb(color):
    value = color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected six-digit hex color: {color}")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _luminance(rgb):
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255


def extract_style(images):
    """Measure a palette. Typography and composition remain human/agent review fields."""
    from PIL import Image

    images = [Path(path) for path in images]
    if not images:
        raise ValueError("At least one reference image is required")
    swatches = []
    border_colors = []
    for path in images:
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((400, 400))
            width, height = image.size
            border_colors += [image.getpixel((0, 0)), image.getpixel((width - 1, 0)), image.getpixel((0, height - 1)), image.getpixel((width - 1, height - 1))]
            small = image.quantize(colors=12).convert("RGB")
            colors = small.getcolors(small.width * small.height) or []
            swatches += [(count, rgb) for count, rgb in colors]
    background = Counter(border_colors).most_common(1)[0][0]
    ranked = sorted(swatches, key=lambda item: item[0], reverse=True)
    candidates = [rgb for _, rgb in ranked if sum(abs(a - b) for a, b in zip(rgb, background)) > 70]
    colorful = sorted(candidates, key=lambda rgb: max(rgb) - min(rgb), reverse=True)
    primary = colorful[0] if colorful else _rgb(DEFAULTS["primary"])
    accent = next((rgb for rgb in colorful[1:] if sum(abs(a - b) for a, b in zip(rgb, primary)) > 100), _rgb(DEFAULTS["accent"]))
    text = (25, 35, 47) if _luminance(background) > 0.55 else (245, 247, 250)
    return {
        "schema_version": "1.0",
        "source_images": [path.name for path in images],
        "palette": {"background": _rgb_hex(background), "text": _rgb_hex(text), "primary": _rgb_hex(primary), "accent": _rgb_hex(accent)},
        "typography": {"heading_font": "Aptos Display", "body_font": "Aptos"},
        "visual_notes": {"composition": None, "type_character": None, "motifs": None},
        "measurement_note": "Palette is sampled automatically. Typography and visual notes require visual review.",
    }


def _profile(profile):
    if profile.get("schema_version") != "1.0":
        raise ValueError("style-profile schema_version must be 1.0")
    palette = {key: profile.get("palette", {}).get(key, value) for key, value in DEFAULTS.items()}
    for color in palette.values():
        _rgb(color)
    fonts = profile.get("typography", {})
    return palette, fonts.get("heading_font", "Aptos Display"), fonts.get("body_font", "Aptos")


def build_presentation(deck, profile, output):
    """Create a 16:9 deck using editable text and shapes."""
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches, Pt

    palette, heading_font, body_font = _profile(profile)
    if not isinstance(deck.get("slides"), list) or not deck["slides"]:
        raise ValueError("Deck requires a nonempty slides array")

    def color(key):
        return RGBColor(*_rgb(palette[key]))

    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    blank = presentation.slide_layouts[6]

    def rectangle(slide, x, y, w, h, fill):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = color(fill)
        shape.line.fill.background()
        return shape

    def text(slide, value, x, y, w, h, size, font=body_font, ink="text", bold=False):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        frame = box.text_frame
        frame.word_wrap = True
        frame.margin_left = frame.margin_right = Inches(0)
        frame.margin_top = frame.margin_bottom = Inches(0)
        para = frame.paragraphs[0]
        para.text = str(value)
        para.font.name = font
        para.font.size = Pt(size)
        para.font.bold = bold
        para.font.color.rgb = color(ink)
        return box

    for number, item in enumerate(deck["slides"], 1):
        kind = item.get("type")
        if kind not in {"title", "section", "bullets", "two-column", "metric"}:
            raise ValueError(f"Unsupported slide type: {kind}")
        slide = presentation.slides.add_slide(blank)
        rectangle(slide, 0, 0, 13.333, 7.5, "background")
        rectangle(slide, 0, 0, 0.12, 7.5, "primary")
        if kind == "title":
            rectangle(slide, 0.88, 1.18, 1.05, 0.1, "accent")
            text(slide, item.get("title", ""), 0.88, 1.62, 11.4, 2.0, 42, heading_font, bold=True)
            text(slide, item.get("subtitle", ""), 0.91, 4.1, 10.8, 1.0, 20)
        elif kind == "section":
            text(slide, f"{number:02d}", 0.88, 0.75, 1.2, 0.7, 19, ink="primary", bold=True)
            rectangle(slide, 0.88, 2.13, 0.17, 2.3, "accent")
            text(slide, item.get("title", ""), 1.38, 2.1, 10.9, 2.0, 38, heading_font, bold=True)
            text(slide, item.get("subtitle", ""), 1.4, 4.4, 10.2, 1.0, 18)
        else:
            text(slide, item.get("title", ""), 0.88, 0.66, 11.5, 0.9, 29, heading_font, bold=True)
            rectangle(slide, 0.88, 1.65, 1.05, 0.07, "accent")
            if kind == "bullets":
                bullets = item.get("bullets", [])
                if not 1 <= len(bullets) <= 5:
                    raise ValueError("Bullet slides require 1-5 bullet strings")
                for index, bullet in enumerate(bullets):
                    y = 2.05 + index * 0.96
                    rectangle(slide, 0.98, y + 0.18, 0.12, 0.12, "accent")
                    text(slide, bullet, 1.4, y, 10.9, 0.83, 21)
            elif kind == "two-column":
                for x, key in ((0.9, "left"), (6.82, "right")):
                    column = item.get(key, {})
                    rectangle(slide, x, 2.02, 5.58, 0.06, "primary")
                    text(slide, column.get("heading", ""), x, 2.3, 5.25, 0.7, 23, heading_font, bold=True)
                    text(slide, column.get("body", ""), x, 3.16, 5.18, 3.7, 18)
            elif kind == "metric":
                text(slide, item.get("value", ""), 0.89, 2.04, 8.7, 2.25, 68, heading_font, "primary", True)
                text(slide, item.get("label", ""), 0.94, 4.3, 10.6, 0.8, 22, bold=True)
                text(slide, item.get("note", ""), 0.94, 5.2, 10.6, 0.9, 16)
        text(slide, f"{number:02d}", 11.96, 7.08, 0.55, 0.25, 10, ink="primary")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing presentation: {output}")
    presentation.save(output)
    return output


def prepare_origin_job(csv_path, x_column, y_columns, output_stem, kind, x_label=None, y_label=None):
    """Validate numeric CSV data before opening or changing Origin."""
    csv_path = Path(csv_path)
    if kind not in {"line", "scatter"}:
        raise ValueError("Origin plot kind must be line or scatter")
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headings = reader.fieldnames or []
        if x_column not in headings or not y_columns or any(name not in headings for name in y_columns):
            raise ValueError(f"CSV columns not found. Available: {headings}")
        rows = list(reader)
    if not rows:
        raise ValueError("CSV has no data rows")
    for row_number, row in enumerate(rows, 2):
        for name in [x_column] + list(y_columns):
            try:
                float(row[name])
            except (TypeError, ValueError) as error:
                raise ValueError(f"Non-numeric value in row {row_number}, column {name}") from error
    output_stem = Path(output_stem)
    existing = [str(output_stem.with_suffix(suffix)) for suffix in (".opju", ".png") if output_stem.with_suffix(suffix).exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite existing Origin output: {', '.join(existing)}")
    return {"csv": str(csv_path.resolve()), "x_column": x_column, "y_columns": list(y_columns), "x_label": x_label or x_column, "y_label": y_label or (y_columns[0] if len(y_columns) == 1 else "Value"), "output_stem": str(output_stem.resolve()), "kind": kind, "rows": len(rows)}


def render_origin(job, profile):
    """Run only on a machine with Origin/OriginPro and the originpro Python package."""
    try:
        import originpro as op
    except ImportError as error:
        raise RuntimeError("Origin is unavailable. Install Origin/OriginPro and its originpro Python package, or use --dry-run.") from error
    palette, _, _ = _profile(profile)
    with Path(job["csv"]).open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    stem = Path(job["output_stem"])
    stem.parent.mkdir(parents=True, exist_ok=True)
    if op.oext:
        op.set_show(True)
    try:
        op.new(asksave=True)
        sheet = op.new_sheet('w', stem.name)
        sheet.from_list(0, [float(row[job["x_column"]]) for row in rows], lname=job["x_column"])
        for index, name in enumerate(job["y_columns"], 1):
            sheet.from_list(index, [float(row[name]) for row in rows], lname=name)
        graph = op.new_graph(lname=stem.name)
        layer = graph[0]
        colors = [palette["primary"], palette["accent"], palette["text"]]
        for index, _name in enumerate(job["y_columns"], 1):
            plot = layer.add_plot(sheet, coly=index, colx=0, type='l' if job["kind"] == "line" else 's')
            plot.color = colors[(index - 1) % len(colors)]
        layer.rescale()
        layer.axis('x').title = job["x_label"]
        layer.axis('y').title = job["y_label"]
        layer.label('Legend').text = "\n".join(f"\\l({index}) {name}" for index, name in enumerate(job["y_columns"], 1))
        project = stem.with_suffix(".opju")
        png = stem.with_suffix(".png")
        if not op.save(str(project)):
            raise RuntimeError("Origin did not save the project")
        if not graph.save_fig(str(png), type="png", width=1600):
            raise RuntimeError("Origin did not export the PNG")
        return project, png
    finally:
        if op.oext:
            op.exit()


def main():
    parser = argparse.ArgumentParser(description="Visual Figure Suite helpers")
    commands = parser.add_subparsers(dest="command", required=True)
    style = commands.add_parser("style", help="Extract measured palette from reference images")
    style.add_argument("images", nargs="+")
    style.add_argument("--output", required=True)
    ppt = commands.add_parser("ppt", help="Create editable PPTX from deck JSON")
    ppt.add_argument("--deck", required=True)
    ppt.add_argument("--profile", required=True)
    ppt.add_argument("--output", required=True)
    origin = commands.add_parser("origin", help="Create Origin line/scatter graph from CSV")
    origin.add_argument("--csv", required=True)
    origin.add_argument("--x", required=True)
    origin.add_argument("--y", action="append", required=True)
    origin.add_argument("--kind", choices=["line", "scatter"], default="line")
    origin.add_argument("--x-label")
    origin.add_argument("--y-label")
    origin.add_argument("--profile", required=True)
    origin.add_argument("--output-stem", required=True)
    origin.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "style":
        result = extract_style(args.images)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            raise FileExistsError(f"Refusing to overwrite existing style profile: {output}")
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(output)
    elif args.command == "ppt":
        deck = json.loads(Path(args.deck).read_text(encoding="utf-8"))
        profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
        print(build_presentation(deck, profile, args.output))
    else:
        profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
        job = prepare_origin_job(args.csv, args.x, args.y, args.output_stem, args.kind, args.x_label, args.y_label)
        _profile(profile)
        if args.dry_run:
            print(json.dumps(job, ensure_ascii=False, indent=2))
        else:
            print(render_origin(job, profile))


if __name__ == "__main__":
    main()
