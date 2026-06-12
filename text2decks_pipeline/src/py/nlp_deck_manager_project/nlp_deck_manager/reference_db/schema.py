from __future__ import annotations

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS vocab_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT NOT NULL,
    lemma TEXT NOT NULL,
    normalized_lemma TEXT NOT NULL,
    part_of_speech TEXT,
    observed_count INTEGER NOT NULL DEFAULT 0,
    first_observed_at TEXT,
    last_observed_at TEXT,
    origin_type TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(language, normalized_lemma)
);

CREATE TABLE IF NOT EXISTS lemma_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vocab_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(vocab_id, tag),
    FOREIGN KEY(vocab_id) REFERENCES vocab_items(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT NOT NULL,
    deck_name TEXT NOT NULL,
    description TEXT,
    deck_kind TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(language, deck_name)
);

CREATE TABLE IF NOT EXISTS lemma_deck_relations (
    vocab_id INTEGER NOT NULL,
    deck_id INTEGER NOT NULL,
    deck_description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(vocab_id, deck_id),
    FOREIGN KEY(vocab_id) REFERENCES vocab_items(id) ON DELETE CASCADE,
    FOREIGN KEY(deck_id) REFERENCES decks(id) ON DELETE CASCADE,
    CHECK (deck_description IS NULL OR length(deck_description) <= 255)
);

CREATE TABLE IF NOT EXISTS input_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_path TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(language, source_name, source_type, source_path)
);

CREATE TABLE IF NOT EXISTS source_observations (
    source_id INTEGER NOT NULL,
    vocab_id INTEGER NOT NULL,
    observed_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(source_id, vocab_id),
    FOREIGN KEY(source_id) REFERENCES input_sources(id) ON DELETE CASCADE,
    FOREIGN KEY(vocab_id) REFERENCES vocab_items(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS info_lemma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vocab_id INTEGER NOT NULL,
    nome_informazione TEXT NOT NULL,
    informazione TEXT NOT NULL,
    origine TEXT NOT NULL,
    tstamp TEXT NOT NULL,
    UNIQUE(vocab_id, nome_informazione, origine),
    FOREIGN KEY(vocab_id) REFERENCES vocab_items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_info_lemma_lookup
ON info_lemma(vocab_id, nome_informazione, origine);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT NOT NULL,
    deck_id INTEGER NOT NULL,
    vocab_id INTEGER,
    note_type TEXT NOT NULL,
    status TEXT NOT NULL,
    fields_json TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(deck_id, vocab_id, note_type),
    FOREIGN KEY(deck_id) REFERENCES decks(id) ON DELETE CASCADE,
    FOREIGN KEY(vocab_id) REFERENCES vocab_items(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS note_processing_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER NOT NULL,
    processor_name TEXT NOT NULL,
    changed INTEGER NOT NULL DEFAULT 0,
    warnings_json TEXT NOT NULL,
    errors_json TEXT NOT NULL,
    updated_fields_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
);
"""
