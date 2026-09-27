import hashlib
import json
from pathlib import Path

from sqlalchemy import text

from .normalize import slugify

ITEM_COLUMNS = [
    "id", "source_sheet", "source_row", "title", "label", "year", "year_text", "year_uncertain",
    "country", "catalog_no", "catalog_norm", "barcode", "matrix", "made_in", "description",
    "quantity", "content_hash",
]
# Fields compared when reporting what changed in an edited row.
DIFF_FIELDS = [c for c in ITEM_COLUMNS if c not in ("id", "source_row", "content_hash")] + ["era", "format", "extra"]


def upsert_lookups(conn, eras_config, formats):
    for era in eras_config["eras"]:
        conn.execute(text("""
            INSERT INTO era (name, slug, sort_order, is_special)
            VALUES (:name, :slug, :sort, :special)
            ON CONFLICT (name) DO UPDATE
            SET slug = EXCLUDED.slug, sort_order = EXCLUDED.sort_order, is_special = EXCLUDED.is_special
        """), {"name": era["name"], "slug": slugify(era["name"]), "sort": era["sort"],
               "special": bool(era.get("special"))})
    for code, name in formats.items():
        conn.execute(text("""
            INSERT INTO format (code, name) VALUES (:code, :name)
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
        """), {"code": code, "name": name})
    era_ids = dict(conn.execute(text("SELECT name, id FROM era")).all())
    format_ids = dict(conn.execute(text("SELECT code, id FROM format")).all())
    return era_ids, format_ids


def item_params(item, era_ids, format_ids, run_id):
    params = {c: item[c] for c in ITEM_COLUMNS}
    params.update(era_id=era_ids[item["era"]], format_id=format_ids[item["format"]],
                  extra=json.dumps(item["extra"], ensure_ascii=False), run_id=run_id)
    return params


def apply(conn, path, result, eras_config, sheets_config):
    era_ids, format_ids = upsert_lookups(conn, eras_config, sheets_config["formats"])
    run_id = conn.execute(text("""
        INSERT INTO import_run (file_name, file_sha256) VALUES (:name, :sha) RETURNING id
    """), {"name": Path(path).name, "sha": hashlib.sha256(Path(path).read_bytes()).hexdigest()}).scalar_one()

    existing = {row["id"]: row for row in conn.execute(text("""
        SELECT i.*, e.name AS era, f.code AS format
        FROM item i JOIN era e ON e.id = i.era_id JOIN format f ON f.id = i.format_id
    """)).mappings()}

    added, updated, restored, unchanged = [], {}, [], 0
    columns = ", ".join(ITEM_COLUMNS)
    values = ", ".join(f":{c}" for c in ITEM_COLUMNS)
    assignments = ", ".join(f"{c} = :{c}" for c in ITEM_COLUMNS if c != "id")

    for item in result.items:
        params = item_params(item, era_ids, format_ids, run_id)
        old = existing.get(item["id"])
        if old is None:
            conn.execute(text(f"""
                INSERT INTO item ({columns}, era_id, format_id, extra, first_seen_import_id, last_seen_import_id)
                VALUES ({values}, :era_id, :format_id, CAST(:extra AS jsonb), :run_id, :run_id)
            """), params)
            added.append(item["id"])
            continue
        if old["status"] != "active":
            restored.append(item["id"])
        if old["content_hash"] != item["content_hash"] or old["status"] != "active":
            diff = {f: [old[f], item[f]] for f in DIFF_FIELDS if old[f] != item[f]}
            if diff:
                updated[item["id"]] = diff
            conn.execute(text(f"""
                UPDATE item SET {assignments}, era_id = :era_id, format_id = :format_id,
                    extra = CAST(:extra AS jsonb), status = 'active',
                    last_seen_import_id = :run_id, updated_at = now()
                WHERE id = :id
            """), params)
        else:
            unchanged += 1
            conn.execute(text("""
                UPDATE item SET source_row = :source_row, last_seen_import_id = :run_id WHERE id = :id
            """), params)

    file_ids = {item["id"] for item in result.items}
    missing = sorted(i for i, row in existing.items() if i not in file_ids and row["status"] == "active")
    if missing:
        conn.execute(text("""
            UPDATE item SET status = 'missing_from_excel', updated_at = now() WHERE id = ANY(:ids)
        """), {"ids": missing})

    # Concerts have no IDs and nothing links to them, so they are replaced as a whole.
    conn.execute(text("DELETE FROM concert"))
    for concert in result.concerts:
        conn.execute(text("""
            INSERT INTO concert (date, place, venue, country, with_kees, with_whom)
            VALUES (:date, :place, :venue, :country, :with_kees, :with_whom)
        """), concert)

    changes = {"added": added, "updated": updated, "missing": missing, "restored": restored}
    conn.execute(text("""
        UPDATE import_run SET finished_at = now(), added = :added, updated = :updated,
            unchanged = :unchanged, missing = :missing, restored = :restored,
            warnings = CAST(:warnings AS jsonb), changes = CAST(:changes AS jsonb)
        WHERE id = :id
    """), {"id": run_id, "added": len(added), "updated": len(updated), "unchanged": unchanged,
           "missing": len(missing), "restored": len(restored),
           "warnings": json.dumps(result.warnings, ensure_ascii=False),
           "changes": json.dumps(changes, ensure_ascii=False, default=str)})
    return changes, unchanged
