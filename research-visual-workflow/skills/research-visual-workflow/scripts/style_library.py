"""Portable SQLite catalog for reference-image style profiles."""

import argparse
import hashlib
import json
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from visual_suite import DEFAULTS, _profile, extract_style


def _db_path(root):
    return Path(root) / "styles.sqlite"


def _connect(root):
    path = _db_path(root)
    if not path.is_file():
        raise FileNotFoundError(f"Style library not initialized: {path}")
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def _connection(root):
    connection = _connect(root)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _json(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _check_profile(profile):
    if not isinstance(profile, dict) or not all(key in profile.get("palette", {}) for key in DEFAULTS):
        raise ValueError("Profile requires background, text, primary, and accent colors")
    _profile(profile)


def _safe_file(root, relative):
    root = Path(root).resolve()
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Library path escapes its root")
    return target


def _row_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "tags": json.loads(row["tags_json"]),
        "asset": row["asset"],
        "profile": row["profile"],
        "added_at": row["added_at"],
        "updated_at": row["updated_at"],
    }


def _search_text(title, tags, profile):
    return " ".join([title] + list(tags) + [json.dumps(profile, ensure_ascii=False)]).casefold()


def _catalog(root):
    root = Path(root)
    with _connection(root) as connection:
        records = [_row_dict(row) for row in connection.execute("SELECT * FROM styles ORDER BY title COLLATE NOCASE, id")]
    (root / "catalog.json").write_text(_json({"schema_version": "1.0", "styles": records}), encoding="utf-8")
    return records


def init_library(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "assets").mkdir(exist_ok=True)
    (root / "profiles").mkdir(exist_ok=True)
    if not _db_path(root).exists():
        sqlite3.connect(_db_path(root)).close()
    with _connection(root) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS styles (
                id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                asset TEXT NOT NULL,
                profile TEXT NOT NULL,
                search_text TEXT NOT NULL,
                added_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
    _catalog(root)
    return root


def list_library(root):
    with _connection(root) as connection:
        return [_row_dict(row) for row in connection.execute("SELECT * FROM styles ORDER BY title COLLATE NOCASE, id")]


def _get_row(connection, style_id):
    matches = list(connection.execute("SELECT * FROM styles WHERE id LIKE ?", (style_id + "%",)))
    if not matches:
        raise KeyError(f"Style not found: {style_id}")
    if len(matches) > 1:
        raise ValueError(f"Ambiguous style ID prefix: {style_id}")
    return matches[0]


def get_record(root, style_id, include_profile=False):
    with _connection(root) as connection:
        record = _row_dict(_get_row(connection, style_id))
    if include_profile:
        record["style_profile"] = json.loads(_safe_file(root, record["profile"]).read_text(encoding="utf-8"))
    return record


def search_library(root, query):
    with _connection(root) as connection:
        rows = connection.execute("SELECT * FROM styles WHERE search_text LIKE ? ORDER BY title COLLATE NOCASE, id", ("%" + query.casefold() + "%",))
        return [_row_dict(row) for row in rows]


def add_image(root, image_path, title, tags=None, profile_path=None):
    from PIL import Image

    root = Path(root)
    title = title.strip()
    if not title:
        raise ValueError("A nonempty title is required")
    tags = list(dict.fromkeys(tag.strip() for tag in (tags or []) if tag.strip()))
    image_path = Path(image_path)
    with Image.open(image_path) as image:
        image_format = image.format
        image.verify()
    extension = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "TIFF": ".tif", "BMP": ".bmp"}.get(image_format)
    if extension is None:
        raise ValueError(f"Unsupported raster image format: {image_format}")
    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
    style_id = digest[:16]
    with _connection(root) as connection:
        duplicate = connection.execute("SELECT * FROM styles WHERE sha256 = ?", (digest,)).fetchone()
        if duplicate:
            return _row_dict(duplicate)

    profile = json.loads(Path(profile_path).read_text(encoding="utf-8")) if profile_path else extract_style([image_path])
    _check_profile(profile)
    asset_rel = f"assets/{digest}{extension}"
    profile_rel = f"profiles/{style_id}.json"
    asset_target = _safe_file(root, asset_rel)
    profile_target = _safe_file(root, profile_rel)
    if asset_target.exists() or profile_target.exists():
        raise FileExistsError("Library files already exist for this image; inspect before retrying")
    shutil.copyfile(image_path, asset_target)
    profile_target.write_text(_json(profile), encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connection(root) as connection:
        connection.execute(
            "INSERT INTO styles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (style_id, digest, title, json.dumps(tags, ensure_ascii=False), asset_rel, profile_rel, _search_text(title, tags, profile), now, now),
        )
    _catalog(root)
    return get_record(root, style_id)


def update_record(root, style_id, profile_path, title=None, tags=None):
    profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    _check_profile(profile)
    with _connection(root) as connection:
        current = _row_dict(_get_row(connection, style_id))
        title = title.strip() if title is not None else current["title"]
        if not title:
            raise ValueError("A nonempty title is required")
        tags = list(dict.fromkeys(tag.strip() for tag in tags if tag.strip())) if tags is not None else current["tags"]
        target = _safe_file(root, current["profile"])
        target.write_text(_json(profile), encoding="utf-8")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        connection.execute(
            "UPDATE styles SET title=?, tags_json=?, search_text=?, updated_at=? WHERE id=?",
            (title, json.dumps(tags, ensure_ascii=False), _search_text(title, tags, profile), now, current["id"]),
        )
    _catalog(root)
    return get_record(root, current["id"])


def export_profile(root, style_id, output):
    record = get_record(root, style_id)
    source = _safe_file(root, record["profile"])
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, output)
    return output


def main():
    parser = argparse.ArgumentParser(description="Reference-image style library")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "add", "list", "search", "show", "update", "export"):
        command = commands.add_parser(name)
        command.add_argument("--library", required=True)
        if name == "add":
            command.add_argument("--image", required=True)
            command.add_argument("--title", required=True)
            command.add_argument("--tag", action="append", default=[])
            command.add_argument("--profile")
        elif name == "search":
            command.add_argument("--query", required=True)
        elif name in ("show", "update", "export"):
            command.add_argument("--id", required=True)
            if name == "update":
                command.add_argument("--profile", required=True)
                command.add_argument("--title")
                command.add_argument("--tag", action="append")
            elif name == "export":
                command.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "init":
        result = {"library": str(init_library(args.library).resolve())}
    elif args.command == "add":
        result = add_image(args.library, args.image, args.title, args.tag, args.profile)
    elif args.command == "list":
        result = list_library(args.library)
    elif args.command == "search":
        result = search_library(args.library, args.query)
    elif args.command == "show":
        result = get_record(args.library, args.id, include_profile=True)
    elif args.command == "update":
        result = update_record(args.library, args.id, args.profile, args.title, args.tag)
    else:
        result = {"output": str(export_profile(args.library, args.id, args.output))}
    print(_json(result), end="")


if __name__ == "__main__":
    main()
