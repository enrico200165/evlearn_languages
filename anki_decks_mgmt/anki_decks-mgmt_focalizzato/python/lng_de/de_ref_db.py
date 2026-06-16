#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
de_ref_db.py

Database access layer for the German lexical reference database.

This module is intentionally limited to persistence concerns:
- opening/creating the SQLite database;
- creating the schema;
- checking whether a lemma already exists;
- mapping LexicalReferenceRecord objects produced by de_token2lexinfo.py to tables;
- adding source-token occurrences;
- pretty-printing a small dump of the database for inspection.

It must not perform linguistic analysis and must not generate Anki decks.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, TextIO


# =============================================================================
# PSEUDO-CONSTANTS
# =============================================================================

DEFAULT_DB_DIR = Path("./lng_deutsch/ref_dbs")
DEFAULT_DB_FILE_NAME = "de_ref_db"
DEFAULT_LANGUAGE = "de"
SCHEMA_VERSION = 1


# =============================================================================
# LOW-LEVEL UTILITIES
# =============================================================================


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with seconds precision."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_dumps(value: Any) -> str:
    """Serialize arbitrary nested data to stable UTF-8 friendly JSON text.

    SQLite has no mandatory JSON type. Storing complex fields as JSON text keeps
    the schema flexible while still allowing later migrations to more normalized
    tables if specific fields become important for querying.
    """

    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def object_to_dict(value: Any) -> dict[str, Any]:
    """Convert dataclass-like or dict-like lexical objects to a plain dict.

    de_token2lexinfo.py exposes lexical_reference_to_dict(...), but accepting a
    dataclass or an already-converted dict makes this module easier to test and
    keeps the persistence layer robust against minor caller variations.
    """

    if isinstance(value, dict):
        return value

    if is_dataclass(value):
        return asdict(value)

    raise TypeError(
        "Expected a LexicalReferenceRecord dataclass or a dict-compatible payload."
    )


def normalize_db_file_name(db_file_name: str) -> str:
    """Return the DB file name exactly as requested unless it is empty.

    SQLite does not require a file extension. The project default is therefore
    the exact file name requested by the user: de_ref_db.
    """

    cleaned = db_file_name.strip()
    if not cleaned:
        raise ValueError("db_file_name cannot be empty")
    return cleaned


# =============================================================================
# CONNECTION AND SCHEMA
# =============================================================================


def open_de_ref_db(
    db_dir: str | Path = DEFAULT_DB_DIR,
    db_file_name: str = DEFAULT_DB_FILE_NAME,
) -> sqlite3.Connection:
    """Open the German reference SQLite database, creating it if needed."""

    db_dir_path = Path(db_dir).expanduser().resolve()
    db_dir_path.mkdir(parents=True, exist_ok=True)

    db_path = db_dir_path / normalize_db_file_name(db_file_name)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Foreign keys are disabled by default in SQLite; enable them explicitly.
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    create_schema(conn)

    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes required by the reference DB.

    The schema mirrors the top-level structure returned by
    de_token2lexinfo.build_de_lexical_reference(...), but keeps the full payload
    as JSON as well. This gives two advantages:
    1. important query fields are normalized into columns/tables;
    2. no information is lost if the lexical object evolves.
    """

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS lemma_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT NOT NULL,
            lemma TEXT NOT NULL,
            normalized_lemma TEXT NOT NULL,
            pos TEXT,
            confidence TEXT,
            lemma_source TEXT,
            lemma_alternatives_json TEXT NOT NULL DEFAULT '[]',
            pos_candidates_json TEXT NOT NULL DEFAULT '[]',
            family_key TEXT,
            base_lemma TEXT,
            related_lemmas_json TEXT NOT NULL DEFAULT '[]',
            derivation_notes_json TEXT NOT NULL DEFAULT '[]',
            common_json TEXT NOT NULL DEFAULT '{}',
            pos_specific_json TEXT NOT NULL DEFAULT '{}',
            sources_json TEXT NOT NULL DEFAULT '[]',
            warnings_json TEXT NOT NULL DEFAULT '[]',
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(language, normalized_lemma)
        );

        CREATE TABLE IF NOT EXISTS input_occurrence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lemma_id INTEGER NOT NULL,
            input_word TEXT NOT NULL,
            normalized_input TEXT,
            info_originarie TEXT,
            raw_line TEXT,
            line_number INTEGER,
            source_headers_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY (lemma_id) REFERENCES lemma_record(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS word_form (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lemma_id INTEGER NOT NULL,
            form TEXT NOT NULL,
            features_json TEXT NOT NULL DEFAULT '[]',
            source_field TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (lemma_id) REFERENCES lemma_record(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS noun_inflection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lemma_id INTEGER NOT NULL,
            case_name TEXT,
            number_name TEXT,
            form TEXT,
            definite_article TEXT,
            indefinite_article TEXT,
            with_definite_article TEXT,
            with_indefinite_article TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (lemma_id) REFERENCES lemma_record(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS example_sentence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lemma_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            sentence TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'generated',
            created_at TEXT NOT NULL,
            FOREIGN KEY (lemma_id) REFERENCES lemma_record(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_lemma_record_lemma
            ON lemma_record(language, normalized_lemma);

        CREATE INDEX IF NOT EXISTS idx_input_occurrence_lemma_id
            ON input_occurrence(lemma_id);

        CREATE INDEX IF NOT EXISTS idx_word_form_lemma_id
            ON word_form(lemma_id);

        CREATE INDEX IF NOT EXISTS idx_example_sentence_lemma_id
            ON example_sentence(lemma_id);
        """
    )

    conn.execute(
        "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
        ("schema_version", str(SCHEMA_VERSION)),
    )
    conn.commit()


# =============================================================================
# QUERY HELPERS
# =============================================================================


def normalize_lemma_for_db(lemma: str) -> str:
    """Normalize a lemma for uniqueness checks.

    German capitalization is linguistically meaningful. Therefore this function
    strips surrounding spaces but does not lowercase the lemma.
    """

    return " ".join(lemma.strip().split())


def get_lemma_id(
    conn: sqlite3.Connection,
    lemma: str,
    language: str = DEFAULT_LANGUAGE,
) -> int | None:
    """Return the lemma id if the lemma already exists, otherwise None."""

    normalized = normalize_lemma_for_db(lemma)
    row = conn.execute(
        """
        SELECT id
        FROM lemma_record
        WHERE language = ? AND normalized_lemma = ?
        """,
        (language, normalized),
    ).fetchone()

    return int(row["id"]) if row else None


def lemma_exists(
    conn: sqlite3.Connection,
    lemma: str,
    language: str = DEFAULT_LANGUAGE,
) -> bool:
    """Return True if the lemma is already present in the reference DB."""

    return get_lemma_id(conn, lemma, language) is not None


# =============================================================================
# INSERT / MAPPING FUNCTIONS
# =============================================================================


def insert_lexical_record(
    conn: sqlite3.Connection,
    lexical_record: Any,
) -> int:
    """Insert a new lexical record and all directly derived child rows.

    The function assumes the caller has already checked that the lemma is not
    present. If the lemma is already present, SQLite's unique constraint will
    prevent duplication.
    """

    payload = object_to_dict(lexical_record)
    now = utc_now_iso()

    language = payload.get("language", DEFAULT_LANGUAGE)
    lemma = payload.get("lemma")
    if not lemma:
        raise ValueError("lexical_record does not contain a valid lemma")

    lexical_family = payload.get("lexical_family") or {}

    cursor = conn.execute(
        """
        INSERT INTO lemma_record (
            language,
            lemma,
            normalized_lemma,
            pos,
            confidence,
            lemma_source,
            lemma_alternatives_json,
            pos_candidates_json,
            family_key,
            base_lemma,
            related_lemmas_json,
            derivation_notes_json,
            common_json,
            pos_specific_json,
            sources_json,
            warnings_json,
            payload_json,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            language,
            lemma,
            normalize_lemma_for_db(lemma),
            payload.get("pos"),
            payload.get("confidence"),
            payload.get("lemma_source"),
            json_dumps(payload.get("lemma_alternatives", [])),
            json_dumps(payload.get("pos_candidates", [])),
            lexical_family.get("family_key"),
            lexical_family.get("base_lemma"),
            json_dumps(lexical_family.get("related_lemmas", [])),
            json_dumps(lexical_family.get("derivation_notes", [])),
            json_dumps(payload.get("common", {})),
            json_dumps(payload.get("pos_specific", {})),
            json_dumps(payload.get("sources", [])),
            json_dumps(payload.get("warnings", [])),
            json_dumps(payload),
            now,
            now,
        ),
    )

    lemma_id = int(cursor.lastrowid)

    insert_word_forms_from_payload(conn, lemma_id, payload)
    insert_noun_inflections_from_payload(conn, lemma_id, payload)
    insert_example_sentences_from_payload(conn, lemma_id, payload)

    return lemma_id


def insert_word_forms_from_payload(
    conn: sqlite3.Connection,
    lemma_id: int,
    payload: dict[str, Any],
) -> None:
    """Insert word-form rows extracted from common and POS-specific payloads."""

    now = utc_now_iso()
    rows: list[tuple[int, str, str, str, str]] = []

    common_forms = (payload.get("common") or {}).get("forms", [])
    for item in common_forms:
        form = item.get("form")
        if form:
            rows.append(
                (lemma_id, form, json_dumps(item.get("features", [])), "common.forms", now)
            )

    pos_specific = payload.get("pos_specific") or {}
    for field_name in ("present_forms", "past_forms", "participles", "all_verb_forms", "forms"):
        for item in pos_specific.get(field_name, []) or []:
            form = item.get("form")
            if form:
                rows.append(
                    (lemma_id, form, json_dumps(item.get("features", [])), f"pos_specific.{field_name}", now)
                )

    if rows:
        conn.executemany(
            """
            INSERT INTO word_form (
                lemma_id,
                form,
                features_json,
                source_field,
                created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )


def insert_noun_inflections_from_payload(
    conn: sqlite3.Connection,
    lemma_id: int,
    payload: dict[str, Any],
) -> None:
    """Insert noun inflection rows, when present."""

    rows = []
    now = utc_now_iso()
    pos_specific = payload.get("pos_specific") or {}

    for item in pos_specific.get("inflection_with_articles", []) or []:
        rows.append(
            (
                lemma_id,
                item.get("case"),
                item.get("number"),
                item.get("form"),
                item.get("definite_article"),
                item.get("indefinite_article"),
                item.get("with_definite_article"),
                item.get("with_indefinite_article"),
                now,
            )
        )

    if rows:
        conn.executemany(
            """
            INSERT INTO noun_inflection (
                lemma_id,
                case_name,
                number_name,
                form,
                definite_article,
                indefinite_article,
                with_definite_article,
                with_indefinite_article,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def insert_example_sentences_from_payload(
    conn: sqlite3.Connection,
    lemma_id: int,
    payload: dict[str, Any],
) -> None:
    """Insert generated example sentences."""

    rows = []
    now = utc_now_iso()

    for position, sentence in enumerate(payload.get("example_sentences", []) or [], start=1):
        if sentence:
            rows.append((lemma_id, position, sentence, "generated", now))

    if rows:
        conn.executemany(
            """
            INSERT INTO example_sentence (
                lemma_id,
                position,
                sentence,
                source,
                created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )


def insert_input_occurrence(
    conn: sqlite3.Connection,
    lemma_id: int,
    *,
    input_word: str,
    normalized_input: str | None = None,
    info_originarie: str | None = None,
    raw_line: str | None = None,
    line_number: int | None = None,
    source_headers: dict[str, str] | None = None,
) -> int:
    """Record that an input token line mapped to an existing or new lemma."""

    cursor = conn.execute(
        """
        INSERT INTO input_occurrence (
            lemma_id,
            input_word,
            normalized_input,
            info_originarie,
            raw_line,
            line_number,
            source_headers_json,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lemma_id,
            input_word,
            normalized_input,
            info_originarie,
            raw_line,
            line_number,
            json_dumps(source_headers or {}),
            utc_now_iso(),
        ),
    )

    return int(cursor.lastrowid)


# =============================================================================
# PRETTY DUMP
# =============================================================================


def _select_first_last_ids(
    conn: sqlite3.Connection,
    limit_each_side: int,
) -> list[int]:
    """Return ids for the first N and last N lemma records without duplicates."""

    first_rows = conn.execute(
        "SELECT id FROM lemma_record ORDER BY id ASC LIMIT ?",
        (limit_each_side,),
    ).fetchall()

    last_rows = conn.execute(
        "SELECT id FROM lemma_record ORDER BY id DESC LIMIT ?",
        (limit_each_side,),
    ).fetchall()

    ids: list[int] = []
    for row in first_rows:
        ids.append(int(row["id"]))
    for row in reversed(last_rows):
        row_id = int(row["id"])
        if row_id not in ids:
            ids.append(row_id)
    return ids


def dump_database_pretty(
    conn: sqlite3.Connection,
    *,
    limit_each_side: int = 3,
    output: TextIO | None = None,
) -> str:
    """Pretty-print the first N and last N lemma entries.

    By default the function dumps the first 3 and last 3 entries, which is
    enough to verify that the database is populated without flooding the console.
    """

    total = conn.execute("SELECT COUNT(*) AS n FROM lemma_record").fetchone()["n"]
    ids = _select_first_last_ids(conn, limit_each_side)

    lines = [
        "German reference DB dump",
        f"schema_version: {SCHEMA_VERSION}",
        f"lemma_records: {total}",
        f"shown_entries: {len(ids)}",
        "",
    ]

    for lemma_id in ids:
        row = conn.execute(
            """
            SELECT *
            FROM lemma_record
            WHERE id = ?
            """,
            (lemma_id,),
        ).fetchone()

        examples = conn.execute(
            """
            SELECT sentence
            FROM example_sentence
            WHERE lemma_id = ?
            ORDER BY position ASC
            LIMIT 2
            """,
            (lemma_id,),
        ).fetchall()

        occurrences = conn.execute(
            """
            SELECT input_word, info_originarie, line_number
            FROM input_occurrence
            WHERE lemma_id = ?
            ORDER BY id ASC
            LIMIT 2
            """,
            (lemma_id,),
        ).fetchall()

        lines.append(f"id: {row['id']}")
        lines.append(f"lemma: {row['lemma']}")
        lines.append(f"pos: {row['pos']}")
        lines.append(f"confidence: {row['confidence']}")
        lines.append(f"sources: {row['sources_json']}")
        lines.append("examples:")
        for example in examples:
            lines.append(f"  - {example['sentence']}")
        lines.append("input_occurrences:")
        for occurrence in occurrences:
            lines.append(
                f"  - line={occurrence['line_number']} input={occurrence['input_word']} info={occurrence['info_originarie']}"
            )
        lines.append("")

    text = "\n".join(lines)

    if output is not None:
        print(text, file=output)

    return text
