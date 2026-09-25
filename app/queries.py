import re

from sqlalchemy import text

from app.importer.normalize import catalog_norm

ID_RE = re.compile(r"^\s*([A-Za-z0-9]+-\d{4,})\s*$")

ITEM_SELECT = """
    SELECT i.*, e.name AS era, e.slug AS era_slug, f.code AS format_code, f.name AS format,
        (SELECT thumb_path FROM item_image im WHERE im.item_id = i.id ORDER BY sort_order, id LIMIT 1) AS thumb
    FROM item i JOIN era e ON e.id = i.era_id JOIN format f ON f.id = i.format_id
"""

SORTS = {
    "id": "i.id",
    "title": "lower(i.title)",
    "format": "f.name",
    "label": "lower(i.label)",
    "year": "i.year",
    "country": "lower(i.country)",
    "catalog": "i.catalog_norm",
}


def home_stats(conn):
    stats = {}
    stats["total"] = conn.execute(text("SELECT count(*) FROM item WHERE status = 'active'")).scalar_one()
    stats["by_sheet"] = conn.execute(text("""
        SELECT source_sheet AS name, count(*) AS n FROM item WHERE status = 'active'
        GROUP BY source_sheet ORDER BY n DESC
    """)).mappings().all()
    stats["eras"] = conn.execute(text("""
        SELECT e.name, e.slug, e.is_special, count(i.id) AS n
        FROM era e LEFT JOIN item i ON i.era_id = e.id AND i.status = 'active'
        GROUP BY e.id HAVING count(i.id) > 0 ORDER BY e.sort_order
    """)).mappings().all()
    stats["decades"] = [
        {"name": f"{decade}s" if decade else "Unknown", "n": n}
        for decade, n in conn.execute(text("""
            SELECT year / 10 * 10 AS decade, count(*) FROM item WHERE status = 'active'
            GROUP BY decade ORDER BY decade NULLS LAST
        """)).all()
    ]
    for field in ("country", "label"):
        stats[field] = conn.execute(text(f"""
            SELECT mode() WITHIN GROUP (ORDER BY {field}) AS name, count(*) AS n
            FROM item WHERE status = 'active' AND {field} IS NOT NULL
            GROUP BY lower({field}) ORDER BY n DESC, name LIMIT 10
        """)).mappings().all()
    stats["with_images"] = conn.execute(text("""
        SELECT count(DISTINCT im.item_id) FROM item_image im JOIN item i ON i.id = im.item_id
        WHERE i.status = 'active'
    """)).scalar_one()
    stats["concerts"] = conn.execute(text("SELECT count(*) FROM concert")).scalar_one()
    stats["last_import"] = conn.execute(text("""
        SELECT finished_at FROM import_run WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1
    """)).scalar()
    return stats


def get_era(conn, slug):
    return conn.execute(text("SELECT * FROM era WHERE slug = :slug"), {"slug": slug}).mappings().first()


def era_facets(conn, era_id):
    """Filter options, taken from the whole era so they don't shrink while filtering."""
    def distinct(field):
        return conn.execute(text(f"""
            SELECT mode() WITHIN GROUP (ORDER BY {field}) FROM item
            WHERE era_id = :era AND status = 'active' AND {field} IS NOT NULL
            GROUP BY lower({field}) ORDER BY lower({field})
        """), {"era": era_id}).scalars().all()

    return {
        "formats": conn.execute(text("""
            SELECT f.code, f.name, count(*) AS n FROM item i JOIN format f ON f.id = i.format_id
            WHERE i.era_id = :era AND i.status = 'active' GROUP BY f.id ORDER BY n DESC
        """), {"era": era_id}).mappings().all(),
        "titles": distinct("title"),
        "labels": distinct("label"),
        "countries": distinct("country"),
        "years": conn.execute(text("""
            SELECT min(year), max(year) FROM item WHERE era_id = :era AND status = 'active'
        """), {"era": era_id}).one(),
    }


def code_conditions(code, params):
    """Partial match on catalog number, barcode or matrix, ignoring spaces and dashes."""
    conditions = ["i.matrix ILIKE :code_raw"]
    params["code_raw"] = f"%{code}%"
    norm = catalog_norm(code)
    if norm:
        conditions.append("i.catalog_norm LIKE :code_norm")
        params["code_norm"] = f"%{norm}%"
        digits = re.sub(r"\D", "", code)
        if len(digits) >= 3:
            conditions.append("i.barcode LIKE :code_digits")
            params["code_digits"] = f"%{digits}%"
    return "(" + " OR ".join(conditions) + ")"


def era_items(conn, era_id, f):
    where = ["i.era_id = :era", "i.status = 'active'"]
    params = {"era": era_id}
    if f["format"]:
        where.append("f.code = ANY(:formats)")
        params["formats"] = f["format"]
    for field in ("title", "label", "country"):
        if f[field]:
            where.append(f"lower(i.{field}) = lower(:{field})")
            params[field] = f[field]
    if f["year_from"] is not None:
        where.append("i.year >= :year_from")
        params["year_from"] = f["year_from"]
    if f["year_to"] is not None:
        where.append("i.year <= :year_to")
        params["year_to"] = f["year_to"]
    if f["code"]:
        where.append(code_conditions(f["code"], params))

    direction = "DESC" if f["dir"] == "desc" else "ASC"
    order = f"{SORTS[f['sort']]} {direction} NULLS LAST, lower(i.title), i.year, i.id"
    return conn.execute(text(f"{ITEM_SELECT} WHERE {' AND '.join(where)} ORDER BY {order}"), params).mappings().all()


def get_item(conn, item_id):
    return conn.execute(text(f"{ITEM_SELECT} WHERE i.id = :id"), {"id": item_id}).mappings().first()


def find_id(conn, q):
    match = ID_RE.match(q)
    if not match:
        return None
    return conn.execute(text("SELECT id FROM item WHERE upper(id) = upper(:id)"),
                        {"id": match.group(1)}).scalar()


def search(conn, q, limit=500):
    params = {"limit": limit}
    conditions = []
    words = re.findall(r"\w+", q)
    if words:
        conditions.append("i.search @@ to_tsquery('simple', :tsq)")
        params["tsq"] = " & ".join(f"{w}:*" for w in words)
    if len(q.strip()) >= 3:
        conditions.append(code_conditions(q.strip(), params))
    if not conditions:
        return []
    rank = "ts_rank(i.search, to_tsquery('simple', :tsq))" if words else "0"
    return conn.execute(text(f"""
        {ITEM_SELECT}
        WHERE i.status = 'active' AND ({' OR '.join(conditions)})
        ORDER BY e.sort_order, {rank} DESC, lower(i.title), i.year, i.id
        LIMIT :limit
    """), params).mappings().all()


def concerts(conn):
    rows = conn.execute(text("SELECT * FROM concert ORDER BY date")).mappings().all()
    by_country = conn.execute(text("""
        SELECT country AS name, count(*) AS n FROM concert GROUP BY country ORDER BY n DESC, country
    """)).mappings().all()
    return rows, by_country


def imports(conn):
    runs = conn.execute(text("SELECT * FROM import_run ORDER BY id DESC")).mappings().all()
    missing = conn.execute(text(f"""
        {ITEM_SELECT} WHERE i.status = 'missing_from_excel' ORDER BY i.id
    """)).mappings().all()
    return runs, missing


def item_images(conn, item_id):
    return conn.execute(text("""
        SELECT * FROM item_image WHERE item_id = :id ORDER BY sort_order, id
    """), {"id": item_id}).mappings().all()


def add_image(conn, item_id, stored):
    conn.execute(text("""
        INSERT INTO item_image (item_id, file_path, thumb_path, width, height, sort_order)
        VALUES (:item_id, :file_path, :thumb_path, :width, :height,
                (SELECT coalesce(max(sort_order) + 1, 0) FROM item_image WHERE item_id = :item_id))
    """), {"item_id": item_id, **stored})


def set_caption(conn, item_id, image_id, caption):
    return conn.execute(text("""
        UPDATE item_image SET caption = :caption WHERE id = :image_id AND item_id = :item_id
    """), {"caption": caption, "image_id": image_id, "item_id": item_id}).rowcount


def move_image(conn, item_id, image_id, step):
    ids = [row["id"] for row in item_images(conn, item_id)]
    if image_id not in ids:
        return False
    pos = ids.index(image_id)
    new_pos = max(0, min(len(ids) - 1, pos + step))
    ids.insert(new_pos, ids.pop(pos))
    for order, iid in enumerate(ids):
        conn.execute(text("UPDATE item_image SET sort_order = :o WHERE id = :id"), {"o": order, "id": iid})
    return True


def delete_image(conn, item_id, image_id):
    return conn.execute(text("""
        DELETE FROM item_image WHERE id = :image_id AND item_id = :item_id RETURNING file_path, thumb_path
    """), {"image_id": image_id, "item_id": item_id}).first()
