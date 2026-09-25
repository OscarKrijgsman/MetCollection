import mimetypes
import os
from pathlib import Path
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import images, queries
from app.db import engine

HERE = Path(__file__).resolve().parent

app = FastAPI(title="MetCollection", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
mimetypes.add_type("image/webp", ".webp")
images.MEDIA_ROOT.mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=images.MEDIA_ROOT), name="media")
templates = Jinja2Templates(directory=HERE / "templates")


def bar_scale(rows):
    return max((r["n"] for r in rows), default=0) or 1


def local_time(value):
    return value.astimezone(LOCAL_TZ).strftime("%-d %b %Y %H:%M") if value else ""


LOCAL_TZ = ZoneInfo(os.environ.get("TZ", "UTC"))
templates.env.globals["bar_scale"] = bar_scale
templates.env.filters["local_time"] = local_time


def int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def read_filters(request):
    q = request.query_params
    sort = q.get("sort", "title")
    return {
        "format": [v for v in q.getlist("format") if v],
        "title": q.get("title") or None,
        "label": q.get("label") or None,
        "country": q.get("country") or None,
        "year_from": int_or_none(q.get("year_from")),
        "year_to": int_or_none(q.get("year_to")),
        "code": (q.get("code") or "").strip() or None,
        "sort": sort if sort in queries.SORTS else "title",
        "dir": "desc" if q.get("dir") == "desc" else "asc",
    }


def query_string(filters, **changes):
    merged = {**filters, **changes}
    pairs = [("format", v) for v in merged["format"]]
    pairs += [(k, v) for k, v in merged.items() if k != "format" and v is not None]
    return urlencode(pairs)


@app.middleware("http")
async def same_origin_posts(request: Request, call_next):
    """Block form posts from other websites (the app has no login)."""
    if request.method == "POST":
        origin = request.headers.get("origin")
        if request.headers.get("sec-fetch-site") == "cross-site" or (
                origin and urlparse(origin).netloc != request.headers.get("host")):
            return PlainTextResponse("Cross-site request blocked", status_code=403)
    return await call_next(request)


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse(request, "404.html", {"detail": getattr(exc, "detail", None)},
                                      status_code=404)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with engine.connect() as conn:
        stats = queries.home_stats(conn)
    return templates.TemplateResponse(request, "home.html", {"s": stats})


@app.get("/era/{slug}", response_class=HTMLResponse)
def era(request: Request, slug: str):
    filters = read_filters(request)
    with engine.connect() as conn:
        era_row = queries.get_era(conn, slug)
        if era_row is None:
            raise HTTPException(404, f"No era called {slug!r}")
        items = queries.era_items(conn, era_row["id"], filters)
        facets = None if request.headers.get("HX-Request") else queries.era_facets(conn, era_row["id"])
    context = {
        "era": era_row, "items": items, "facets": facets, "f": filters,
        "active": any(filters[k] for k in ("format", "title", "label", "country", "code"))
                  or filters["year_from"] is not None or filters["year_to"] is not None,
        "sort_url": lambda col: "?" + query_string(
            filters, sort=col, dir="desc" if filters["sort"] == col and filters["dir"] == "asc" else "asc"),
    }
    template = "_items.html" if request.headers.get("HX-Request") else "era.html"
    return templates.TemplateResponse(request, template, context)


@app.get("/item/{item_id}", response_class=HTMLResponse)
def item(request: Request, item_id: str):
    with engine.connect() as conn:
        row = queries.get_item(conn, item_id)
        if row is None:
            raise HTTPException(404, f"No item with ID {item_id}")
        gallery = queries.item_images(conn, item_id)
    return templates.TemplateResponse(request, "item.html", {
        "item": row, "images": gallery, "messages": request.query_params.getlist("msg")})


def back_to_item(item_id, messages=()):
    query = urlencode([("msg", m) for m in messages])
    return RedirectResponse(f"/item/{item_id}{'?' + query if query else ''}#images", status_code=303)


def require_item(conn, item_id):
    if queries.get_item(conn, item_id) is None:
        raise HTTPException(404, f"No item with ID {item_id}")


@app.post("/item/{item_id}/images")
async def upload_images(item_id: str, files: list[UploadFile] = File(...)):
    messages = []
    with engine.begin() as conn:
        require_item(conn, item_id)
        for upload in files:
            if not upload.filename:
                continue
            data = await upload.read(images.MAX_BYTES + 1)
            try:
                stored = images.save(item_id, upload.filename, data)
            except images.ImageError as err:
                messages.append(str(err))
                continue
            queries.add_image(conn, item_id, stored)
    return back_to_item(item_id, messages)


@app.post("/item/{item_id}/images/{image_id}/caption")
def caption_image(item_id: str, image_id: int, caption: str = Form("")):
    with engine.begin() as conn:
        if not queries.set_caption(conn, item_id, image_id, caption.strip() or None):
            raise HTTPException(404, "No such image")
    return back_to_item(item_id)


@app.post("/item/{item_id}/images/{image_id}/move")
def move_image(item_id: str, image_id: int, step: int = Form(...)):
    with engine.begin() as conn:
        if not queries.move_image(conn, item_id, image_id, 1 if step > 0 else -1):
            raise HTTPException(404, "No such image")
    return back_to_item(item_id)


@app.post("/item/{item_id}/images/{image_id}/delete")
def delete_image(item_id: str, image_id: int):
    with engine.begin() as conn:
        paths = queries.delete_image(conn, item_id, image_id)
        if paths is None:
            raise HTTPException(404, "No such image")
    images.delete_files(*paths)
    return back_to_item(item_id)


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = ""):
    q = q.strip()
    with engine.connect() as conn:
        exact = queries.find_id(conn, q) if q else None
        if exact:
            return RedirectResponse(f"/item/{exact}", status_code=303)
        results = queries.search(conn, q) if q else []
    groups = {}
    for row in results:
        groups.setdefault((row["era"], row["era_slug"]), []).append(row)
    return templates.TemplateResponse(request, "search.html", {"q": q, "results": results, "groups": groups})


@app.get("/concerts", response_class=HTMLResponse)
def concerts(request: Request):
    with engine.connect() as conn:
        rows, by_country = queries.concerts(conn)
    return templates.TemplateResponse(request, "concerts.html", {
        "rows": rows, "by_country": by_country, "with_kees": sum(r["with_kees"] for r in rows)})


@app.get("/imports", response_class=HTMLResponse)
def imports(request: Request):
    with engine.connect() as conn:
        runs, missing = queries.imports(conn)
    return templates.TemplateResponse(request, "imports.html", {"runs": runs, "missing": missing})
