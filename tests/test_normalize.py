from pathlib import Path

import pytest
import yaml

from app.importer.normalize import (
    Eras,
    catalog_norm,
    clean,
    extract_barcode,
    gtin_valid,
    match_format,
    parse_year,
    slugify,
)
from app.importer.read_excel import column_letter

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def eras():
    return Eras(yaml.safe_load((ROOT / "config/eras.yaml").read_text()))


@pytest.mark.parametrize("raw, expected", [
    (None, None), ("", None), ("   ", None),
    (1983.0, "1983"), (304.706, "304.706"), (7, "7"),
    ("  Kill 'Em All  ", "Kill 'Em All"), ("a   b", "a b"),
])
def test_clean(raw, expected):
    assert clean(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    (1983.0, (1983, "1983", False)),
    ("2008? ", (2008, "2008?", True)),
    ("2008/2010", (2008, "2008/2010", True)),
    ("19??", (None, "19??", True)),
    ("????", (None, "????", True)),
    ("?", (None, "?", True)),
    (None, (None, None, False)),
])
def test_parse_year(raw, expected):
    assert parse_year(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("Kill 'Em All ", "Kill 'Em All"),
    ("Kill em all", "Kill 'Em All"),
    ("Kill em All", "Kill 'Em All"),
    ("Ride the lightning ", "Ride the Lightning"),
    ("Master of puppets", "Master of Puppets"),
    ("…And justice for all", "…And Justice for All"),
    ("...and Justice for All", "…And Justice for All"),
    ("Garage inc", "Garage Inc."),
    ("Garage Inc.", "Garage Inc."),
    ("St.Anger", "St. Anger"),
    ("72 Seasons ", "72 Seasons"),
    ("Hardwired…to self-destruct", "Hardwired…to Self-Destruct"),
])
def test_era_aliases(eras, raw, expected):
    assert eras.resolve(raw) == expected


def test_unknown_era(eras):
    assert eras.resolve("Kill em all 2") is None


@pytest.mark.parametrize("title, expected", [
    ("Load", "Load"),
    ("…And justice for all", "…And Justice for All"),
    ("Nothing else matters", "Metallica"),
    ("MetalliStore", "Other"),
])
def test_era_from_title(eras, title, expected):
    assert eras.from_title(title) == expected


def test_duplicate_alias_rejected():
    config = {"eras": [{"name": "A", "sort": 1, "aliases": ["X"]},
                       {"name": "B", "sort": 2, "aliases": ["x"]}], "fallback": "A"}
    with pytest.raises(ValueError):
        Eras(config)


def test_slugify():
    assert slugify("Kill 'Em All") == "kill-em-all"
    assert slugify("S&M2") == "s-and-m2"
    assert slugify("…And Justice for All") == "and-justice-for-all"


def test_catalog_norm():
    assert catalog_norm("866 706-4") == "8667064"
    assert catalog_norm("BLCKND043-4") == "BLCKND0434"
    assert catalog_norm(None) is None


def test_gtin_valid():
    assert gtin_valid("0602508861512")
    assert not gtin_valid("0602508861513")


@pytest.mark.parametrize("texts, expected", [
    (["Slim-case, 00602508861512"], "0602508861512"),  # GTIN-14 shortened to EAN-13
    (["00602547100573"], "0602547100573"),
    (["762181240025"], "762181240025"),                  # UPC-A
    (["06025274777-8 7"], "0602527477787"),              # spaces and dashes inside
    (["8536-40218-2"], None),                            # 10 digits: catalog number, not a barcode
    (["60766-2", "MANUFACTURED IN U.S.A."], None),
    ([None, "", "BLCKND043-4"], None),
])
def test_extract_barcode(texts, expected):
    assert extract_barcode(*texts) == expected


DVD_SHEET = next(s for s in yaml.safe_load((ROOT / "config/sheets.yaml").read_text())["item_sheets"]
                 if s["prefix"] == "DVD")


@pytest.mark.parametrize("texts, expected", [
    (["Blu-ray", None], "bluray"),
    (["Blu-ray + Blu-ray 3D"], "bluray"),
    (["3 cds, 2 dvd's", "Large box"], "boxset"),
    (["3cds, 3 VHS"], "boxset"),
    (["2 DVD 2 CD"], "boxset"),
    (["Shoebox with DVD + tshirt + rest"], "boxset"),
    (["DVD digi"], "dvd"),
    ([None, None], "dvd"),
])
def test_match_format(texts, expected):
    assert match_format(DVD_SHEET["format_rules"], DVD_SHEET["format"], *texts) == expected


def test_column_letter():
    assert [column_letter(i) for i in (0, 1, 25, 26)] == ["A", "B", "Z", "AA"]
