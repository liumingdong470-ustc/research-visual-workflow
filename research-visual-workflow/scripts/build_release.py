"""Build the publication ZIP from the explicit text-only allowlist."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
NAME = "research-visual-workflow"
MARKERS = (r"[a-z]:[\\/]+Users[\\/]+[^\\/\r\n]+[\\/]", r"/" + r"home/[^/\s]+/",
           r"sk-(?:proj-)?[A-Za-z0-9_-]{24,}", r"-----BEGIN " + r"(?:[A-Z ]+ )?PRIVATE KEY-----")


def build(destination):
    names = json.loads((ROOT / "publication-files.json").read_text(encoding="utf-8"))["files"]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate release paths.")
    payload = {}
    for name in names:
        p = PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name:
            raise ValueError(f"Unsafe release path: {name}")
        if name not in {"LICENSE", ".gitignore"} and p.suffix.lower() not in {".md", ".json", ".py", ".txt", ".csv"}:
            raise ValueError(f"Release expects text files: {name}")
        if any(part in {"assets", "profiles", "inbox", "private", ".git"} for part in p.parts) or p.name in {"catalog.json", "local-setup.md", "settings.json"}:
            raise ValueError(f"Private path in release manifest: {name}")
        source = ROOT.joinpath(*p.parts)
        if source.resolve() != source or source.stat().st_size > 256_000:
            raise ValueError(f"Redirected or unexpectedly large file: {name}")
        raw = source.read_bytes()
        text = raw.decode("utf-8")
        if "\x00" in text or any(re.search(pattern, text, re.IGNORECASE) for pattern in MARKERS):
            raise ValueError(f"Review potential personal path or credential in: {name}")
        payload[f"{NAME}/{name}"] = raw
    with ZipFile(destination, "x", ZIP_DEFLATED) as archive:
        for name, raw in payload.items():
            archive.writestr(name, raw)
    with ZipFile(destination) as archive:
        if set(archive.namelist()) != set(payload) or archive.testzip() is not None:
            raise RuntimeError("Release verification failed.")
    print(f"{destination}: {len(payload)} explicitly approved text files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
