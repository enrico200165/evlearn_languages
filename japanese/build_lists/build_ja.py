"""
build_core_ja_from_bccwj.py

Scopo
-----
Generare liste Core-1000, Core-2000, Core-3000, Core-4000 e Core-5000
per il giapponese, senza overlap, a partire dalla BCCWJ Word List.

Fonte consigliata
-----------------
BCCWJ Word List:
https://clrd.ninjal.ac.jp/bccwj/en/freq-list.html

La pagina ufficiale indica che la word/frequency list BCCWJ è pubblica
e gratuita per ricerca e didattica.

Idea
----
1. Scaricare manualmente la BCCWJ Word List dal sito ufficiale.
2. Passare il file allo script.
3. Identificare le colonne lemma/base form e frequenza.
4. Aggregare eventuali duplicati.
5. Ordinare per frequenza decrescente.
6. Generare blocchi senza overlap:

       Core-1000  = rank 1-1000
       Core-2000  = rank 1001-2000
       Core-3000  = rank 2001-3000
       Core-4000  = rank 3001-4000
       Core-5000  = rank 4001-5000

Installazione
-------------
    python -m pip install pandas openpyxl

Esempio
-------
    python build_core_ja_from_bccwj.py ^
        --input BCCWJ_frequency_list.xlsx ^
        --output-dir output_ja ^
        --max-rank 5000

Avvertenze
----------
- I nomi delle colonne possono variare a seconda del file scaricato.
  Per questo lo script consente di specificare --lemma-column,
  --frequency-column e --pos-column.
- Il giapponese richiede particolare attenzione a lemma, grafia,
  kana, kanji e parte del discorso.
- La lista generata deve essere considerata un punto di partenza
  didattico, non una verità assoluta.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

import pandas as pd


LEMMA_CANDIDATES = [
    "lemma",
    "base",
    "base_form",
    "基本形",
    "語彙素",
    "lexeme",
    "lForm",
    "lemma_form"
]

FREQUENCY_CANDIDATES = [
    "frequency",
    "freq",
    "count",
    "度数",
    "頻度",
    "書字形出現頻度",
    "lemma_frequency"
]

POS_CANDIDATES = [
    "pos",
    "part_of_speech",
    "品詞",
    "品詞大分類"
]


def resolve_output_dir(
    input_path: Path,
    output_dir_arg: str | None
) -> Path:
    """
    Determinare la directory di output.

    Regola predefinita:
    - se --output-dir non viene specificato, creare una directory figlia
      della directory che contiene il file di input;
    - il nome della directory è:

          out_<radice del filename di input, senza estensione>

    Esempio:
    - input:  dati/BCCWJ_frequency_list.xlsx
    - output: dati/out_BCCWJ_frequency_list

    Se --output-dir viene specificato, viene rispettato il percorso indicato.
    """

    if output_dir_arg:
        return Path(output_dir_arg).expanduser().resolve()

    input_path = input_path.expanduser().resolve()

    return input_path.parent / f"out_{input_path.stem}"


def setup_logging(
    output_dir: Path
) -> Path:
    """
    Configurare logging dettagliato su file.

    La console resta volutamente sintetica:
    - file elaborato;
    - informazioni essenziali;
    - errori.

    Il file di log contiene informazioni più dettagliate.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    log_path = output_dir / "build_core_ja.log"

    logging.basicConfig(
        filename=log_path,
        filemode="w",
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8"
    )

    return log_path


def read_table(path: Path) -> pd.DataFrame:
    """
    Leggere un file BCCWJ in formato comune.

    Supporta:
    - .xlsx
    - .xls
    - .csv
    - .tsv
    - .txt tab-delimited
    """

    suffix = path.suffix.lower()

    logging.info("Lettura file input: %s", path)
    logging.info("Formato rilevato da estensione: %s", suffix)

    if suffix in {
        ".xlsx",
        ".xls"
    }:
        df = pd.read_excel(
            path
        )
        logging.info("File Excel letto: righe=%s colonne=%s", len(df), len(df.columns))
        return df

    if suffix == ".csv":
        df = pd.read_csv(
            path,
            encoding="utf-8"
        )
        logging.info("File CSV letto: righe=%s colonne=%s", len(df), len(df.columns))
        return df

    if suffix in {
        ".tsv",
        ".txt"
    }:
        df = pd.read_csv(
            path,
            sep="\t",
            encoding="utf-8"
        )
        logging.info("File TSV/TXT letto: righe=%s colonne=%s", len(df), len(df.columns))
        return df

    raise RuntimeError(
        f"Formato non supportato: {suffix}"
    )


def normalize_column_name(
    name: str
) -> str:
    """
    Normalizzare un nome colonna per confronti semplici.
    """

    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def find_column(
    columns,
    candidates: list[str]
) -> str | None:
    """
    Cercare una colonna usando una lista di possibili nomi.

    La ricerca è volutamente tollerante.
    """

    normalized = {
        normalize_column_name(col): col
        for col in columns
    }

    for candidate in candidates:

        key = normalize_column_name(
            candidate
        )

        if key in normalized:
            return normalized[key]

    return None


def select_columns(
    df: pd.DataFrame,
    lemma_column: str | None,
    frequency_column: str | None,
    pos_column: str | None
) -> tuple[str, str, str | None]:
    """
    Determinare le colonne da usare.

    Se l'utente le specifica da riga di comando,
    vengono usate quelle.

    Altrimenti si tenta il riconoscimento automatico.
    """

    columns = list(
        df.columns
    )

    lemma = (
        lemma_column
        or
        find_column(
            columns,
            LEMMA_CANDIDATES
        )
    )

    frequency = (
        frequency_column
        or
        find_column(
            columns,
            FREQUENCY_CANDIDATES
        )
    )

    pos = (
        pos_column
        or
        find_column(
            columns,
            POS_CANDIDATES
        )
    )

    if lemma is None:
        raise RuntimeError(
            "Colonna lemma non trovata. "
            "Usare --lemma-column. "
            f"Colonne disponibili: {columns}"
        )

    if frequency is None:
        raise RuntimeError(
            "Colonna frequenza non trovata. "
            "Usare --frequency-column. "
            f"Colonne disponibili: {columns}"
        )

    logging.info("Colonne disponibili: %s", columns)
    logging.info("Colonna lemma selezionata: %s", lemma)
    logging.info("Colonna frequenza selezionata: %s", frequency)
    logging.info("Colonna POS selezionata: %s", pos)

    return lemma, frequency, pos


def normalize_lemma(
    value
) -> str:
    """
    Normalizzare la voce lessicale giapponese.

    Per il giapponese non si applica lower().
    Si rimuovono solo spazi esterni.
    """

    if pd.isna(
        value
    ):
        return ""

    return str(
        value
    ).strip()


def build_frequency_rows(
    df: pd.DataFrame,
    lemma_col: str,
    freq_col: str,
    pos_col: str | None,
    max_rank: int
) -> list[dict]:
    """
    Aggregare frequenze per lemma e generare righe ordinate.

    Se esistono più righe per lo stesso lemma,
    le frequenze vengono sommate.
    """

    records = {}
    skipped_empty_lemma = 0
    skipped_bad_frequency = 0

    logging.info("Avvio aggregazione frequenze.")

    for _, row in df.iterrows():

        lemma = normalize_lemma(
            row[lemma_col]
        )

        if not lemma:
            skipped_empty_lemma += 1
            continue

        try:
            freq = int(
                row[freq_col]
            )
        except Exception:
            skipped_bad_frequency += 1
            continue

        pos = ""

        if pos_col is not None:
            pos_value = row.get(
                pos_col,
                ""
            )
            if not pd.isna(
                pos_value
            ):
                pos = str(
                    pos_value
                ).strip()

        if lemma not in records:
            records[lemma] = {
                "lemma": lemma,
                "frequency": 0,
                "pos": pos
            }

        records[lemma]["frequency"] += freq

        if (
            not records[lemma]["pos"]
            and
            pos
        ):
            records[lemma]["pos"] = pos

    logging.info(
        "Aggregazione completata: lemmi_unici=%s righe_senza_lemma=%s righe_frequenza_non_valida=%s",
        len(records),
        skipped_empty_lemma,
        skipped_bad_frequency
    )

    sorted_items = sorted(
        records.values(),
        key=lambda item: item["frequency"],
        reverse=True
    )

    rows = []

    for rank, item in enumerate(
        sorted_items[:max_rank],
        start=1
    ):

        band_number = ((rank - 1) // 1000) + 1

        rows.append(
            {
                "rank": rank,
                "lemma": item["lemma"],
                "frequency": item["frequency"],
                "pos": item["pos"],
                "core_band": f"Core-{band_number * 1000}",
                "language": "ja"
            }
        )

    logging.info("Righe ordinate generate: %s", len(rows))

    return rows


def write_csv(
    path: Path,
    rows: list[dict]
) -> None:
    """
    Scrivere CSV UTF-8.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "rank",
        "lemma",
        "frequency",
        "pos",
        "core_band",
        "language"
    ]

    logging.info("Scrittura CSV: %s righe=%s", path, len(rows))

    with path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


def write_core_bands(
    output_dir: Path,
    rows: list[dict]
) -> None:
    """
    Scrivere:
    - lista completa core_0001_5000_ja.csv;
    - blocchi senza overlap:
      core_1000_ja.csv, core_2000_ja.csv, ...
    """

    write_csv(
        output_dir / "core_0001_5000_ja.csv",
        rows
    )

    for start in range(
        1,
        5001,
        1000
    ):

        end = start + 999

        band_rows = [
            row for row in rows
            if start <= int(row["rank"]) <= end
        ]

        band_name = f"core_{end}_ja.csv"

        write_csv(
            output_dir / band_name,
            band_rows
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generare liste Core giapponesi da BCCWJ Word List."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help="File BCCWJ Word List: .xlsx, .xls, .csv, .tsv, .txt."
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Directory output. Se non specificata, viene creata accanto "
            "al file input come out_<radice_filename_input>."
        )
    )

    parser.add_argument(
        "--lemma-column",
        default=None,
        help="Nome colonna lemma/base form."
    )

    parser.add_argument(
        "--frequency-column",
        default=None,
        help="Nome colonna frequenza."
    )

    parser.add_argument(
        "--pos-column",
        default=None,
        help="Nome colonna part of speech."
    )

    parser.add_argument(
        "--max-rank",
        type=int,
        default=5000,
        help="Numero massimo di lemmi da esportare."
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(
        args.input
    ).expanduser().resolve()

    output_dir = resolve_output_dir(
        input_path=input_path,
        output_dir_arg=args.output_dir
    )

    log_path = setup_logging(
        output_dir=output_dir
    )

    try:
        logging.info("Working directory: %s", Path.cwd())
        logging.info("Input richiesto: %s", input_path)
        logging.info("Output directory: %s", output_dir)
        logging.info("File log: %s", log_path)
        logging.info("Argomenti: %s", vars(args))

        print(
            f"File elaborato: {input_path}",
            file=sys.stderr
        )

        if not input_path.exists():
            message = f"File non trovato: {input_path}"
            logging.error(message)
            print(
                f"ERRORE: {message}",
                file=sys.stderr
            )
            raise SystemExit(
                message
            )

        df = read_table(
            input_path
        )

        lemma_col, freq_col, pos_col = select_columns(
            df=df,
            lemma_column=args.lemma_column,
            frequency_column=args.frequency_column,
            pos_column=args.pos_column
        )

        print(
            f"Colonna lemma: {lemma_col}",
            file=sys.stderr
        )

        print(
            f"Colonna frequenza: {freq_col}",
            file=sys.stderr
        )

        print(
            f"Colonna POS: {pos_col}",
            file=sys.stderr
        )

        rows = build_frequency_rows(
            df=df,
            lemma_col=lemma_col,
            freq_col=freq_col,
            pos_col=pos_col,
            max_rank=args.max_rank
        )

        write_core_bands(
            output_dir=output_dir,
            rows=rows
        )

        logging.info("Elaborazione completata: righe_generate=%s output_dir=%s", len(rows), output_dir)

        print(
            f"Generate {len(rows)} righe in {output_dir}"
        )

        print(
            f"Log dettagliato: {log_path}",
            file=sys.stderr
        )

    except Exception as exc:
        logging.exception("Errore durante l'elaborazione.")
        print(
            f"ERRORE: {exc}",
            file=sys.stderr
        )
        raise


if __name__ == "__main__":
    main()
