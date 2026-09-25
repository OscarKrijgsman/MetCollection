# MetCollection

PostgreSQL database of the Metallica collection in `Metallica_disc.xls`. The Excel file is the master; the database is refreshed from it. See `PLAN.md` for the design.

Requires Docker Desktop.

## First run

```bash
docker compose build
docker compose run --rm app import Metallica_disc.xls
```

This starts PostgreSQL, creates the schema and imports everything.

## Browsing

```bash
docker compose up -d
```

Open http://localhost:8000. Stop with `docker compose down` (the data stays).

From a phone or tablet on the same wifi: `http://<mac-name>.local:8000` (the Mac's name is shown by `scutil --get LocalHostName`). Anyone on the network can open it, including uploading and deleting images; change `"8000:8000"` back to `"127.0.0.1:8000:8000"` in `docker-compose.yml` to limit it to this Mac.

## Images

Open an item (click its ID or title) and use **Upload** at the bottom. Select several files at once; JPEG, PNG, WebP and HEIC (iPhone photos, converted to JPEG) up to 20 MB each. Add a caption, reorder with the arrows, or delete.

Files are stored in `media/items/<ID>/`, with a thumbnail next to each. They are linked to the Excel ID, so editing, moving or sorting rows in Excel never detaches them.

## Updating the collection

1. Edit `Metallica_disc.xls` in Excel. New rows go in without an ID.
2. Give new rows an ID (runs on the Mac and uses Excel, so formatting is kept):
   ```bash
   .venv/bin/python scripts/assign_ids.py --dry-run
   .venv/bin/python scripts/assign_ids.py
   ```
3. Preview, then import:
   ```bash
   docker compose run --rm app import Metallica_disc.xls --dry-run
   docker compose run --rm app import Metallica_disc.xls
   ```

The import stops without changing anything when a row has no ID, an ID is duplicated, an era is unknown, or a column header moved. The message says what to fix.

- **Unknown era:** add the spelling as an alias (or a new era) in `config/eras.yaml`.
- **New or moved column:** update `config/sheets.yaml`. Extra columns at the end of a sheet are picked up automatically (blank header: note, named header: extra field).
- **Row removed from Excel:** the item stays in the database, marked `missing_from_excel`. It comes back if the ID returns.

## IDs

| Sheet | Prefix |
|---|---|
| CDs | `CD-` |
| Vinyl | `LP-` |
| 7Inch | `7IN-` |
| DVD and boxsets | `DVD-` |
| Cassettes | `CAS-` |

IDs never change and are never reused. Sorting or moving rows is safe.

## Tests

```bash
docker compose run --rm --entrypoint pytest app
```

## Database access

PostgreSQL listens on `localhost:5433` (database, user and password: `metcollection`), for tools like TablePlus or DBeaver.

## Backup

```bash
docker compose exec -T db pg_dump -U metcollection metcollection > backup-$(date +%F).sql
```

Also copy the `media/` folder: the database stores only the paths, the image files live there.

## Mac-side Python environment

`scripts/assign_ids.py` runs on the Mac (not in Docker) because it drives Excel. Its one dependency, `xlrd`, lives in `.venv` in this folder. To recreate it:

```bash
python3 -m venv .venv && .venv/bin/pip install xlrd==2.0.2
```
