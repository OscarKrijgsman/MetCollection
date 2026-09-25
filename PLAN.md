# MetCollection: Plan

PostgreSQL database plus a local web app for browsing the Metallica collection stored in `Metallica_disc.xls`.

Status: all three phases built and verified on 2026-09-25.

---

## 1. Decisions

| Topic | Decision | Source |
|---|---|---|
| Master data | The Excel file stays the master. The database gets refreshed from it with an import script. | Answered |
| Hosting | Runs locally with Docker Compose: PostgreSQL and a Python web app, opened at `http://localhost:8000` | Answered |
| Tabs | CDs, Vinyl, 7Inch and Cassettes are grouped under eras. DVD and boxsets gets its own era. Concerts gets its own page. | Answered |
| "Easily add new" | Adding new rows in Excel and re-importing is the only thing needed. No code changes. | Answered |
| Cassette era | The importer maps the cassette title to an era through the alias file. Anything unmatched goes to "Other". | Assumed, see section 10 |
| Images | Upload them on the item's page. Files go on disk and the database keeps the metadata. The schema and folders are set up in phase 1, and uploading is built in phase 2. | Assumed, see section 10 |
| DVD format | The format (DVD, Blu-ray, Box set, VHS) is read from the description. Anything else is DVD. The rules live in `config/sheets.yaml`. | Assumed, see section 10 |
| Item IDs | Every item row in Excel has a permanent `ID` in column A (`CD-0001`, `LP-0001`, `7IN-0001`, `DVD-0001`, `CAS-0001`). The ID is the key for matching and for images. | Done 2026-09-25, see section 6 |

---

## 2. What the Excel contains (verified)

All item sheets now start with an `ID` column (column A). The columns below come after it.

| Sheet | Items (SUM total) | Columns |
|---|---|---|
| CDs | 681 | SUM, Era, CD (title), Label, year, Country, Barcode, Matrix, Made, description, 1 unnamed note column |
| Vinyl | 314 | SUM, Era, Vinyl (title), Label, year, Country, Barcode, description, 3 unnamed note columns |
| 7Inch | 40 | SUM, Era, Vinyl (title), Label, year, Country, Barcode, description, 1 unnamed note column |
| DVD and boxsets | 49 | SUM, CD (title), Label, year, Country, Barcode, Matrix, description, Additional Info. **No Era column.** Sheet name has a leading space: `' DVD and boxsets'` |
| Cassettes | 16 | SUM, Cassette (title), Label, year, Country, Barcode, Matrix, Made, description. **No Era column.** |
| Concerts | 25 concerts | Day, Month, Year, Place, Venue, Country, Kees (0/1), With whom |

Data issues the importer has to handle:

1. **Era names are inconsistent across sheets.** Some examples: `Kill 'Em All ` (CDs), `Kill em All` (CDs), `Kill em all` (Vinyl). Also `Garage inc` and `Garage Inc.`, `Master of puppets` and `Master of Puppets`, `…And justice for all` and `…and Justice for All`, and trailing spaces on `Ride the lightning `, `72 Seasons `. The fix is a canonical era list plus an alias file (section 5).
2. **The "Barcode" column mostly holds catalog numbers** (`CDMFN 7`, `60766-2`, `BLCKND043-4`). Actual EAN/UPC barcodes sometimes appear in the description instead (`Slim-case, 00602508861512`). The plan is to keep the column as `catalog_no`, pull any 8 to 14 digit number found in any text field into `barcode`, and make search cover both.
3. **Separator rows.** Rows with SUM 0 and no data separate groups. They have no ID and the importer skips them.
4. **Irregular years:** `19??`, `200?`, `1988?`, `2008/2010`, `????`, `?`. Both versions get stored: the raw text (`year_text`) for display, and a parsed integer (`year`) plus an `year_uncertain` flag for filtering and stats.
5. **Duplicates.** Some rows describe two copies ("Twice in collection #02 & #05") but still have SUM 1. SUM becomes `quantity`, and the note is kept as it is.
6. **Vinyl `Various artists` row:** SUM 0 and only a title. Read as a sub-heading, so it has no ID and isn't imported.
7. **Unnamed note columns** in CDs, Vinyl and 7Inch. They're imported as `note_1..note_3`, all shown on the detail page and all searchable.

The importer checks its own count against the SUM total row of each sheet and reports any difference.

---

## 3. Architecture

```
docker compose
├── db    postgres:16        volume: pgdata
└── app   python 3.12
          FastAPI + Jinja2 templates + HTMX (server rendered, no JS build step)
          SQLAlchemy Core + Alembic (schema migrations)
          pandas + xlrd (read .xls)
          volume: ./media  (images)
```

Why this stack:
- There's no Node toolchain on the machine, and none is needed. It's server-rendered HTML, and HTMX handles filtering without full page reloads.
- Postgres takes care of the hard parts: full-text search, trigram matching for partial barcode lookups, and JSONB for anything unexpected.
- Alembic migrations let the schema change later (images, new fields) without rebuilding the database.

---

## 4. Database schema

```sql
era
  id            serial PK
  name          text unique        -- canonical: "Kill 'Em All"
  slug          text unique        -- "kill-em-all"
  sort_order    int                -- chronological release order
  is_special    bool               -- true for "DVD and Boxsets", "Other", "Compilation"

format
  id            serial PK
  code          text unique        -- cd, lp, 7inch, cassette, dvd, bluray, boxset, vhs
  name          text               -- "CD", "Vinyl", "7 Inch", ...

item
  id            text PK            -- Excel ID, e.g. "CD-0001"
  era_id        FK era
  format_id     FK format
  source_sheet  text               -- "CDs", "Vinyl", ...
  source_row    int                -- Excel row number, for traceability
  title         text
  label         text
  year          int null
  year_text     text               -- raw value, e.g. "19??"
  year_uncertain bool
  country       text
  catalog_no    text               -- the Excel "Barcode" column
  catalog_norm  text               -- catalog_no with spaces/dashes/dots stripped, uppercased
  barcode       text null          -- EAN/UPC digits found in any field
  matrix        text
  made_in       text
  description   text
  additional_info text
  notes         text[]             -- unnamed note columns
  quantity      int default 1
  content_hash  text               -- hash of all row values, used to detect changes on re-import
  status        text               -- 'active' | 'missing_from_excel'
  extra         jsonb default '{}' -- any column not mapped above
  search        tsvector generated -- title, label, country, catalog, barcode, matrix, made_in, description, notes
  first_seen_import_id  FK import_run
  last_seen_import_id   FK import_run
  created_at, updated_at

item_image                         -- ready from day one, used in phase 2
  id            serial PK
  item_id       text FK item ON DELETE RESTRICT
  file_path     text               -- relative to ./media, e.g. items/CD-0001/3f9a.jpg
  thumb_path    text
  caption       text               -- "Front", "Back", "Matrix side A", ...
  sort_order    int
  width, height int
  created_at

concert
  id            serial PK
  date          date
  place, venue, country  text
  with_kees     bool
  with_whom     text

import_run
  id, file_name, file_sha256, started_at, finished_at,
  added, updated, unchanged, missing, warnings jsonb
```

Indexes: GIN on `item.search`, GIN trigram (`pg_trgm`) on `catalog_norm`, `barcode`, `matrix` and `title`, and B-tree on `era_id`, `format_id`, `year`, `country` and `label`.

`item_image.item_id` uses `RESTRICT` on purpose. An item that has images can never be removed silently.

---

## 5. Era normalization

`config/eras.yaml` is the single place that controls eras:

```yaml
- name: "Kill 'Em All"
  sort: 1
  aliases: ["Kill 'Em All", "Kill em all", "Kill em All"]
- name: "Ride the Lightning"
  sort: 2
  aliases: ["Ride the lightning"]
...
- name: "DVD and Boxsets"
  sort: 99
  special: true
```

Matching ignores case, surrounding whitespace, and the difference between `…` and `...`. If the importer runs into an era name it doesn't know, it **stops and lists the unknown values**. Nothing gets imported until each value has been added as an alias or as a new era. This keeps typos in Excel from creating ghost eras. An **empty** Era cell is not an error: the item goes to "Other" and the report shows a warning (currently LP-0255, Live at Webster Hall).

Cassettes have no Era column, so their title goes through the same alias lookup (`Load` becomes Load, `…And justice for all` becomes …And Justice for All). Unmatched titles like `MetalliStore` and `No life till leather` go to "Other". `cassette_title_overrides` in the same file can pin a title to an era.

Eras currently in the file: Kill 'Em All, Ride the Lightning, Master of Puppets, Garage Days, …And Justice for All, Metallica, Load, Reload, Garage Inc., S&M, St. Anger, Death Magnetic, Lulu, Beyond Magnetic, Through the Never, Hardwired…to Self-Destruct, S&M2, 72 Seasons, Mission Impossible (OST), Liberte, egalite, fraternite, Metallica!, Compilation, Other, plus DVD and Boxsets.

---

## 6. Import and update workflow

**IDs.** Column A of each item sheet holds a permanent ID. The prefix comes from the sheet and the number runs up per sheet:

| Sheet | Prefix | Range as of 2026-09-25 |
|---|---|---|
| CDs | `CD-` | CD-0001 to CD-0681 |
| Vinyl | `LP-` | LP-0001 to LP-0314 |
| 7Inch | `7IN-` | 7IN-0001 to 7IN-0040 |
| DVD and boxsets | `DVD-` | DVD-0001 to DVD-0049 |
| Cassettes | `CAS-` | CAS-0001 to CAS-0016 |

Rules:
- An ID never changes and never gets reused, even when a row is moved, edited or deleted.
- Sorting or moving rows in Excel is safe, because the ID moves with the row.
- The numbers follow the order the rows were in on 2026-09-25. New rows get the next free number, wherever they sit in the sheet.

**Adding new rows.** Add the rows in Excel without an ID, save, then run on the Mac (Excel does the writing, so formatting and formulas are kept):

```bash
.venv/bin/python scripts/assign_ids.py --dry-run   # show which rows get which ID
.venv/bin/python scripts/assign_ids.py             # write the IDs and save the workbook
```

Only rows that have a title and SUM >= 1 get an ID. Existing IDs are never touched. The script stops on invalid or duplicate IDs. You can also type an ID by hand, as long as it uses the right prefix and a number that isn't taken.

**Importing.**

```bash
docker compose run --rm app import Metallica_disc.xls --dry-run   # show what would change
docker compose run --rm app import Metallica_disc.xls             # apply
```

What happens on each run:

| Case | Action |
|---|---|
| ID exists and the row is unchanged | Only `last_seen_import_id` gets updated |
| ID exists and the row was edited | The fields get updated. The ID and images stay. The report lists the changes. |
| New ID | New item is inserted |
| ID in database but not in the file | Status set to `missing_from_excel`, **never deleted**. Hidden from lists and stats, but shown on the imports page, and it comes back if the row returns. |
| Item row without an ID | Import aborts and says to run `assign_ids.py` first |
| Duplicate or malformed ID | Import aborts and lists the rows |
| Unknown era | Import aborts with a list of the values to add to `eras.yaml` |
| Count differs from SUM row | Warning in the report |

The whole import runs in a single transaction. If it fails, nothing changes.

---

## 7. Web app

All pages are server-rendered. Filters live in the URL query string, so any filtered view can be bookmarked.

**`/` Home: statistics**
- Total items, broken down by format (CD / Vinyl / 7" / Cassette / DVD and Boxsets)
- Items per era (bar chart). Each bar links to that era, so the chart doubles as the era navigation.
- Items per decade of release, and top 10 countries and labels
- Number of items with images, date of the last import
- Eras in chronological order, then Compilation, Other and DVD and Boxsets below a divider. Concerts is a tile and a header link.
- Search bar in the header on every page. Typing an exact ID (`LP-0042`) opens that item.

**`/era/{slug}`: era list**
- A combined table of CDs, Vinyl, 7" and Cassettes (the DVD and Boxsets era shows only its own items)
- Filters: Format (multi-select), Title (dropdown with the titles in this era), Label, Year (from/to), Country, Barcode/catalog (partial match)
- Sortable columns, a result count, and a thumbnail column once images exist
- Filters update through HTMX without reloading the page

**`/item/{id}`: detail** (e.g. `/item/CD-0001`)
- Every field, including matrix, made in, description, notes, `extra`, and the source sheet and row
- Image gallery (phase 3): upload multiple images, add a caption, reorder, delete

**`/search?q=`: global search**
- Searches every text field
- Barcode/catalog matching ignores spaces and dashes, so `8667064` finds `866 706-4`
- Partial matches work through trigram (`BLCKND04` finds all BLCKND04x)
- Results are grouped by era, and each links to the item's detail page

**`/concerts`**
- A table of attended concerts with a count, a "with Kees" count, and concerts per country

**`/imports`**
- Import history, the changes in each import, and items missing from the Excel

---

## 8. Images (built in phase 3)

- Storage: `./media/items/{item_id}/{uuid}.{ext}`, e.g. `./media/items/CD-0001/3f9a.jpg`, with a thumbnail next to each (400px wide, generated with Pillow on upload)
- The database stores only paths and metadata (`item_image`). The binary files stay out of Postgres, which keeps backups and browsing simple.
- `./media` is a Docker volume mounted from the project folder, so the images are plain files you can back up
- Allowed: jpg, png, webp, and HEIC converted to jpg. Max 20 MB per file. Checked by content type and by Pillow decoding it, not only by extension.
- Images are linked to the Excel ID, so they stay attached whatever you change in the row, and even when you sort the sheet
- Deleting an image removes its files; the button asks for confirmation first
- The app has no login, so form posts coming from other websites are refused (checked with the `Origin` and `Sec-Fetch-Site` headers)
- A later bulk import can use the ID in the file name (`CD-0001_front.jpg`)

---

## 9. Project structure

```
MetCollection/
├── Metallica_disc.xls
├── PLAN.md
├── README.md                  # how to run, import, back up
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── pytest.ini
├── config/
│   ├── eras.yaml
│   └── sheets.yaml            # sheet -> column mapping, so a renamed column is a config change
├── app/
│   ├── main.py                # FastAPI app and routes
│   ├── db.py
│   ├── queries.py             # stats, filters, search
│   ├── importer/
│   │   ├── read_excel.py
│   │   ├── normalize.py       # eras, years, barcodes, formats
│   │   └── sync.py            # ID matching, change detection, report
│   ├── templates/
│   └── static/                # css, htmx.min.js
├── scripts/
│   └── assign_ids.py          # host-side: gives new Excel rows an ID (done)
├── migrations/                # Alembic
├── media/                     # images (git-ignored)
└── tests/
    └── test_normalize.py      # era aliases, year parsing, barcode extraction, ID validation
```

Backup: `docker compose exec db pg_dump` to a file, plus copying `./media`. Both steps get documented in the README.

---

## 10. Assumptions still open

These questions weren't answered. The plan uses the defaults below. Say so if any of them is wrong.

1. **Cassette era:** mapped from the title, and unmatched titles go to "Other". The more reliable fix is to add an Era column to the Cassettes tab. The importer will use that column as soon as it exists.
2. **Images:** uploaded through the item page. A bulk folder import can be added later if needed.
3. **DVD format:** read from the description (`Blu-ray`, `VHS`, `box` and so on). Blu-ray first, then box sets (`3 cds`, `2 DVD 2 CD`, `shoebox`, `CD-style box`), then VHS; everything else is DVD. Current result: 31 DVD, 10 Blu-ray, 8 box set.
4. **"Kees" column** in Concerts: read as a yes/no "attended with Kees".
5. **File format:** `.xls` is read as is. If you ever save it as `.xlsx`, the importer handles that too.

---

## 11. Build phases

**Phase 1: database and import** (done)
- Docker Compose, schema and migrations (including `item_image`)
- `eras.yaml`, `sheets.yaml`, the importer with dry-run, ID matching and the report
- Unit tests for normalization
- Check: per-sheet counts match the SUM rows (681 / 314 / 40 / 49 / 16), and no unknown eras

**Phase 2: web app** (done)
- Home stats, era lists with filters, detail page, global search, concerts page, imports page
- Check: spot-check 20 random items against the Excel, and confirm the barcode search examples in section 7 work

**Phase 3: images** (done)
- Upload, thumbnails, gallery, reorder and delete, a thumbnail column in the lists
- Check: upload, edit and sort the Excel, re-import, and confirm the images stay attached
