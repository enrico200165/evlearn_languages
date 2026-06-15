#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
de_populate_ref_db_from_tokens.py

Read a UTF-8 token list, map each German token to a lemma, and populate the
German lexical reference SQLite database.

This module orchestrates the workflow only:
- read token lines;
- parse optional inline metadata after the marker declared in the header;
- determine the lemma cheaply first;
- check whether the lemma is already present in the DB;
- if absent, call de_token2lexinfo.build_de_lexical_reference(...);
- delegate persistence to de_ref_db.py.

It does not define the database schema directly and does not generate Anki decks.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from de_ref_db import (
    DEFAULT_DB_DIR,
    DEFAULT_DB_FILE_NAME,
    dump_database_pretty,
    get_lemma_id,
    insert_input_occurrence,
    insert_lexical_record,
    open_de_ref_db,
)
from de_token2lexinfo import (
    build_de_lexical_reference,
    lexical_reference_to_dict,
    normalize_word,
    produce_lemma,
)


DEFAULT_HEADER_PREFIX = "/#header/"
DEFAULT_INFO_MARKER = "/#info/"


@dataclass(frozen=True)
class TokenLine:
    """Parsed line from a token input file."""

    line_number: int
    token: str
    info_originarie: str | None
    raw_line: str


@dataclass(frozen=True)
class TokenFileParseResult:
    """Header metadata and parsed token lines."""

    headers: dict[str, str]
    marker: str
    token_lines: list[TokenLine]


@dataclass(frozen=True)
class PopulateSummary:
    """Summary returned by the top-level populate function."""

    input_file: Path
    db_path: Path
    total_token_lines: int
    inserted_lemmas: int
    existing_lemmas: int
    input_occurrences: int
    skipped_lines: int


# =============================================================================
# TOKEN FILE PARSING
# =============================================================================


def parse_header_line(line: str, header_prefix: str) -> tuple[str, str] | None:
    """Parse a line like '/#header/ marker: /#info/'."""

    if not line.startswith(header_prefix):
        return None

    body = line[len(header_prefix):].strip()
    if ":" not in body:
        return body, ""

    key, value = body.split(":", 1)
    return key.strip(), value.strip()


def parse_token_file(
    token_file_path: str | Path,
    *,
    header_prefix: str = DEFAULT_HEADER_PREFIX,
    default_marker: str = DEFAULT_INFO_MARKER,
) -> TokenFileParseResult:
    """Read a UTF-8 token file and return headers plus token rows.

    Data lines are interpreted using the marker declared in the header, for
    example:

        /#header/ marker: /#info/
        Abfahrt /#info/ article=die; example=...

    Everything after the marker is preserved verbatim as info_originarie.
    """

    path = Path(token_file_path).expanduser().resolve()
    headers: dict[str, str] = {}
    token_lines: list[TokenLine] = []
    marker = default_marker

    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw_line = raw.rstrip("\n")
            stripped = raw_line.strip()

            if not stripped:
                continue

            parsed_header = parse_header_line(stripped, header_prefix)
            if parsed_header is not None:
                key, value = parsed_header
                headers[key] = value
                if key == "marker" and value:
                    marker = value
                continue

            if marker in raw_line:
                token, info = raw_line.split(marker, 1)
                token = token.strip()
                info_originarie = info.strip() or None
            else:
                token = raw_line.strip()
                info_originarie = None

            if not token:
                continue

            token_lines.append(
                TokenLine(
                    line_number=line_number,
                    token=token,
                    info_originarie=info_originarie,
                    raw_line=raw_line,
                )
            )

    return TokenFileParseResult(
        headers=headers,
        marker=marker,
        token_lines=token_lines,
    )


# =============================================================================
# POPULATION WORKFLOW
# =============================================================================


def populate_de_reference_db_from_token_file(
    token_file_path: str | Path,
    *,
    db_dir: str | Path = DEFAULT_DB_DIR,
    db_file_name: str = DEFAULT_DB_FILE_NAME,
    print_lemmas: bool = True,
    allow_download: bool = True,
    use_wiktionary: bool = True,
    commit_every: int = 25,
    dump_after: bool = False,
) -> PopulateSummary:
    """Top-level function for importing a token list into the reference DB.

    The function keeps orchestration separate from persistence and linguistic
    analysis. It calls de_ref_db.py for all DB operations and de_token2lexinfo.py
    for linguistic analysis.
    """

    token_file = Path(token_file_path).expanduser().resolve()
    parsed = parse_token_file(token_file)

    conn = open_de_ref_db(db_dir=db_dir, db_file_name=db_file_name)
    db_path = Path(db_dir).expanduser().resolve() / db_file_name

    inserted_lemmas = 0
    existing_lemmas = 0
    input_occurrences = 0
    skipped_lines = 0

    try:
        for index, token_line in enumerate(parsed.token_lines, start=1):
            token = token_line.token

            try:
                # First determine only the lemma. This is cheaper than building
                # the full lexical reference record and allows skipping expensive
                # enrichment if the lemma is already present.
                lemma_result = produce_lemma(
                    token,
                    allow_download=allow_download,
                )
                lemma = lemma_result.lemma

                lemma_id = get_lemma_id(conn, lemma)

                if lemma_id is None:
                    lexical_record = build_de_lexical_reference(
                        token,
                        allow_download=allow_download,
                        use_wiktionary=use_wiktionary,
                    )
                    payload = lexical_reference_to_dict(lexical_record)
                    lemma = payload["lemma"]

                    lemma_id = get_lemma_id(conn, lemma)
                    if lemma_id is None:
                        lemma_id = insert_lexical_record(conn, payload)
                        inserted_lemmas += 1
                    else:
                        existing_lemmas += 1
                else:
                    existing_lemmas += 1

                insert_input_occurrence(
                    conn,
                    lemma_id,
                    input_word=token,
                    normalized_input=normalize_word(token),
                    info_originarie=token_line.info_originarie,
                    raw_line=token_line.raw_line,
                    line_number=token_line.line_number,
                    source_headers=parsed.headers,
                )
                input_occurrences += 1

                if print_lemmas:
                    print(lemma)

                if commit_every > 0 and index % commit_every == 0:
                    conn.commit()

            except Exception as exc:
                skipped_lines += 1
                print(
                    f"WARNING: skipped line {token_line.line_number}: {token!r}: {exc}"
                )

        conn.commit()

        if dump_after:
            dump_database_pretty(conn, limit_each_side=3, output=None)
            print(dump_database_pretty(conn, limit_each_side=3))

    finally:
        conn.close()

    return PopulateSummary(
        input_file=token_file,
        db_path=db_path,
        total_token_lines=len(parsed.token_lines),
        inserted_lemmas=inserted_lemmas,
        existing_lemmas=existing_lemmas,
        input_occurrences=input_occurrences,
        skipped_lines=skipped_lines,
    )


# =============================================================================
# CLI
# =============================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate German lexical reference DB from a token list."
    )

    parser.add_argument(
        "token_file",
        help="UTF-8 token list file. One German token per line."
    )

    parser.add_argument(
        "--db-dir",
        default=str(DEFAULT_DB_DIR),
        help=f"Database directory. Default: {DEFAULT_DB_DIR}"
    )

    parser.add_argument(
        "--db-file-name",
        default=DEFAULT_DB_FILE_NAME,
        help=f"Database file name. Default: {DEFAULT_DB_FILE_NAME}"
    )

    parser.add_argument(
        "--no-print-lemmas",
        action="store_true",
        help="Do not print each lemma to console."
    )

    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Do not allow downloading external lexical resources."
    )

    parser.add_argument(
        "--no-wiktionary",
        action="store_true",
        help="Do not query Wiktionary."
    )

    parser.add_argument(
        "--commit-every",
        type=int,
        default=25,
        help="Commit every N processed token lines. Default: 25."
    )

    parser.add_argument(
        "--dump-after",
        action="store_true",
        help="Pretty-print first 3 and last 3 DB entries after import."
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    summary = populate_de_reference_db_from_token_file(
        args.token_file,
        db_dir=args.db_dir,
        db_file_name=args.db_file_name,
        print_lemmas=not args.no_print_lemmas,
        allow_download=not args.no_download,
        use_wiktionary=not args.no_wiktionary,
        commit_every=args.commit_every,
        dump_after=args.dump_after,
    )

    print("Import summary")
    print(f"input_file: {summary.input_file}")
    print(f"db_path: {summary.db_path}")
    print(f"total_token_lines: {summary.total_token_lines}")
    print(f"inserted_lemmas: {summary.inserted_lemmas}")
    print(f"existing_lemmas: {summary.existing_lemmas}")
    print(f"input_occurrences: {summary.input_occurrences}")
    print(f"skipped_lines: {summary.skipped_lines}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
