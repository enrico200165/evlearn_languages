from nlp_deck_manager.core import build_ranked_rows
from nlp_deck_manager.models import LemmaOccurrence


def test_core_bands_do_not_overlap():
    occ = {
        f"w{i}": LemmaOccurrence(f"w{i}", f"w{i}", 1000 - i, "de")
        for i in range(1, 2501)
    }
    rows = build_ranked_rows(occ, language="de", max_rank=2500, band_size=1000)
    assert len(rows) == 2500
    assert rows[0].core_band == "Core-1000"
    assert rows[1000].core_band == "Core-2000"
    assert len({r.normalized_lemma for r in rows}) == 2500
