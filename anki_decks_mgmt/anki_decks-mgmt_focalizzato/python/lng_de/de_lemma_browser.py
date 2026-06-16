
"""
de_lemma_browser.py

Browser testuale per consultare un database SQLite di riferimento lessicale
per il tedesco.

Obiettivo:
- mostrare, in prospettiva studente, tutte le informazioni disponibili
  per un lemma;
- permettere la navigazione sequenziale tra i lemmi;
- permettere la ricerca per sottostringa o espressione regolare;
- mostrare i lemmi trovati e permettere la scelta da lista.

Dipendenze:
- obbligatorie: solo libreria standard Python;
- consigliata per una visualizzazione più leggibile: rich

Installazione consigliata:
    py -m pip install rich

Esempi:
    py de_lemma_browser.py --db path/al/database.sqlite
    py de_lemma_browser.py --db path/al/database.sqlite --lemma Haus
    py de_lemma_browser.py --db path/al/database.sqlite --table lemmas --lemma-column lemma

Comandi interattivi:
    n                  lemma successivo
    p                  lemma precedente
    g 120              vai al lemma numero 120
    s haus             cerca sottostringa
    r ^Haus            cerca regex
    l                  mostra di nuovo la lista dell'ultima ricerca
    h                  guida comandi
    q                  esci
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import shorten
from typing import Any, Iterable, Optional


try:
    from rich import box
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.prompt import IntPrompt, Prompt
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


DEFAULT_DB_PATH = Path(os.environ.get("DE_REF_DB", "de_reference.sqlite"))

LEMMA_TABLE_NAME_CANDIDATES = (
    "lemmas",
    "lemma",
    "de_lemmas",
    "de_lemma",
    "lexemes",
    "lexeme",
    "words",
    "word",
)

LEMMA_COLUMN_CANDIDATES = (
    "lemma",
    "headword",
    "lexeme",
    "word",
    "wort",
    "token",
    "form",
    "surface",
)

ID_COLUMN_CANDIDATES = (
    "id",
    "lemma_id",
    "lexeme_id",
    "word_id",
)

LONG_TEXT_COLUMNS = (
    "informazione",
    "information",
    "description",
    "descrizione",
    "note",
    "notes",
    "examples",
    "esempi",
    "conjugation",
    "coniugazione",
    "declension",
    "declinazione",
    "json",
    "raw",
    "content",
    "body",
)


@dataclass(frozen=True)
class ColumnInfo:
    cid: int
    name: str
    col_type: str
    not_null: bool
    default_value: Any
    primary_key: bool


@dataclass(frozen=True)
class TableInfo:
    name: str
    columns: list[ColumnInfo]


@dataclass(frozen=True)
class LemmaSource:
    table: str
    lemma_column: str
    id_column: Optional[str]


@dataclass(frozen=True)
class LemmaRecord:
    index: int
    row_id: Optional[Any]
    lemma: str
    row: dict[str, Any]


class LemmaBrowser:
    def __init__(
        self,
        db_path: Path,
        lemma_table: Optional[str] = None,
        lemma_column: Optional[str] = None,
        id_column: Optional[str] = None,
        max_rows_per_table: int = 1000,
        max_text_chars: int = 0,
    ) -> None:
        self.db_path = db_path
        self.max_rows_per_table = max_rows_per_table
        self.max_text_chars = max_text_chars
        self.console = Console() if RICH_AVAILABLE else None

        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row

        self.tables = self._read_schema()
        self.lemma_source = self._detect_lemma_source(
            forced_table=lemma_table,
            forced_lemma_column=lemma_column,
            forced_id_column=id_column,
        )
        self.lemmas = self._load_lemmas()
        self.current_index = 0
        self.last_matches: list[int] = []

    def close(self) -> None:
        self.conn.close()

    def _read_schema(self) -> dict[str, TableInfo]:
        rows = self.conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        result: dict[str, TableInfo] = {}
        for row in rows:
            table_name = row["name"]
            pragma_rows = self.conn.execute(
                f"PRAGMA table_info({quote_ident(table_name)})"
            ).fetchall()

            columns = [
                ColumnInfo(
                    cid=pr["cid"],
                    name=pr["name"],
                    col_type=pr["type"] or "",
                    not_null=bool(pr["notnull"]),
                    default_value=pr["dflt_value"],
                    primary_key=bool(pr["pk"]),
                )
                for pr in pragma_rows
            ]
            result[table_name] = TableInfo(name=table_name, columns=columns)

        if not result:
            raise RuntimeError("Il database non contiene tabelle consultabili.")

        return result

    def _detect_lemma_source(
        self,
        forced_table: Optional[str],
        forced_lemma_column: Optional[str],
        forced_id_column: Optional[str],
    ) -> LemmaSource:
        if forced_table:
            if forced_table not in self.tables:
                raise RuntimeError(f"Tabella lemmi non trovata: {forced_table}")

            table_info = self.tables[forced_table]
            col_names = {c.name for c in table_info.columns}

            if forced_lemma_column:
                if forced_lemma_column not in col_names:
                    raise RuntimeError(
                        f"Colonna lemma non trovata in {forced_table}: "
                        f"{forced_lemma_column}"
                    )
                lemma_col = forced_lemma_column
            else:
                lemma_col = choose_first_existing(col_names, LEMMA_COLUMN_CANDIDATES)
                if not lemma_col:
                    raise RuntimeError(
                        f"Impossibile identificare la colonna lemma in {forced_table}. "
                        "Usare --lemma-column."
                    )

            if forced_id_column:
                if forced_id_column not in col_names:
                    raise RuntimeError(
                        f"Colonna id non trovata in {forced_table}: {forced_id_column}"
                    )
                id_col = forced_id_column
            else:
                id_col = self._guess_id_column(table_info)

            return LemmaSource(
                table=forced_table,
                lemma_column=lemma_col,
                id_column=id_col,
            )

        scored: list[tuple[int, str, str, Optional[str]]] = []

        for table_info in self.tables.values():
            col_names = {c.name for c in table_info.columns}
            lemma_col = choose_first_existing(col_names, LEMMA_COLUMN_CANDIDATES)
            if not lemma_col:
                continue

            score = 0
            low_table = table_info.name.lower()

            if low_table in LEMMA_TABLE_NAME_CANDIDATES:
                score += 100

            for candidate in LEMMA_TABLE_NAME_CANDIDATES:
                if candidate in low_table:
                    score += 20

            if lemma_col == "lemma":
                score += 30

            score += min(self._count_rows(table_info.name), 10000) // 100

            scored.append(
                (
                    score,
                    table_info.name,
                    lemma_col,
                    self._guess_id_column(table_info),
                )
            )

        if not scored:
            raise RuntimeError(
                "Impossibile trovare automaticamente una tabella lemmi. "
                "Specificare --table e --lemma-column."
            )

        scored.sort(reverse=True, key=lambda item: item[0])
        _, table_name, lemma_col, id_col = scored[0]

        return LemmaSource(
            table=table_name,
            lemma_column=lemma_col,
            id_column=id_col,
        )

    def _guess_id_column(self, table_info: TableInfo) -> Optional[str]:
        for col in table_info.columns:
            if col.primary_key:
                return col.name

        col_names = {c.name for c in table_info.columns}
        return choose_first_existing(col_names, ID_COLUMN_CANDIDATES)

    def _count_rows(self, table_name: str) -> int:
        try:
            row = self.conn.execute(
                f"SELECT COUNT(*) AS n FROM {quote_ident(table_name)}"
            ).fetchone()
            return int(row["n"])
        except sqlite3.Error:
            return 0

    def _load_lemmas(self) -> list[LemmaRecord]:
        source = self.lemma_source
        columns_sql = "*"
        order_sql = f"LOWER({quote_ident(source.lemma_column)})"

        rows = self.conn.execute(
            f"""
            SELECT {columns_sql}
            FROM {quote_ident(source.table)}
            WHERE {quote_ident(source.lemma_column)} IS NOT NULL
              AND TRIM(CAST({quote_ident(source.lemma_column)} AS TEXT)) <> ''
            ORDER BY {order_sql}
            """
        ).fetchall()

        result: list[LemmaRecord] = []
        for index, row in enumerate(rows):
            data = dict(row)
            lemma = str(data[source.lemma_column])
            row_id = data.get(source.id_column) if source.id_column else None
            result.append(
                LemmaRecord(
                    index=index,
                    row_id=row_id,
                    lemma=lemma,
                    row=data,
                )
            )

        if not result:
            raise RuntimeError(
                f"La tabella {source.table} non contiene lemmi consultabili."
            )

        return result

    def run(self, start_lemma: Optional[str] = None) -> None:
        if start_lemma:
            found_index = self.find_exact_or_first_substring(start_lemma)
            if found_index is not None:
                self.current_index = found_index
            else:
                self.print_warning(
                    f"Lemma iniziale non trovato: {start_lemma}. "
                    "Viene mostrato il primo lemma."
                )

        self.show_current()

        while True:
            command = self.ask_command()
            if not command:
                continue

            should_quit = self.execute_command(command)
            if should_quit:
                break

    def ask_command(self) -> str:
        prompt = "Comando [n/p/s/r/g/l/h/q]"
        if RICH_AVAILABLE:
            return Prompt.ask(prompt, default="n").strip()
        return input(f"{prompt}: ").strip()

    def execute_command(self, command: str) -> bool:
        parts = command.split(maxsplit=1)
        action = parts[0].lower()
        argument = parts[1].strip() if len(parts) > 1 else ""

        if action in {"q", "quit", "exit", "esci"}:
            return True

        if action in {"h", "help", "aiuto", "?"}:
            self.show_help()
            return False

        if action in {"n", "next", "avanti"}:
            self.move(1)
            self.show_current()
            return False

        if action in {"p", "prev", "previous", "indietro"}:
            self.move(-1)
            self.show_current()
            return False

        if action in {"g", "goto", "vai"}:
            self.goto_command(argument)
            return False

        if action in {"s", "search", "cerca"}:
            self.search_substring_command(argument)
            return False

        if action in {"r", "regex"}:
            self.search_regex_command(argument)
            return False

        if action in {"l", "list", "lista"}:
            self.show_match_list(self.last_matches)
            self.choose_from_matches(self.last_matches)
            return False

        self.print_warning(f"Comando non riconosciuto: {command}")
        self.show_help()
        return False

    def move(self, delta: int) -> None:
        self.current_index = (self.current_index + delta) % len(self.lemmas)

    def goto_command(self, argument: str) -> None:
        if not argument:
            number = self.ask_int("Numero lemma", 1, len(self.lemmas))
        else:
            try:
                number = int(argument)
            except ValueError:
                self.print_error("Il comando g richiede un numero.")
                return

        if number < 1 or number > len(self.lemmas):
            self.print_error(f"Numero fuori intervallo: 1-{len(self.lemmas)}")
            return

        self.current_index = number - 1
        self.show_current()

    def search_substring_command(self, argument: str) -> None:
        query = argument or self.ask_text("Sottostringa da cercare")
        query = query.strip()
        if not query:
            return

        query_lower = query.casefold()
        matches = [
            item.index
            for item in self.lemmas
            if query_lower in item.lemma.casefold()
        ]

        self.last_matches = matches
        self.show_match_list(matches, title=f"Risultati per sottostringa: {query}")
        self.choose_from_matches(matches)

    def search_regex_command(self, argument: str) -> None:
        pattern = argument or self.ask_text("Regex da cercare")
        pattern = pattern.strip()
        if not pattern:
            return

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            self.print_error(f"Regex non valida: {exc}")
            return

        matches = [
            item.index
            for item in self.lemmas
            if regex.search(item.lemma)
        ]

        self.last_matches = matches
        self.show_match_list(matches, title=f"Risultati per regex: {pattern}")
        self.choose_from_matches(matches)

    def find_exact_or_first_substring(self, text: str) -> Optional[int]:
        text_norm = text.casefold()

        for item in self.lemmas:
            if item.lemma.casefold() == text_norm:
                return item.index

        for item in self.lemmas:
            if text_norm in item.lemma.casefold():
                return item.index

        return None

    def choose_from_matches(self, matches: list[int]) -> None:
        if not matches:
            return

        prompt = (
            "Numero risultato da aprire "
            "(Invio per non cambiare lemma, 0 per annullare)"
        )
        number = self.ask_optional_int(prompt)

        if number is None or number == 0:
            return

        if number < 1 or number > len(matches):
            self.print_error(f"Scelta fuori intervallo: 1-{len(matches)}")
            return

        self.current_index = matches[number - 1]
        self.show_current()

    def ask_text(self, prompt: str) -> str:
        if RICH_AVAILABLE:
            return Prompt.ask(prompt).strip()
        return input(f"{prompt}: ").strip()

    def ask_int(self, prompt: str, minimum: int, maximum: int) -> int:
        while True:
            if RICH_AVAILABLE:
                value = IntPrompt.ask(prompt)
            else:
                raw = input(f"{prompt}: ").strip()
                try:
                    value = int(raw)
                except ValueError:
                    print("Inserire un numero intero.")
                    continue

            if minimum <= value <= maximum:
                return value

            self.print_error(f"Inserire un numero tra {minimum} e {maximum}.")

    def ask_optional_int(self, prompt: str) -> Optional[int]:
        raw = self.ask_text(prompt)
        if not raw:
            return None

        try:
            return int(raw)
        except ValueError:
            self.print_error("Inserire un numero intero oppure premere Invio.")
            return None

    def show_current(self) -> None:
        lemma_record = self.lemmas[self.current_index]
        related = self.fetch_related_data(lemma_record)

        if RICH_AVAILABLE:
            self.show_current_rich(lemma_record, related)
        else:
            self.show_current_plain(lemma_record, related)

    def fetch_related_data(
        self,
        lemma_record: LemmaRecord,
    ) -> dict[str, list[dict[str, Any]]]:
        source = self.lemma_source
        result: dict[str, list[dict[str, Any]]] = {}

        for table_name, table_info in self.tables.items():
            if table_name == source.table:
                continue

            col_names = {c.name for c in table_info.columns}
            rows: list[sqlite3.Row] = []

            try:
                if (
                    lemma_record.row_id is not None
                    and source.id_column
                    and "lemma_id" in col_names
                ):
                    rows = self.conn.execute(
                        f"""
                        SELECT *
                        FROM {quote_ident(table_name)}
                        WHERE {quote_ident("lemma_id")} = ?
                        LIMIT ?
                        """,
                        (lemma_record.row_id, self.max_rows_per_table),
                    ).fetchall()

                elif (
                    lemma_record.row_id is not None
                    and source.id_column
                    and source.id_column in col_names
                    and table_name != source.table
                ):
                    rows = self.conn.execute(
                        f"""
                        SELECT *
                        FROM {quote_ident(table_name)}
                        WHERE {quote_ident(source.id_column)} = ?
                        LIMIT ?
                        """,
                        (lemma_record.row_id, self.max_rows_per_table),
                    ).fetchall()

                elif source.lemma_column in col_names:
                    rows = self.conn.execute(
                        f"""
                        SELECT *
                        FROM {quote_ident(table_name)}
                        WHERE {quote_ident(source.lemma_column)} = ?
                        LIMIT ?
                        """,
                        (lemma_record.lemma, self.max_rows_per_table),
                    ).fetchall()

                elif "lemma" in col_names:
                    rows = self.conn.execute(
                        f"""
                        SELECT *
                        FROM {quote_ident(table_name)}
                        WHERE {quote_ident("lemma")} = ?
                        LIMIT ?
                        """,
                        (lemma_record.lemma, self.max_rows_per_table),
                    ).fetchall()

                elif "token" in col_names:
                    rows = self.conn.execute(
                        f"""
                        SELECT *
                        FROM {quote_ident(table_name)}
                        WHERE {quote_ident("token")} = ?
                        LIMIT ?
                        """,
                        (lemma_record.lemma, self.max_rows_per_table),
                    ).fetchall()

            except sqlite3.Error:
                rows = []

            if rows:
                result[table_name] = [dict(row) for row in rows]

        return result

    def show_current_rich(
        self,
        lemma_record: LemmaRecord,
        related: dict[str, list[dict[str, Any]]],
    ) -> None:
        assert self.console is not None

        self.console.clear()

        total = len(self.lemmas)
        title = f"{lemma_record.lemma}   ({lemma_record.index + 1}/{total})"

        subtitle_parts = [
            f"tabella lemmi: {self.lemma_source.table}",
            f"colonna lemma: {self.lemma_source.lemma_column}",
        ]
        if self.lemma_source.id_column:
            subtitle_parts.append(f"id: {lemma_record.row_id}")

        self.console.print(
            Panel(
                "\n".join(subtitle_parts),
                title=title,
                border_style="cyan",
                expand=True,
            )
        )

        main_table = self.make_rich_key_value_table(
            "Scheda principale del lemma",
            lemma_record.row,
        )
        self.console.print(main_table)

        if not related:
            self.console.print(
                Panel(
                    "Nessuna informazione collegata trovata in altre tabelle.",
                    title="Altre informazioni",
                    border_style="yellow",
                )
            )
        else:
            for table_name, rows in related.items():
                self.console.print(self.make_rich_rows_panel(table_name, rows))

        self.console.print(
            Panel(
                "n = successivo | p = precedente | s testo = cerca | "
                "r regex = regex | g numero = vai | l = lista | h = guida | q = esci",
                title="Comandi",
                border_style="green",
            )
        )

    def make_rich_key_value_table(self, title: str, row: dict[str, Any]) -> Table:
        table = Table(
            title=title,
            box=box.ROUNDED,
            show_header=True,
            header_style="bold",
            expand=True,
        )
        table.add_column("Campo", style="cyan", no_wrap=True)
        table.add_column("Valore", overflow="fold")

        for key, value in row.items():
            table.add_row(pretty_label(key), self.format_value(value, key))

        return table

    def make_rich_rows_panel(
        self,
        table_name: str,
        rows: list[dict[str, Any]],
    ) -> Panel:
        renderables = []

        for i, row in enumerate(rows, start=1):
            table = Table(
                title=f"Record {i}",
                box=box.SIMPLE,
                show_header=False,
                expand=True,
            )
            table.add_column("Campo", style="cyan", no_wrap=True)
            table.add_column("Valore", overflow="fold")

            for key, value in row.items():
                table.add_row(pretty_label(key), self.format_value(value, key))

            renderables.append(table)

        return Panel(
            Group(*renderables),
            title=f"{pretty_label(table_name)} ({len(rows)} record)",
            border_style="blue",
            expand=True,
        )

    def format_value(self, value: Any, column_name: str = "") -> str:
        if value is None:
            return ""

        text = str(value)

        if self.max_text_chars and len(text) > self.max_text_chars:
            text = text[: self.max_text_chars] + "\n[...]"

        if column_name.lower() in LONG_TEXT_COLUMNS:
            return text

        return text

    def show_current_plain(
        self,
        lemma_record: LemmaRecord,
        related: dict[str, list[dict[str, Any]]],
    ) -> None:
        clear_terminal()

        total = len(self.lemmas)
        print("=" * 80)
        print(f"{lemma_record.lemma} ({lemma_record.index + 1}/{total})")
        print("=" * 80)
        print(
            f"Tabella lemmi: {self.lemma_source.table} | "
            f"Colonna lemma: {self.lemma_source.lemma_column}"
        )
        if self.lemma_source.id_column:
            print(f"ID: {lemma_record.row_id}")

        print("\nScheda principale del lemma")
        print("-" * 80)
        for key, value in lemma_record.row.items():
            print(f"{pretty_label(key)}: {self.format_value(value, key)}")

        if related:
            for table_name, rows in related.items():
                print("\n" + pretty_label(table_name))
                print("-" * 80)
                for i, row in enumerate(rows, start=1):
                    print(f"\nRecord {i}")
                    for key, value in row.items():
                        print(f"{pretty_label(key)}: {self.format_value(value, key)}")
        else:
            print("\nNessuna informazione collegata trovata in altre tabelle.")

        print("\nComandi: n, p, s testo, r regex, g numero, l, h, q")

    def show_match_list(
        self,
        matches: list[int],
        title: str = "Risultati ultima ricerca",
    ) -> None:
        if not matches:
            self.print_warning("Nessun lemma trovato.")
            return

        if RICH_AVAILABLE:
            assert self.console is not None

            table = Table(
                title=f"{title} - {len(matches)} lemmi",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold",
            )
            table.add_column("Scelta", justify="right", style="cyan")
            table.add_column("Indice DB", justify="right")
            table.add_column("Lemma", style="bold")

            for choice_number, lemma_index in enumerate(matches, start=1):
                lemma = self.lemmas[lemma_index]
                table.add_row(
                    str(choice_number),
                    str(lemma.index + 1),
                    lemma.lemma,
                )

            self.console.print(table)
        else:
            print(f"\n{title} - {len(matches)} lemmi")
            print("-" * 80)
            for choice_number, lemma_index in enumerate(matches, start=1):
                lemma = self.lemmas[lemma_index]
                print(f"{choice_number:>4}. [{lemma.index + 1:>6}] {lemma.lemma}")

    def show_help(self) -> None:
        text = """
Comandi disponibili

n
    Mostrare il lemma successivo.

p
    Mostrare il lemma precedente.

g NUMERO
    Andare al lemma con quel numero progressivo.

s TESTO
    Cercare tutti i lemmi che contengono TESTO.
    La ricerca non distingue maiuscole e minuscole.

r REGEX
    Cercare tutti i lemmi che corrispondono a una espressione regolare Python.
    Esempi:
        r ^ab
        r ung$
        r ^ge.*t$

l
    Mostrare di nuovo la lista dell'ultima ricerca.

h
    Mostrare questa guida.

q
    Uscire.
""".strip()

        if RICH_AVAILABLE:
            assert self.console is not None
            self.console.print(Panel(text, title="Guida", border_style="green"))
        else:
            print(text)

    def print_error(self, message: str) -> None:
        if RICH_AVAILABLE:
            assert self.console is not None
            self.console.print(f"[bold red]Errore:[/bold red] {message}")
        else:
            print(f"Errore: {message}", file=sys.stderr)

    def print_warning(self, message: str) -> None:
        if RICH_AVAILABLE:
            assert self.console is not None
            self.console.print(f"[yellow]{message}[/yellow]")
        else:
            print(message)


def choose_first_existing(
    available_columns: Iterable[str],
    candidates: Iterable[str],
) -> Optional[str]:
    available = {name.lower(): name for name in available_columns}

    for candidate in candidates:
        if candidate.lower() in available:
            return available[candidate.lower()]

    return None


def quote_ident(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def pretty_label(name: str) -> str:
    text = name.replace("_", " ").replace("-", " ").strip()
    if not text:
        return name
    return text[:1].upper() + text[1:]


def clear_terminal() -> None:
    command = "cls" if os.name == "nt" else "clear"
    os.system(command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Visualizza e naviga i lemmi presenti in un database SQLite "
            "di riferimento per il tedesco."
        )
    )

    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=(
            "Percorso del database SQLite. "
            "Default: valore della variabile DE_REF_DB oppure de_reference.sqlite"
        ),
    )

    parser.add_argument(
        "--table",
        default=None,
        help=(
            "Nome della tabella che contiene i lemmi. "
            "Se omesso viene rilevata automaticamente."
        ),
    )

    parser.add_argument(
        "--lemma-column",
        default=None,
        help=(
            "Nome della colonna che contiene il testo del lemma. "
            "Se omesso viene rilevata automaticamente."
        ),
    )

    parser.add_argument(
        "--id-column",
        default=None,
        help=(
            "Nome della colonna identificativa del lemma. "
            "Se omesso viene rilevata automaticamente."
        ),
    )

    parser.add_argument(
        "--lemma",
        default=None,
        help="Lemma iniziale da aprire.",
    )

    parser.add_argument(
        "--max-rows-per-table",
        type=int,
        default=1000,
        help=(
            "Numero massimo di righe collegate da mostrare per ogni tabella. "
            "Default: 1000"
        ),
    )

    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=0,
        help=(
            "Numero massimo di caratteri da mostrare per un singolo campo testo. "
            "0 significa nessun taglio. Default: 0"
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db).resolve()

    if not db_path.exists():
        print(f"Errore: database non trovato: {db_path}", file=sys.stderr)
        return 2

    if args.max_rows_per_table <= 0:
        print("Errore: --max-rows-per-table deve essere maggiore di zero.", file=sys.stderr)
        return 2

    if args.max_text_chars < 0:
        print("Errore: --max-text-chars non può essere negativo.", file=sys.stderr)
        return 2

    browser: Optional[LemmaBrowser] = None

    try:
        browser = LemmaBrowser(
            db_path=db_path,
            lemma_table=args.table,
            lemma_column=args.lemma_column,
            id_column=args.id_column,
            max_rows_per_table=args.max_rows_per_table,
            max_text_chars=args.max_text_chars,
        )
        browser.run(start_lemma=args.lemma)
        return 0

    except KeyboardInterrupt:
        print("\nUscita.")
        return 130

    except (RuntimeError, sqlite3.Error) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 1

    finally:
        if browser is not None:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
