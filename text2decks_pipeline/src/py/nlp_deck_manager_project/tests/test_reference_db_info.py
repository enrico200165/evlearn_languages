from nlp_deck_manager.models import LemmaOccurrence
from nlp_deck_manager.reference_db import ReferenceDb


def test_info_lemma_cache_roundtrip(tmp_path):
    db_path = tmp_path / "vocab_reference_de.sqlite"
    with ReferenceDb(db_path) as db:
        result = db.upsert_lemma(
            LemmaOccurrence(
                lemma="arbeiten",
                normalized_lemma="arbeiten",
                frequency=3,
                language="de",
                part_of_speech="VERB",
            )
        )
        saved = db.upsert_lemma_info(
            vocab_id=result.vocab_id,
            nome_informazione="coniugazione",
            informazione="{\"praesens\": {\"ich\": \"arbeite\"}}",
            origine="test_api",
        )
        loaded = db.get_lemma_info(
            vocab_id=result.vocab_id,
            nome_informazione="coniugazione",
            origine="test_api",
        )
        assert loaded is not None
        assert loaded.informazione == saved.informazione
        assert loaded.origine == "test_api"


def test_info_lemma_can_create_manual_lemma(tmp_path):
    db_path = tmp_path / "vocab_reference_de.sqlite"
    with ReferenceDb(db_path) as db:
        info = db.upsert_lemma_info_by_lemma(
            language="de",
            lemma="Haus",
            normalized_lemma="haus",
            nome_informazione="flessione",
            informazione="test",
            origine="manuale",
        )
        assert info.nome_informazione == "flessione"
        row = db.get_vocab_row(language="de", normalized_lemma="haus")
        assert row is not None
        assert row["origin_type"] == "manual"
