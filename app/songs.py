"""Count how often each song was played across the setlists in config/setlists.json."""
import re
from collections import Counter

# setlist.fm notes ride along as trailing parentheses: "(tour debut)", "(with ... outro)".
# A cover credit and a few real titles end in parentheses too, so those stay.
KEEP_PARENS = {"Sanitarium"}
TRAILING_PARENS = re.compile(r"\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*$")
NOT_SONGS = ("Bass/Guitar Solos", "Kirk and Rob Doodle")


def song_title(name):
    """The song as released, without setlist.fm's performance notes."""
    name = name.strip()
    while m := TRAILING_PARENS.search(name):
        note = m.group(1)
        if note.endswith("cover") or note in KEEP_PARENS:
            break
        name = name[:m.start()].rstrip()
    return name


def song_counts(setlists):
    """Rows of name, n: live performances per song, most played first. Tapes are left out."""
    counts = Counter()
    for setlist in setlists.values():
        for section in setlist["sections"]:
            for song in section["songs"]:
                if song["tape"] or song["name"].startswith(NOT_SONGS):
                    continue
                for part in song["name"].split(" / "):  # a medley counts each song
                    counts[song_title(part)] += 1
    return [{"name": name, "n": n}
            for name, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].casefold()))]
