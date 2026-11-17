from app.songs import song_counts, song_title


def test_song_title_drops_performance_notes():
    assert song_title("Battery (tour debut)") == "Battery"
    assert song_title('Seek & Destroy (with "Wasting My Hate" outro)') == "Seek & Destroy"
    assert song_title("Am I Evil? (Diamond Head cover) (Half, no intro)") == "Am I Evil? (Diamond Head cover)"
    assert song_title("Whiskey in the Jar ([traditional] cover) (fan introduction)") == "Whiskey in the Jar ([traditional] cover)"
    assert song_title("Welcome Home (Sanitarium)") == "Welcome Home (Sanitarium)"


def test_song_counts_skips_tapes_and_solos_and_splits_medleys():
    songs = [{"name": n, "tape": t} for n, t in [
        ("The Ecstasy of Gold (Ennio Morricone song)", True),
        ("Battery", False),
        ("Bass/Guitar Solos", False),
        ("Kirk and Rob Doodle (\"Orca Attack\")", False),
        ("Hit the Lights / Battery (with outro)", False),
    ]]
    setlists = {"2000-01-01": {"sections": [{"title": None, "songs": songs}]}}
    assert song_counts(setlists) == [{"name": "Battery", "n": 2}, {"name": "Hit the Lights", "n": 1}]
