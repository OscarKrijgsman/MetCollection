import argparse
import sys
from pathlib import Path

import yaml
from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parent.parent
LIST_LIMIT = 25


def migrate():
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")


def show(label, values):
    print(f"{label} ({len(values)}):")
    for value in values[:LIST_LIMIT]:
        print(f"  {value}")
    if len(values) > LIST_LIMIT:
        print(f"  ... and {len(values) - LIST_LIMIT} more")


def run_import(path, dry_run):
    from app.db import engine
    from app.importer import read_excel, sync
    from app.importer.normalize import Eras

    eras_config = yaml.safe_load((ROOT / "config/eras.yaml").read_text())
    sheets_config = yaml.safe_load((ROOT / "config/sheets.yaml").read_text())
    result = read_excel.read(path, sheets_config, Eras(eras_config))

    print(f"Read {Path(path).name}")
    for sheet, (count, total) in result.sheet_counts.items():
        check = "" if total is None else ("  ok" if count == total else f"  total row says {total}")
        print(f"  {sheet:<18}{count:>5}{check}")
    if result.warnings:
        show("Warnings", result.warnings)
    if result.errors:
        show("Errors, nothing imported", result.errors)
        return 1

    migrate()
    with engine.connect() as conn:
        with conn.begin() as transaction:
            changes, unchanged = sync.apply(conn, path, result, eras_config, sheets_config)
            if dry_run:
                transaction.rollback()

    print(f"Items: {len(changes['added'])} added, {len(changes['updated'])} updated, {unchanged} unchanged, "
          f"{len(changes['missing'])} missing from Excel, {len(changes['restored'])} restored")
    print(f"Concerts: {len(result.concerts)}")
    if 0 < len(changes["added"]) <= LIST_LIMIT:
        show("Added", changes["added"])
    if changes["updated"]:
        show("Updated", [f"{item_id}: " + "; ".join(f"{f} {old!r} -> {new!r}" for f, (old, new) in diff.items())
                         for item_id, diff in changes["updated"].items()])
    if changes["missing"]:
        show("Missing from Excel (kept in database, hidden)", changes["missing"])
    if changes["restored"]:
        show("Back in Excel", changes["restored"])
    print("Dry run, nothing saved." if dry_run else "Saved.")
    return 0


def main():
    parser = argparse.ArgumentParser(prog="metcollection")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate", help="create or upgrade the database schema")
    sub.add_parser("serve", help="run the web app on port 8000")
    imp = sub.add_parser("import", help="import the collection Excel file")
    imp.add_argument("file")
    imp.add_argument("--dry-run", action="store_true", help="show changes without saving")
    args = parser.parse_args()

    if args.cmd == "migrate":
        migrate()
        print("Database schema is up to date.")
        return 0
    if args.cmd == "serve":
        import uvicorn

        migrate()
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=[str(ROOT / "app")])
        return 0
    return run_import(args.file, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
