import hashlib
import json
import re

YEAR_RE = re.compile(r"(19|20)\d\d")
BARCODE_RE = re.compile(r"\d[\d \-]{6,}\d")


def clean(value):
    """Cell value to trimmed text, or None when empty. Numbers lose Excel's '.0'."""
    if value is None:
        return None
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else repr(value)
    if isinstance(value, int):
        return str(value)
    text = " ".join(str(value).split())
    return text or None


def parse_quantity(value):
    text = clean(value)
    return int(text) if text and text.isdigit() else None


def parse_year(value):
    """Returns (year, year_text, uncertain). '2008?' -> (2008, '2008?', True)."""
    text = clean(value)
    if text is None:
        return None, None, False
    match = YEAR_RE.search(text)
    year = int(match.group()) if match else None
    return year, text, year is None or text != match.group()


def era_key(name):
    return " ".join(name.replace("…", "...").lower().split())


def slugify(name):
    name = name.replace("…", " ").replace("&", " and ").lower()
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")


def catalog_norm(catalog_no):
    if not catalog_no:
        return None
    return re.sub(r"[^0-9A-Za-z]", "", catalog_no).upper() or None


def gtin_valid(digits):
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def extract_barcode(*texts):
    """First UPC/EAN (12 or 13 digits, valid check digit) found in the texts.

    Spaces and dashes inside the number are ignored. An 11-digit number is read as
    a UPC-A that lost its leading zero in Excel; a 14-digit GTIN with a leading
    zero is shortened to its EAN-13.
    """
    for text in texts:
        if not text:
            continue
        for match in BARCODE_RE.finditer(text):
            digits = re.sub(r"\D", "", match.group())
            if len(digits) == 11:
                digits = "0" + digits
            if len(digits) == 14 and digits.startswith("0"):
                digits = digits[1:]
            if len(digits) in (12, 13) and gtin_valid(digits):
                return digits
    return None


def match_format(rules, default, *texts):
    haystack = " ".join(t for t in texts if t)
    for code, pattern in rules:
        if re.search(pattern, haystack, re.IGNORECASE):
            return code
    return default


def content_hash(item):
    return hashlib.sha256(json.dumps(item, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class Eras:
    def __init__(self, config):
        self.config = config
        self.by_key = {}
        for era in config["eras"]:
            for spelling in [era["name"], *era.get("aliases", [])]:
                key = era_key(spelling)
                if self.by_key.get(key, era["name"]) != era["name"]:
                    raise ValueError(f"eras.yaml: {spelling!r} is listed under two eras")
                self.by_key[key] = era["name"]
        overrides = config.get("title_overrides") or {}
        for name in [config["fallback"], *overrides.values()]:
            if era_key(name) not in self.by_key:
                raise ValueError(f"eras.yaml: {name!r} is not a defined era")
        self.fallback = self.by_key[era_key(config["fallback"])]
        self.title_overrides = {era_key(k): self.by_key[era_key(v)] for k, v in overrides.items()}

    def resolve(self, name):
        return self.by_key.get(era_key(name))

    def from_title(self, title):
        key = era_key(title)
        return self.title_overrides.get(key) or self.by_key.get(key) or self.fallback
