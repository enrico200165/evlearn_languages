from pathlib import Path

from nlp_deck_manager.readers import iter_text_units_from_path


def test_srt_reader(tmp_path: Path):
    p = tmp_path / "x.srt"
    p.write_text("1\n00:00:01,000 --> 00:00:02,000\nHallo Welt!\n", encoding="utf-8")
    units = list(iter_text_units_from_path(p))
    assert [u.text for u in units] == ["Hallo Welt!"]
