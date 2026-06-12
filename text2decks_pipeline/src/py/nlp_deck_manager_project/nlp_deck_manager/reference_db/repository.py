from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from nlp_deck_manager.models import LemmaInfo, LemmaOccurrence, Note
from nlp_deck_manager.reference_db.schema import SCHEMA_SQL


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class LemmaImportResult:
    lemma: str
    normalized_lemma: str
    language: str
    frequency: int
    action: str
    vocab_id: int


class ReferenceDb:
    """Repository SQLite del Language Reference DB.

    Il DB è uno strumento di supporto alla qualità dei deck. Non viene aggiornato
    automaticamente quando un lemma viene rimosso da un deck.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "ReferenceDb":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.close()

    def upsert_lemma(self, occurrence: LemmaOccurrence, *, origin_type: str = "observed") -> LemmaImportResult:
        now = utc_now()
        row = self.conn.execute(
            "SELECT id FROM vocab_items WHERE language = ? AND normalized_lemma = ?",
            (occurrence.language, occurrence.normalized_lemma),
        ).fetchone()
        if row is None:
            cur = self.conn.execute(
                """
                INSERT INTO vocab_items (
                    language, lemma, normalized_lemma, part_of_speech,
                    observed_count, first_observed_at, last_observed_at,
                    origin_type, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    occurrence.language,
                    occurrence.lemma,
                    occurrence.normalized_lemma,
                    occurrence.part_of_speech,
                    int(occurrence.frequency),
                    now if occurrence.frequency > 0 else None,
                    now if occurrence.frequency > 0 else None,
                    origin_type,
                    now,
                    now,
                ),
            )
            action = "NEW"
            vocab_id = int(cur.lastrowid)
        else:
            vocab_id = int(row["id"])
            self.conn.execute(
                """
                UPDATE vocab_items
                SET lemma = COALESCE(NULLIF(?, ''), lemma),
                    part_of_speech = COALESCE(?, part_of_speech),
                    observed_count = observed_count + ?,
                    last_observed_at = CASE WHEN ? > 0 THEN ? ELSE last_observed_at END,
                    first_observed_at = CASE
                        WHEN ? > 0 AND first_observed_at IS NULL THEN ?
                        ELSE first_observed_at
                    END,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    occurrence.lemma,
                    occurrence.part_of_speech,
                    int(occurrence.frequency),
                    int(occurrence.frequency),
                    now,
                    int(occurrence.frequency),
                    now,
                    now,
                    vocab_id,
                ),
            )
            action = "UPDATED"
        return LemmaImportResult(
            lemma=occurrence.lemma,
            normalized_lemma=occurrence.normalized_lemma,
            language=occurrence.language,
            frequency=int(occurrence.frequency),
            action=action,
            vocab_id=vocab_id,
        )

    def import_lemma_occurrences(self, occurrences: dict[str, LemmaOccurrence]) -> list[LemmaImportResult]:
        results = [self.upsert_lemma(occ) for occ in occurrences.values()]
        self.conn.commit()
        return results

    def get_vocab_id(self, *, language: str, normalized_lemma: str) -> int | None:
        row = self.conn.execute(
            "SELECT id FROM vocab_items WHERE language = ? AND normalized_lemma = ?",
            (language, normalized_lemma),
        ).fetchone()
        return int(row["id"]) if row else None

    def get_vocab_row(self, *, language: str, normalized_lemma: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM vocab_items WHERE language = ? AND normalized_lemma = ?",
            (language, normalized_lemma),
        ).fetchone()

    def add_lemma_tag(self, *, vocab_id: int, tag: str) -> None:
        tag = tag.strip()
        if not tag:
            return
        self.conn.execute(
            "INSERT OR IGNORE INTO lemma_tags (vocab_id, tag, created_at) VALUES (?, ?, ?)",
            (vocab_id, tag, utc_now()),
        )

    def upsert_deck(
        self,
        *,
        language: str,
        deck_name: str,
        description: str | None = None,
        deck_kind: str | None = None,
    ) -> int:
        now = utc_now()
        row = self.conn.execute(
            "SELECT id FROM decks WHERE language = ? AND deck_name = ?",
            (language, deck_name),
        ).fetchone()
        if row:
            deck_id = int(row["id"])
            self.conn.execute(
                """
                UPDATE decks
                SET description = COALESCE(?, description),
                    deck_kind = COALESCE(?, deck_kind),
                    updated_at = ?
                WHERE id = ?
                """,
                (description, deck_kind, now, deck_id),
            )
            return deck_id
        cur = self.conn.execute(
            """
            INSERT INTO decks (language, deck_name, description, deck_kind, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (language, deck_name, description, deck_kind, now, now),
        )
        return int(cur.lastrowid)

    def get_deck_id(self, *, language: str, deck_name: str) -> int | None:
        row = self.conn.execute(
            "SELECT id FROM decks WHERE language = ? AND deck_name = ?",
            (language, deck_name),
        ).fetchone()
        return int(row["id"]) if row else None

    def link_lemma_to_deck(self, *, vocab_id: int, deck_id: int, deck_description: str | None = None) -> None:
        if deck_description is not None and len(deck_description) > 255:
            raise ValueError("deck_description deve avere massimo 255 caratteri")
        now = utc_now()
        self.conn.execute(
            """
            INSERT INTO lemma_deck_relations (vocab_id, deck_id, deck_description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(vocab_id, deck_id) DO UPDATE SET
                deck_description = excluded.deck_description,
                updated_at = excluded.updated_at
            """,
            (vocab_id, deck_id, deck_description, now, now),
        )

    def find_decks_for_lemma(self, *, language: str, normalized_lemma: str) -> list[sqlite3.Row]:
        return list(
            self.conn.execute(
                """
                SELECT d.id AS deck_id, d.deck_name, d.deck_kind, r.deck_description
                FROM vocab_items v
                JOIN lemma_deck_relations r ON r.vocab_id = v.id
                JOIN decks d ON d.id = r.deck_id
                WHERE v.language = ? AND v.normalized_lemma = ?
                ORDER BY d.deck_name
                """,
                (language, normalized_lemma),
            )
        )

    def lemma_is_in_core_deck(self, *, language: str, normalized_lemma: str) -> bool:
        rows = self.find_decks_for_lemma(language=language, normalized_lemma=normalized_lemma)
        return any((row["deck_kind"] or "").lower() == "core" for row in rows)

    def register_source(self, *, language: str, source_name: str, source_type: str, source_path: str | None) -> int:
        now = utc_now()
        row = self.conn.execute(
            """
            SELECT id FROM input_sources
            WHERE language = ? AND source_name = ? AND source_type = ? AND source_path IS ?
            """,
            (language, source_name, source_type, source_path),
        ).fetchone()
        if row:
            return int(row["id"])
        cur = self.conn.execute(
            """
            INSERT INTO input_sources (language, source_name, source_type, source_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (language, source_name, source_type, source_path, now),
        )
        return int(cur.lastrowid)

    def save_note(self, note: Note) -> int:
        now = utc_now()
        if note.deck_id is None:
            note.deck_id = self.upsert_deck(language=note.language, deck_name=note.deck_name)
        if note.vocab_id is None:
            note.vocab_id = self.get_vocab_id(language=note.language, normalized_lemma=note.normalized_lemma)
        fields_json = json.dumps(note.fields, ensure_ascii=False, sort_keys=True)
        tags_json = json.dumps(note.tags, ensure_ascii=False)
        row = self.conn.execute(
            "SELECT id FROM notes WHERE deck_id = ? AND vocab_id IS ? AND note_type = ?",
            (note.deck_id, note.vocab_id, note.note_type),
        ).fetchone()
        if row:
            note_id = int(row["id"])
            self.conn.execute(
                """
                UPDATE notes
                SET fields_json = ?, tags_json = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (fields_json, tags_json, note.status, now, note_id),
            )
            return note_id
        cur = self.conn.execute(
            """
            INSERT INTO notes (language, deck_id, vocab_id, note_type, status, fields_json, tags_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (note.language, note.deck_id, note.vocab_id, note.note_type, note.status, fields_json, tags_json, now, now),
        )
        return int(cur.lastrowid)

    def load_notes_for_deck(self, *, language: str, deck_name: str) -> list[Note]:
        rows = self.conn.execute(
            """
            SELECT n.*, d.deck_name, v.lemma, v.normalized_lemma
            FROM notes n
            JOIN decks d ON d.id = n.deck_id
            LEFT JOIN vocab_items v ON v.id = n.vocab_id
            WHERE n.language = ? AND d.deck_name = ?
            ORDER BY n.id
            """,
            (language, deck_name),
        ).fetchall()
        notes: list[Note] = []
        for row in rows:
            notes.append(
                Note(
                    language=row["language"],
                    deck_name=row["deck_name"],
                    lemma=row["lemma"] or "",
                    normalized_lemma=row["normalized_lemma"] or "",
                    note_type=row["note_type"],
                    fields=json.loads(row["fields_json"]),
                    tags=json.loads(row["tags_json"]),
                    status=row["status"],
                    vocab_id=row["vocab_id"],
                    deck_id=row["deck_id"],
                    note_id=row["id"],
                )
            )
        return notes

    def record_processing_result(self, *, note_id: int, processor_name: str, result) -> None:
        self.conn.execute(
            """
            INSERT INTO note_processing_runs (
                note_id, processor_name, changed, warnings_json, errors_json, updated_fields_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                note_id,
                processor_name,
                1 if result.changed else 0,
                json.dumps(result.warnings, ensure_ascii=False),
                json.dumps(result.errors, ensure_ascii=False),
                json.dumps(result.updated_fields, ensure_ascii=False, sort_keys=True),
                utc_now(),
            ),
        )


    def upsert_manual_lemma(
        self,
        *,
        language: str,
        lemma: str,
        normalized_lemma: str | None = None,
        part_of_speech: str | None = None,
        origin_type: str = "manual",
    ) -> int:
        """Inserire o aggiornare un lemma non necessariamente osservato in un corpus.

        Serve per import manuali o per memorizzare informazioni cache relative a
        lemmi non ancora prodotti dalla pipeline NLP.
        """

        clean_lemma = lemma.strip()
        clean_normalized = (normalized_lemma or lemma).strip().lower()
        if not clean_lemma:
            raise ValueError("lemma non può essere vuoto")
        occurrence = LemmaOccurrence(
            lemma=clean_lemma,
            normalized_lemma=clean_normalized,
            frequency=0,
            language=language.strip().lower(),
            part_of_speech=part_of_speech,
        )
        return self.upsert_lemma(occurrence, origin_type=origin_type).vocab_id

    def upsert_lemma_info(
        self,
        *,
        vocab_id: int,
        nome_informazione: str,
        informazione: str,
        origine: str,
    ) -> LemmaInfo:
        """Creare o aggiornare una informazione cache associata a un lemma.

        La coppia logica è:
            lemma + nome_informazione + origine

        Se la riga esiste già viene aggiornata, così una chiamata API più recente
        può sostituire una risposta precedente senza duplicare record.
        """

        name = nome_informazione.strip()
        source = origine.strip() or "unspecified"
        if not name:
            raise ValueError("nome_informazione non può essere vuoto")
        now = utc_now()
        self.conn.execute(
            """
            INSERT INTO info_lemma (vocab_id, nome_informazione, informazione, origine, tstamp)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(vocab_id, nome_informazione, origine) DO UPDATE SET
                informazione = excluded.informazione,
                tstamp = excluded.tstamp
            """,
            (int(vocab_id), name, informazione, source, now),
        )
        return LemmaInfo(
            vocab_id=int(vocab_id),
            nome_informazione=name,
            informazione=informazione,
            origine=source,
            tstamp=now,
        )

    def upsert_lemma_info_by_lemma(
        self,
        *,
        language: str,
        lemma: str,
        nome_informazione: str,
        informazione: str,
        origine: str,
        normalized_lemma: str | None = None,
        create_if_missing: bool = True,
    ) -> LemmaInfo:
        """Salvare una informazione usando lemma o normalized_lemma.

        Se il lemma non è presente e create_if_missing è True, viene creato come
        lemma manuale. Questo consente di precaricare dati da dizionari, liste o
        revisioni umane anche prima dell'osservazione in un corpus.
        """

        lang = language.strip().lower()
        norm = (normalized_lemma or lemma).strip().lower()
        vocab_id = self.get_vocab_id(language=lang, normalized_lemma=norm)
        if vocab_id is None:
            if not create_if_missing:
                raise KeyError(f"Lemma non trovato: language={lang}, normalized_lemma={norm}")
            vocab_id = self.upsert_manual_lemma(language=lang, lemma=lemma, normalized_lemma=norm)
        return self.upsert_lemma_info(
            vocab_id=vocab_id,
            nome_informazione=nome_informazione,
            informazione=informazione,
            origine=origine,
        )

    def get_lemma_info(
        self,
        *,
        vocab_id: int,
        nome_informazione: str,
        origine: str | None = None,
    ) -> LemmaInfo | None:
        """Leggere una informazione cache associata a un lemma.

        Se origine è None viene restituita la versione più recente per quel
        nome_informazione, indipendentemente dall'origine.
        """

        name = nome_informazione.strip()
        if origine is None:
            row = self.conn.execute(
                """
                SELECT * FROM info_lemma
                WHERE vocab_id = ? AND nome_informazione = ?
                ORDER BY tstamp DESC, id DESC
                LIMIT 1
                """,
                (int(vocab_id), name),
            ).fetchone()
        else:
            row = self.conn.execute(
                """
                SELECT * FROM info_lemma
                WHERE vocab_id = ? AND nome_informazione = ? AND origine = ?
                ORDER BY tstamp DESC, id DESC
                LIMIT 1
                """,
                (int(vocab_id), name, origine.strip() or "unspecified"),
            ).fetchone()
        if row is None:
            return None
        return LemmaInfo(
            vocab_id=int(row["vocab_id"]),
            nome_informazione=row["nome_informazione"],
            informazione=row["informazione"],
            origine=row["origine"],
            tstamp=row["tstamp"],
        )

    def get_lemma_info_by_lemma(
        self,
        *,
        language: str,
        normalized_lemma: str,
        nome_informazione: str,
        origine: str | None = None,
    ) -> LemmaInfo | None:
        vocab_id = self.get_vocab_id(language=language.strip().lower(), normalized_lemma=normalized_lemma.strip().lower())
        if vocab_id is None:
            return None
        return self.get_lemma_info(vocab_id=vocab_id, nome_informazione=nome_informazione, origine=origine)

    def list_lemma_info(
        self,
        *,
        vocab_id: int,
    ) -> list[LemmaInfo]:
        rows = self.conn.execute(
            """
            SELECT * FROM info_lemma
            WHERE vocab_id = ?
            ORDER BY nome_informazione, origine
            """,
            (int(vocab_id),),
        ).fetchall()
        return [
            LemmaInfo(
                vocab_id=int(row["vocab_id"]),
                nome_informazione=row["nome_informazione"],
                informazione=row["informazione"],
                origine=row["origine"],
                tstamp=row["tstamp"],
            )
            for row in rows
        ]

    def list_lemma_info_by_lemma(
        self,
        *,
        language: str,
        normalized_lemma: str,
    ) -> list[LemmaInfo]:
        vocab_id = self.get_vocab_id(language=language.strip().lower(), normalized_lemma=normalized_lemma.strip().lower())
        if vocab_id is None:
            return []
        return self.list_lemma_info(vocab_id=vocab_id)

    def list_decks(self, *, language: str | None = None) -> list[sqlite3.Row]:
        if language:
            return list(self.conn.execute("SELECT * FROM decks WHERE language = ? ORDER BY deck_name", (language,)))
        return list(self.conn.execute("SELECT * FROM decks ORDER BY language, deck_name"))
