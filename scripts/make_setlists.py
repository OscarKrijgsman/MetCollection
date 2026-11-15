"""Write the concert setlists to config/setlists.json (read by the web app) and setlists/*.md.

The setlists are transcribed by hand from setlist.fm into the list C below; setlist.fm
blocks scripted downloads and its API needs a key. To add a concert, append an entry and
run the script. The date must match the date in the Concerts tab of the Excel sheet,
because the Concerts page links by that date.

Usage: python scripts/make_setlists.py [markdown_dir] [json_file]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "setlists"
JSON_OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "config" / "setlists.json"
BASE = "https://www.setlist.fm/setlist/metallica/"
T = "[tape] "  # song played from tape
E = "--Encore"
E2 = "--Encore 2"
E3 = "--Encore 3"

C = [
 ("1996-11-12", "Utrecht", "Prins van Oranjehal", "Netherlands", "Poor Touring Me",
  "1996/prins-van-oranjehal-utrecht-netherlands-13d6e1b1.html", None, [
  "So What (Anti-Nowhere League cover)", "Creeping Death", "Sad but True", "Ain't My Bitch", "Whiplash",
  "King Nothing", "One", "Wasting My Hate", "Bass/Guitar Solos", "Nothing Else Matters", "Until It Sleeps",
  "For Whom the Bell Tolls", "Wherever I May Roam", "Fade to Black",
  "Ride the Lightning / No Remorse / Hit the Lights / The Four Horsemen / Seek & Destroy / Fight Fire With Fire",
  E, "Last Caress (Misfits cover)", "Master of Puppets (Short Version)", 'Enter Sandman (With stage "accident")',
  E2, "Am I Evil? (Diamond Head cover) (Half, no intro)", "Motorbreath"]),
 ("1997-08-22", "Hasselt", "Domein Kiewit (Pukkelpop 1997)", "Belgium", "Blitzkrieg 97",
  "1997/domein-kiewit-hasselt-belgium-73d6daf9.html", None, [
  "So What (Anti-Nowhere League cover)", "Master of Puppets (Short Version)", "King Nothing", "Sad but True",
  "Fuel", "Hero of the Day", "Ain't My Bitch", "One", "Until It Sleeps", "For Whom the Bell Tolls",
  "Wherever I May Roam", "Nothing Else Matters", "Enter Sandman",
  E, "Stone Cold Crazy (Queen cover)", "Creeping Death", "Battery"]),
 ("1999-05-23", "Nuenen", "Landgoed Gulbergen, Main Stage (Dynamo Open Air 1999)", "Netherlands", "Garage Remains the Same",
  "1999/landgoed-gulbergen-main-stage-nuenen-netherlands-73d6e241.html",
  None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Breadfan (Budgie cover)", "Master of Puppets",
  "Of Wolf and Man", "The Thing That Should Not Be", "Fuel", "The Memory Remains", "Bleeding Me",
  'Bass/Guitar Solos (including "My Friend of Misery" and "Welcome Home (Sanitarium)")', "The Four Horsemen",
  "For Whom the Bell Tolls", 'King Nothing (including "The Outlaw Torn")', "Wherever I May Roam", "One",
  "Fight Fire With Fire",
  E, "Nothing Else Matters", "Sad but True", "Creeping Death (w/ members of Anthrax, Biohazard & Merauder)",
  E2, 'Die, Die My Darling (Misfits cover) (preceded by "Fixxxer" jam)', "Enter Sandman",
  E3, 'Battery (with "Damage, Inc." outro)']),
 ("2003-06-15", "Nijmegen", "Goffertpark (Fields of Rock 2003)", "Netherlands", "European Festivals 2003",
  "2003/goffertpark-nijmegen-netherlands-bd6dd16.html",
  'setlist.fm note: "Harvester of Sorrow" was recorded and included on the Dutch edition of the "Frantic" CD single.', [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Blackened", "No Remorse", "Harvester of Sorrow",
  "Welcome Home (Sanitarium)", "For Whom the Bell Tolls", "Frantic", "Sad but True", "St. Anger",
  "Seek & Destroy", "Master of Puppets", "Damage, Inc.",
  E, "Ride the Lightning", "Nothing Else Matters", "Creeping Death",
  E2, "Hit the Lights", "Enter Sandman"]),
 ("2003-12-06", "Arnhem", "Gelredome", "Netherlands", "Madly in Anger with the World",
  "2003/gelredome-arnhem-netherlands-1bd6e1b0.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Battery", "Fuel", "Seek & Destroy", "Fade to Black",
  "The Thing That Should Not Be", "Frantic", "Creeping Death", "The Unnamed Feeling", "Sad but True", "One",
  "Blackened",
  E, "Harvester of Sorrow", "Nothing Else Matters", "Master of Puppets",
  E2, "St. Anger", "Enter Sandman",
  E3, "So What (Anti-Nowhere League cover)", "Whiplash"]),
 ("2004-06-10", "Gelsenkirchen", "Arena AufSchalke", "Germany", "Madly in Anger with the World",
  "2004/arena-aufschalke-gelsenkirchen-germany-3bd6dc50.html",
  None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Blackened", "Fuel", "The Four Horsemen", "Fade to Black",
  "Frantic", "Holier Than Thou", "I Disappear", "St. Anger", "Sad but True", "Creeping Death", "Battery",
  E, "Wherever I May Roam", "Nothing Else Matters", "Master of Puppets", T + "'Full Metal Jacket' Clip", "One",
  "Enter Sandman",
  E2, "Metal Militia", "Seek & Destroy (w/ Let There Be Rock outro)"]),
 ("2004-06-21", "Amsterdam", "ArenA", "Netherlands", "Madly in Anger with the World",
  "2004/arena-amsterdam-netherlands-bd6e18e.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Blackened", "Fuel", "Leper Messiah",
  "Welcome Home (Sanitarium)", "Frantic", "Holier Than Thou", "Wherever I May Roam", "St. Anger",
  "Sad but True", "Creeping Death", "Battery",
  E, "No Leaf Clover", "Nothing Else Matters", "Master of Puppets", T + "'Full Metal Jacket' Clip", "One",
  "Enter Sandman",
  E2, "Dyers Eve (preceded by The Frayed Ends of Sanity/Am I Evil?/...And Justice For All/Eye of the Beholder jam)",
  "Seek & Destroy (with AC/DC's \"Let There Be Rock\" outro)"]),
 ("2006-06-08", "Arnhem", "Gelredome", "Netherlands", "Escape From the Studio 2006",
  "2006/gelredome-arnhem-netherlands-1bd6e1b4.html",
  'Songs 7 to 14 are the Master of Puppets album in full; setlist.fm prints "Master of Puppets" as an extra line before them with no song link, so it is shown here as a heading.', [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Motorbreath", "Fuel", "Wherever I May Roam",
  "The New Song (includes excerpts of The End of the Line & All Nightmare Long)",
  'The Unforgiven (preceded by extended intro featuring "...and Justice For All" snippet)',
  "--Master of Puppets (album)", "Battery", "Master of Puppets", "The Thing That Should Not Be",
  "Welcome Home (Sanitarium)", "Disposable Heroes", "Leper Messiah", "Orion", "Damage, Inc.",
  E, "Sad but True", "Nothing Else Matters", "One", "Enter Sandman",
  E2, "Die, Die My Darling (Misfits cover) (with Avenged Sevenfold & Trivium; tour debut)", "Seek & Destroy"]),
 ("2007-07-08", "London", "Wembley Stadium", "England", "Sick of the Studio '07",
  "2007/wembley-stadium-london-england-53d6e771.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Creeping Death", "For Whom the Bell Tolls", "Sad but True",
  "Disposable Heroes", "The Unforgiven", "...And Justice for All", "The Memory Remains", "The Four Horsemen",
  "Orion", "Fade to Black", "Master of Puppets", "Battery",
  E, "No Leaf Clover (Tour debut)", "Nothing Else Matters", "One", "Enter Sandman",
  E2, "Whiplash", "Seek & Destroy"]),
 ("2008-05-30", "Landgraaf", "Megaland (Pinkpop 2008)", "Netherlands", "European Summer Vacation",
  "2008/megaland-landgraaf-netherlands-4bd6a7d6.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Creeping Death", "For Whom the Bell Tolls",
  "Ride the Lightning", "The Four Horsemen", "Bleeding Me (First time live since Nov 20, 2004)",
  "...And Justice for All", "Devil's Dance", "The Memory Remains", "Fade to Black", "Master of Puppets",
  "Whiplash", "Nothing Else Matters", "Sad but True", "One", "Enter Sandman",
  E, "Last Caress (Misfits cover) (preceded by Invaders jam)", "So What (Anti-Nowhere League cover)",
  "Seek & Destroy (with AC/DC's \"Let There Be Rock\" outro)"]),
 ("2009-03-30", "Rotterdam", "Ahoy", "Netherlands", "World Magnetic",
  "2009/ahoy-rotterdam-netherlands-3bd63c8c.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "That Was Just Your Life", "The End of the Line",
  "No Remorse", "The Thing That Should Not Be", "One", "Broken, Beat & Scarred", "My Apocalypse",
  "Sad but True", "Turn the Page (Bob Seger cover)", "All Nightmare Long", "The Day That Never Comes",
  "Master of Puppets", "Fight Fire With Fire", "Nothing Else Matters", "Enter Sandman",
  E, 'Of Wolf and Man (preceded by "Suicide & Redemption" jam)', "Trapped Under Ice",
  'Seek & Destroy (with "Wasting My Hate" outro)']),
 ("2009-05-16", "Oberhausen", "König-Pilsener-Arena", "Germany", "World Magnetic",
  "2009/konig-pilsener-arena-oberhausen-germany-13df4521.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "That Was Just Your Life", "The End of the Line",
  "For Whom the Bell Tolls", "Disposable Heroes", "One", "Broken, Beat & Scarred", "Cyanide", "Sad but True",
  "Bleeding Me", "All Nightmare Long", "The Day That Never Comes", "Master of Puppets", "Damage, Inc.",
  "Nothing Else Matters", "Enter Sandman",
  E, "Am I Evil? (Diamond Head cover) (Preceded by Black Magic/Raining Blood jam)", "Hit the Lights",
  'Seek & Destroy (with "Wasting My Hate" outro)']),
 ("2009-06-20", "Nijmegen", "Goffertpark (Sonisphere Netherlands 2009)", "Netherlands", "World Magnetic",
  "2009/goffertpark-nijmegen-netherlands-23d67c6b.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", T + "Blackened Intro", "Blackened", "Creeping Death",
  "Holier Than Thou", "Harvester of Sorrow", "One", "Broken, Beat & Scarred", "Cyanide", "Sad but True",
  "Welcome Home (Sanitarium)", "The Judas Kiss", "The Day That Never Comes", "Master of Puppets", "Dyers Eve",
  "Nothing Else Matters", "Enter Sandman",
  E, 'Stone Cold Crazy (Queen cover) (preceded by "Metal Militia" jam)', "Phantom Lord",
  'Seek & Destroy (with "Wasting My Hate" outro)']),
 ("2011-07-02", "Gelsenkirchen", "Veltins-Arena", "Germany", "2011 Vacation Tour",
  "2011/veltins-arena-gelsenkirchen-germany-23d36c57.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Hit the Lights", "Master of Puppets", "The Shortest Straw",
  "Seek & Destroy", "Welcome Home (Sanitarium)", "The Memory Remains", "All Nightmare Long", "Sad but True",
  "Wherever I May Roam", "The Call of Ktulu", "One", "For Whom the Bell Tolls", "Blackened", "Fade to Black",
  "Enter Sandman",
  E, "Helpless (Diamond Head cover) (with Megadeth and Anthrax)", "Battery", "Creeping Death"]),
 ("2012-05-28", "Werchter", "Festivalpark (Werchter Boutique 2012)", "Belgium", "2012 European Black Album Tour",
  "2012/festivalpark-werchter-belgium-53dff391.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Hit the Lights", "Master of Puppets",
  "Ride the Lightning (tour debut)", "For Whom the Bell Tolls", "Hell and Back",
  "--The Black Album (in reverse order)", "The Struggle Within", "My Friend of Misery", "The God That Failed",
  "Of Wolf and Man", "Nothing Else Matters (Original Version)", "Through the Never", "Don't Tread on Me",
  "Wherever I May Roam", "The Unforgiven", "Holier Than Thou", "Sad but True", "Enter Sandman (Extended Bridge)",
  E, "Battery", "One", "Seek & Destroy"]),
 ("2014-06-09", "Landgraaf", "Megaland, Main Stage (Pinkpop 2014)", "Netherlands", "Metallica by Request",
  "2014/megaland-main-stage-landgraaf-netherlands-13c015f9.html",
  'setlist.fm note: the Vote of the Day choices were "Blackened", "Fuel" and "The Day That Never Comes". The show was delayed almost an hour and a half by a thunderstorm.', [
  T + "Intro By Request", T + "The Ecstasy of Gold (Ennio Morricone song)", "Battery (without taped intro)",
  "Master of Puppets", "Welcome Home (Sanitarium)", "Ride the Lightning (Followed by a guitar solo by Kirk)",
  "The Unforgiven", "Lords of Summer", "Wherever I May Roam",
  "Sad but True (fan introduction - Closed with a bass solo by Robert)", "Fade to Black",
  "...And Justice for All", "One", "For Whom the Bell Tolls",
  "Whiskey in the Jar ([traditional] cover) (fan introduction)",
  "Nothing Else Matters (Preceded by Kirk's clean guitar solo)", "Enter Sandman",
  E, "Fuel (Vote of the Day)", "Creeping Death", "Seek & Destroy (w/ The Frayed Ends of Sanity outro)"]),
 ("2017-09-04", "Amsterdam", "Ziggo Dome", "Netherlands", "Worldwired",
  "2017/ziggo-dome-amsterdam-netherlands-3e2edc7.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", T + "Hardwired Intro", "Hardwired", "Atlas, Rise!",
  "Seek & Destroy", "Through the Never", "The Day That Never Comes",
  "Now That We're Dead (with extended middle drum solo with all members of the band, James fell into a hole in the stage)",
  "Dream No More", "For Whom the Bell Tolls", "Halo on Fire",
  'Kirk and Rob Doodle (Chic\'s "Le Freak", "I Disappear" and "(Anesthesia) Pulling Teeth")',
  "Am I Evil? (Diamond Head cover) (half; tour debut)", "The Memory Remains", "Moth Into Flame",
  "Sad but True", "One", "Master of Puppets",
  E, "Blackened", "Nothing Else Matters", 'Enter Sandman (with "The Frayed Ends of Sanity" outro)']),
 ("2017-09-06", "Amsterdam", "Ziggo Dome", "Netherlands", "Worldwired",
  "2017/ziggo-dome-amsterdam-netherlands-33e2e021.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", T + "Hardwired Intro", "Hardwired", "Atlas, Rise!",
  "Seek & Destroy", "Leper Messiah (tour debut)", "Fade to Black (with new intro tape)",
  "Now That We're Dead (with extended middle drum solo with all members of the band)", "Confusion",
  "For Whom the Bell Tolls", "Halo on Fire",
  'Kirk and Rob Doodle (Golden Earring\'s "Radar Love", "Eye of the Beholder" and "(Anesthesia) Pulling Teeth")',
  "Blitzkrieg (Blitzkrieg cover) (tour debut; first live performance since August 6, 2012)", "Fuel",
  "Moth Into Flame", "Sad but True", "One", "Master of Puppets",
  E, "Damage, Inc. (tour debut)", "Nothing Else Matters", 'Enter Sandman (with "The Frayed Ends of Sanity" outro)']),
 ("2019-06-11", "Amsterdam", "Johan Cruijff ArenA", "Netherlands", "Worldwired",
  "2019/johan-cruijff-arena-amsterdam-netherlands-7391fe4d.html", None, [
  T + "The Ecstasy of Gold (Ennio Morricone song)", T + "Hardwired Intro", "Hardwired",
  "The Memory Remains (with extended outro)", "Ride the Lightning", "The God That Failed", "The Unforgiven",
  "Here Comes Revenge", "Moth Into Flame", "Sad but True", "No Leaf Clover",
  'Kirk and Rob Doodle (André Hazes\' "Bloed, zweet en tranen", "ManUNkind" and "Orion")', "St. Anger", "One",
  "Master of Puppets", "For Whom the Bell Tolls", "Creeping Death", "Seek & Destroy",
  E, "Spit Out the Bone", "Nothing Else Matters", 'Enter Sandman (with "The Frayed Ends of Sanity" outro)']),
 ("2022-06-17", "Landgraaf", "Megaland (Pinkpop 2022)", "Netherlands", "European Tour 2022",
  "2022/megaland-landgraaf-netherlands-6bb46e8a.html", None, [
  T + "It's a Long Way to the Top (If You Wanna Rock 'n' Roll) (AC/DC song)",
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Whiplash", "Creeping Death", "Enter Sandman",
  "Harvester of Sorrow", "Trapped Under Ice", "Bleeding Me", "Sad but True", "Dirty Window",
  "Wherever I May Roam (Tour debut)", "For Whom the Bell Tolls", "Moth Into Flame", "Welcome Home (Sanitarium)",
  "Seek & Destroy",
  E, "Metal Militia (Tour debut, First time since December 15, 2016)", "One", "Master of Puppets"]),
 ("2023-04-27", "Amsterdam", "Johan Cruijff ArenA", "Netherlands", "M72 World Tour",
  "2023/johan-cruijff-arena-amsterdam-netherlands-13b819c1.html", "First show of the M72 World Tour.", [
  T + "It's a Long Way to the Top (If You Wanna Rock 'n' Roll) (AC/DC song)",
  T + "The Ecstasy of Gold (Ennio Morricone song)", T + "Orion Intro",
  "Orion (First time as an opener since December 10, 2011)", "For Whom the Bell Tolls", "Holier Than Thou",
  "King Nothing", "Lux Æterna (First performance with tape)", "Screaming Suicide (Live debut)", "Fade to Black",
  "Sleepwalk My Life Away (Live debut)", "Nothing Else Matters", "Sad but True", "The Day That Never Comes",
  "Ride the Lightning",
  "Battery (First full performance in front of a live audience since December 7, 2011)", "Fuel",
  "Seek & Destroy", "Master of Puppets", T + "The Ecstasy of Gold (Ennio Morricone song) (Metallica version)"]),
 ("2023-04-29", "Amsterdam", "Johan Cruijff ArenA", "Netherlands", "M72 World Tour",
  "2023/johan-cruijff-arena-amsterdam-netherlands-23b87c3f.html", None, [
  T + "It's a Long Way to the Top (If You Wanna Rock 'n' Roll) (AC/DC song)",
  T + "The Ecstasy of Gold (Ennio Morricone song)", T + "The Call of Ktulu Intro", "The Call of Ktulu",
  "Creeping Death", "Leper Messiah", "Until It Sleeps (First performance since November 3, 2008)",
  "72 Seasons (First time in front of a live audience)", "If Darkness Had a Son (First performance of the full version)",
  "Welcome Home (Sanitarium)", "You Must Burn! (Live debut)", "The Unforgiven", "Wherever I May Roam",
  "Harvester of Sorrow", "Moth Into Flame", "Fight Fire With Fire",
  'Whiskey in the Jar ([traditional] cover) (preceded by "The Outlaw Torn" jam)', "One", "Enter Sandman"]),
 ("2024-08-30", "Seattle", "Lumen Field", "USA", "M72 World Tour",
  "2024/lumen-field-seattle-wa-23abacb7.html", None, [
  T + "It's a Long Way to the Top (If You Wanna Rock 'n' Roll) (AC/DC song)",
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Creeping Death", "Harvester of Sorrow", "Leper Messiah",
  "King Nothing", "72 Seasons", "If Darkness Had a Son (Dedicated to Megan, from Make-a-Wish)",
  'Kirk and Rob Doodle ("Orca Attack")', "The Day That Never Comes", "Shadows Follow",
  "Orion (Dedicated to Cliff Burton)", "Nothing Else Matters (KH Doodle intro)",
  "Sad but True (Extended James Outro)", "Blackened", "Fuel", "Seek & Destroy", "Master of Puppets"]),
 ("2024-09-01", "Seattle", "Lumen Field", "USA", "M72 World Tour",
  "2024/lumen-field-seattle-wa-2babacaa.html", None, [
  T + "It's a Long Way to the Top (If You Wanna Rock 'n' Roll) (AC/DC song)",
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Whiplash", "For Whom the Bell Tolls (Extended Kirk outro)",
  "Ride the Lightning", "The Memory Remains (With extended band outro)", "Lux Æterna", "Screaming Suicide",
  'Kirk and Rob Doodle (The Sonics\' "The Witch" and Mudhoney\'s "Touch Me I\'m Sick", tribute to Seattle bands)',
  "Welcome Home (Sanitarium)", "Wherever I May Roam", "The Call of Ktulu (Dedicated to Cliff Burton)",
  "The Unforgiven", "Inamorata", "Fight Fire With Fire", "Moth Into Flame", "One",
  "Enter Sandman (Dedicated to Sam, from Make-A-Wish)"]),
 ("2026-05-30", "Berlin", "Olympiastadion", "Germany", "M72 World Tour",
  "2026/olympiastadion-berlin-germany-7347364d.html",
  "setlist.fm note: the biggest stadium concert in Germany to date, with about 94,000 attendees.", [
  T + "It's a Long Way to the Top (If You Wanna Rock 'n' Roll) (AC/DC song)",
  T + "The Ecstasy of Gold (Ennio Morricone song)", "Creeping Death", "For Whom the Bell Tolls",
  "Of Wolf and Man", "The Memory Remains", "72 Seasons", "The Unforgiven", "Fuel",
  'Kirk and Rob Doodle (covering "Sonne" by Rammstein)', "The Day That Never Comes", "Wherever I May Roam",
  "Nothing Else Matters", "Sad but True", "One", "Seek & Destroy", "Master of Puppets", "Enter Sandman"]),
]

OUT.mkdir(parents=True, exist_ok=True)
# The folder is generated, so stale files (a concert whose date changed) are removed.
for old in OUT.glob("*.md"):
    old.unlink()
data = {}
index = ["# Metallica setlists, concerts attended", "",
         "Transcribed from setlist.fm on 2026-11-15. Songs played from tape are marked *(tape)*.", "",
         "| Date | Place | Venue | Songs | File |", "|---|---|---|---|---|"]
for date, place, venue, country, tour, path, note, items in C:
    slug = f"{date}-{place.lower().replace(' ', '-')}"
    lines = [f"# Metallica, {venue}, {place}, {country}", "",
             f"- Date: {date}", f"- Tour: {tour}", f"- Source: {BASE}{path}", ""]
    if note:
        lines += [f"> {note}", ""]
    sections = [{"title": None, "songs": []}]
    for it in items:
        if it.startswith("--"):
            sections.append({"title": it[2:], "songs": []})
        else:
            tape = it.startswith(T)
            sections[-1]["songs"].append({"name": it[len(T):] if tape else it, "tape": tape})
    data[date] = {
        "date": date, "place": place, "venue": venue, "country": country, "tour": tour,
        "url": BASE + path, "note": note, "sections": [x for x in sections if x["songs"]]}
    n = songs = 0
    for it in items:
        if it.startswith("--"):
            lines += ["", f"**{it[2:]}**", ""]
            continue
        n += 1
        if it.startswith(T):
            lines.append(f"{n}. {it[len(T):]} *(tape)*")
        else:
            songs += 1
            lines.append(f"{n}. {it}")
    (OUT / f"{slug}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    index.append(f"| {date} | {place} | {venue} | {songs} | [{slug}.md]({slug}.md) |")
(OUT / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"wrote {len(C)} setlists to {OUT}")
