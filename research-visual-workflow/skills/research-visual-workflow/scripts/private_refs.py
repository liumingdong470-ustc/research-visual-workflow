"""Local reference library front end; compatible with the Visual Figure Suite catalog."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import style_library as db

LOCAL = Path.home() / ".research-visual-workflow"
SETTINGS = LOCAL / "settings.json"
SKILL = Path(__file__).resolve().parents[1]
TYPES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def protected_path(path):
    path = Path(path).expanduser().resolve()
    if path.is_relative_to(SKILL):
        raise ValueError("Choose a private folder outside the installed Skill directory.")
    for ancestor in (path, *path.parents):
        if (ancestor / ".git").exists() or (ancestor / "publication-files.json").exists():
            raise ValueError("Choose a private folder outside the Git working tree or public release folder.")
    return path


def library_path(explicit=None):
    if explicit:
        path = explicit
    elif SETTINGS.is_file():
        path = json.loads(SETTINGS.read_text(encoding="utf-8"))["library"]
    else:
        path = LOCAL / "library"
    root = protected_path(path)
    for name in ("assets", "profiles", "styles.sqlite", "catalog.json", "inbox"):
        child = root / name
        if child.resolve() != child:
            raise ValueError(f"Private library entry must not be redirected: {name}")
    return root


def add(root, args):
    sources = [Path(p) for p in args.image or []]
    if args.inbox:
        folder = root / "inbox"
        folder.mkdir(parents=True, exist_ok=True)
        sources = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in TYPES)
    if args.profile and len(sources) != 1:
        raise ValueError("A reviewed profile must correspond to exactly one image.")
    if args.title and len(sources) != 1:
        raise ValueError("A custom title must correspond to exactly one image.")
    result = {"added": 0, "reused": 0, "items": [], "errors": []}
    if not sources:
        return result
    if not (root / "styles.sqlite").is_file():
        db.init_library(root)
    for source in sources:
        try:
            if source.is_symlink() or source.suffix.lower() not in TYPES:
                raise ValueError("Supply a supported local image file.")
            checksum = hashlib.sha256(source.read_bytes()).hexdigest()
            with db._connection(root) as conn:
                already = conn.execute("SELECT id FROM styles WHERE sha256 = ?", (checksum,)).fetchone()
            record = db.add_image(root, source, args.title or source.stem, args.tag, args.profile)
            result["reused" if already else "added"] += 1
            result["items"].append({"id": record["id"], "title": record["title"]})
        except (OSError, ValueError, sqlite3.Error) as error:
            result["errors"].append({"file": source.name, "error": str(error)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    for name in ("configure", "status", "init", "inbox", "add", "list", "search", "show"):
        sub = actions.add_parser(name)
        sub.add_argument("--library", required=(name == "configure"))
        if name == "add":
            group = sub.add_mutually_exclusive_group(required=True)
            group.add_argument("--image", action="append")
            group.add_argument("--inbox", action="store_true")
            sub.add_argument("--title")
            sub.add_argument("--tag", action="append", default=[])
            sub.add_argument("--profile")
        elif name == "search":
            sub.add_argument("--query", required=True)
        elif name == "show":
            sub.add_argument("--id", required=True)
    args = parser.parse_args()
    try:
        root = library_path(args.library)
        if args.action == "configure":
            protected_path(SETTINGS.parent)
            SETTINGS.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS.write_text(json.dumps({"library": str(root)}, ensure_ascii=False) + "\n", encoding="utf-8")
            result = {"library": str(root), "initialized": (root / "styles.sqlite").is_file()}
        elif args.action == "status":
            result = {"library": str(root), "initialized": (root / "styles.sqlite").is_file()}
        elif args.action == "init":
            db.init_library(root)
            result = {"library": str(root)}
        elif args.action == "inbox":
            (root / "inbox").mkdir(parents=True, exist_ok=True)
            result = {"inbox": str(root / "inbox")}
        elif args.action == "add":
            result = add(root, args)
        elif args.action == "list":
            result = db.list_library(root)
        elif args.action == "search":
            result = db.search_library(root, args.query)
        else:
            result = db.get_record(root, args.id, include_profile=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if isinstance(result, dict) and result.get("errors") else 0
    except (OSError, ValueError, KeyError, sqlite3.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
