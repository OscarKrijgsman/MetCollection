"""Add or complete the ID column in Metallica_disc.xls.

Runs on the Mac host (drives Microsoft Excel via AppleScript so formatting,
formulas and the .xls format are preserved). Safe to re-run: existing IDs are
never changed, only rows without an ID get the next free number.

Usage: python scripts/assign_ids.py [path/to/Metallica_disc.xls] [--dry-run]
"""

import re
import subprocess
import sys
from pathlib import Path

import xlrd

# sheet name -> (ID prefix, title column index before the ID column exists)
SHEETS = {
    "CDs": ("CD", 2),
    "Vinyl": ("LP", 2),
    "7Inch": ("7IN", 2),
    " DVD and boxsets": ("DVD", 1),
    "Cassettes": ("CAS", 1),
}
ID_HEADER = "ID"
ID_RE = re.compile(r"^([A-Z0-9]+)-(\d{4})$")


def plan_sheet(sheet, prefix, title_col):
    has_id = str(sheet.cell_value(0, 0)).strip() == ID_HEADER
    offset = 1 if has_id else 0
    title_col += offset
    sum_col = offset

    existing = {}
    for r in range(1, sheet.nrows):
        v = str(sheet.cell_value(r, 0)).strip() if has_id else ""
        if v:
            m = ID_RE.match(v)
            if not m or m.group(1) != prefix:
                sys.exit(f"{sheet.name!r} row {r + 1}: invalid ID {v!r}")
            if v in existing.values():
                sys.exit(f"{sheet.name!r} row {r + 1}: duplicate ID {v!r}")
            existing[r] = v

    next_n = max((int(ID_RE.match(v).group(2)) for v in existing.values()), default=0) + 1
    column = [ID_HEADER]
    added = []
    for r in range(1, sheet.nrows):
        title = str(sheet.cell_value(r, title_col)).strip()
        qty = sheet.cell_value(r, sum_col)
        is_item = bool(title) and isinstance(qty, float) and qty >= 1
        if r in existing:
            column.append(existing[r])
        elif is_item:
            new_id = f"{prefix}-{next_n:04d}"
            next_n += 1
            column.append(new_id)
            added.append((r + 1, new_id, title))
        else:
            column.append("")
    return has_id, column, added


def applescript_list(values):
    esc = [v.replace("\\", "\\\\").replace('"', '\\"') for v in values]
    return "{" + ", ".join('{"%s"}' % v for v in esc) + "}"


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv
    path = Path(args[0] if args else "Metallica_disc.xls").resolve()

    book = xlrd.open_workbook(str(path))
    steps = []
    for name, (prefix, title_col) in SHEETS.items():
        has_id, column, added = plan_sheet(book.sheet_by_name(name), prefix, title_col)
        print(f"{name.strip()}: {len(added)} new IDs" + ("" if has_id else " (adding ID column)"))
        for row, new_id, title in added[:3]:
            print(f"  row {row}: {new_id}  {title}")
        if len(added) > 3:
            print(f"  ... up to {added[-1][1]}")
        if not added and has_id:
            continue
        sheet_ref = f'worksheet "{name}" of wb'
        if not has_id:
            steps.append(f'insert into range (range "A:A" of {sheet_ref}) shift shift to right')
        steps.append(
            f'set value of range "A1:A{len(column)}" of {sheet_ref} to {applescript_list(column)}'
        )

    if dry_run or not steps:
        print("Nothing written." if not steps else "Dry run, nothing written.")
        return

    body = "\n    ".join(steps)
    script = f'''
tell application "Microsoft Excel"
    set wasOpen to (name of every workbook) contains "{path.name}"
    if wasOpen then
        set wb to workbook "{path.name}"
        if not (saved of wb) then error "Workbook has unsaved changes, save it first."
    else
        open POSIX file "{path}"
        set wb to workbook "{path.name}"
    end if
    {body}
    save wb
    if not wasOpen then close wb saving no
end tell
'''
    subprocess.run(["osascript", "-"], input=script, text=True, check=True)
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
