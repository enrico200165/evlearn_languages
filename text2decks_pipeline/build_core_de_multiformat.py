"""
build_core_de_multiformat.py

Scopo
-----
Generare liste Core-1000, Core-2000, Core-3000, Core-4000 e Core-5000
per il tedesco, senza overlap, a partire da corpora NLP, file di testo
normali e file di sottotitoli.

Formati input gestiti
---------------------
- Archivio Leipzig .tar.gz contenente un file *sentences.txt
- File Leipzig/testo con una frase per riga oppure ID<TAB>frase
- File testo .txt, .text, .corpus, .csv, .tsv
- Sottotitoli SubRip .srt
- Sottotitoli WebVTT .vtt
- Sottotitoli SubStation Alpha / Advanced SubStation Alpha .ssa, .ass

Installazione
-------------
    python -m pip install requests spacy
    python -m spacy download de_core_news_sm

Esempi uso
----------
    python build_core_de_multiformat.py --input deu_news_2025_30K.tar.gz

    python build_core_de_multiformat.py --input corpus.txt

    python build_core_de_multiformat.py --input lezione.srt

    python build_core_de_multiformat.py --input video.vtt --limit-sentences 1000

    python build_core_de_multiformat.py --url "https://.../deu_news_2025_30K.tar.gz"

Output
------
Se --output-dir non viene indicato, la directory di output viene creata accanto
al file di input e si chiama:

    out_<radice_del_file_input_senza_estensione>

Note per il programmatore
-------------------------
La struttura è divisa in tre livelli:
1. riconoscimento formato input;
2. estrazione righe/frasi pulite dal formato sorgente;
3. analisi linguistica e scrittura CSV.

Per aggiungere un formato basta:
- aggiungere una voce in InputFormat;
- scrivere una funzione iter_sentences_from_<formato>();
- aggiornare detect_input_format() e get_sentence_iterator().
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import logging
import re
import sys
import tarfile
from collections import Counter
from enum import Enum
from pathlib import Path
from typing import Iterable, Callable
from urllib.parse import urlparse, unquote

import requests
import spacy


WORD_RE = re.compile(r"^[A-Za-zÄÖÜäöüß]+(?:-[A-Za-zÄÖÜäöüß]+)?$")
SRT_TIME_RE = re.compile(r"^\d{1,2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{1,2}:\d{2}:\d{2},\d{3}")
VTT_TIME_RE = re.compile(r"^(?:\d{1,2}:)?\d{2}:\d{2}\.\d{3}\s+-->\s+(?:\d{1,2}:)?\d{2}:\d{2}\.\d{3}")
HTML_TAG_RE = re.compile(r"<[^>]+>")
ASS_OVERRIDE_RE = re.compile(r"\{[^}]*\}")
MULTISPACE_RE = re.compile(r"\s+")


class InputFormat(str, Enum):
    """Formati input supportati."""

    AUTO = "auto"
    LEIPZIG_TAR = "leipzig-tar"
    TEXT = "text"
    SRT = "srt"
    VTT = "vtt"
    ASS = "ass"


SentenceIteratorFactory = Callable[[Path], Iterable[str]]


def input_root_name(path: Path) -> str:
    """
    Ricavare la radice del nome file di input.

    Per gli archivi .tar.gz viene rimossa l'estensione composta completa.
    """

    name = path.name

    if name.lower().endswith(".tar.gz"):
        return name[:-7]

    return path.stem


def default_output_dir_for_input(input_path: Path) -> Path:
    """
    Restituire la directory di output predefinita.
    """

    return input_path.resolve().parent / f"out_{input_root_name(input_path)}"


def filename_from_url(url: str) -> str:
    """
    Ricavare un nome file plausibile da un URL.
    """

    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name

    if not name:
        name = "downloaded_corpus.tar.gz"

    return name


def setup_logging(output_dir: Path) -> logging.Logger:
    """
    Configurare logging su console e su file.
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("build_core_de")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    file_handler = logging.FileHandler(
        output_dir / "build_core_de.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(message)s"
        )
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def download_file(url: str, output_path: Path) -> Path:
    """
    Scaricare un file da URL.
    """

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)

    return output_path


def clean_common_text(text: str) -> str:
    """
    Pulire testo proveniente da file normali o sottotitoli.
    """

    text = html.unescape(text)
    text = text.replace("\ufeff", "")
    text = HTML_TAG_RE.sub(" ", text)
    text = text.replace("♪", " ")
    text = text.replace("♫", " ")
    text = MULTISPACE_RE.sub(" ", text)

    return text.strip()


def maybe_remove_leipzig_id(line: str) -> str:
    """
    Gestire righe del tipo ID<TAB>frase.
    """

    if "\t" in line:
        first, second = line.split("\t", 1)

        if first.strip().isdigit():
            return second

    return line


def iter_sentences_from_leipzig_tar(path: Path) -> Iterable[str]:
    """
    Estrarre frasi da un archivio Leipzig .tar.gz.
    """

    with tarfile.open(path, mode="r:gz") as tar:
        members = [
            m for m in tar.getmembers()
            if m.isfile() and m.name.endswith("sentences.txt")
        ]

        if not members:
            raise RuntimeError("Nessun file sentences.txt trovato nell'archivio Leipzig.")

        member = members[0]
        extracted = tar.extractfile(member)

        if extracted is None:
            raise RuntimeError(f"Impossibile estrarre {member.name}")

        text_stream = io.TextIOWrapper(
            extracted,
            encoding="utf-8",
            errors="replace"
        )

        for line in text_stream:
            sentence = clean_common_text(maybe_remove_leipzig_id(line.strip()))

            if sentence:
                yield sentence


def iter_sentences_from_text(path: Path) -> Iterable[str]:
    """
    Leggere frasi da un normale file di testo.

    Sono accettate anche righe Leipzig ID<TAB>frase.
    """

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            sentence = clean_common_text(maybe_remove_leipzig_id(line.strip()))

            if sentence:
                yield sentence


def iter_sentences_from_srt(path: Path) -> Iterable[str]:
    """
    Estrarre testo parlato da un file .srt.

    Vengono ignorati:
    - numeri progressivi dei cue;
    - righe temporali;
    - righe vuote.
    """

    with path.open("r", encoding="utf-8-sig", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.isdigit():
                continue

            if SRT_TIME_RE.match(line):
                continue

            sentence = clean_common_text(line)

            if sentence:
                yield sentence


def iter_sentences_from_vtt(path: Path) -> Iterable[str]:
    """
    Estrarre testo parlato da un file .vtt WebVTT.

    Vengono ignorati header, cue temporali e metadati comuni.
    """

    skip_prefixes = (
        "WEBVTT",
        "NOTE",
        "STYLE",
        "REGION",
        "Kind:",
        "Language:",
    )

    with path.open("r", encoding="utf-8-sig", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith(skip_prefixes):
                continue

            if VTT_TIME_RE.match(line):
                continue

            if "-->" in line:
                continue

            sentence = clean_common_text(line)

            if sentence:
                yield sentence


def clean_ass_dialogue_text(text: str) -> str:
    """
    Pulire testo di dialogo SSA/ASS.
    """

    text = ASS_OVERRIDE_RE.sub(" ", text)
    text = text.replace(r"\N", " ")
    text = text.replace(r"\n", " ")
    text = text.replace(r"\h", " ")

    return clean_common_text(text)


def iter_sentences_from_ass(path: Path) -> Iterable[str]:
    """
    Estrarre testo da file .ass o .ssa.

    Le righe Dialogue hanno forma generale:

        Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text

    Il testo viene quindi ricavato dal decimo campo, preservando eventuali
    virgole interne nel testo.
    """

    with path.open("r", encoding="utf-8-sig", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line.startswith("Dialogue:"):
                continue

            payload = line[len("Dialogue:"):].strip()
            parts = payload.split(",", 9)

            if len(parts) < 10:
                continue

            sentence = clean_ass_dialogue_text(parts[9])

            if sentence:
                yield sentence


def detect_input_format(path: Path) -> InputFormat:
    """
    Riconoscere il formato input in base a estensione e firma minima.
    """

    name = path.name.lower()
    suffix = path.suffix.lower()

    if name.endswith(".tar.gz"):
        return InputFormat.LEIPZIG_TAR

    if suffix == ".srt":
        return InputFormat.SRT

    if suffix == ".vtt":
        return InputFormat.VTT

    if suffix in {".ass", ".ssa"}:
        return InputFormat.ASS

    return InputFormat.TEXT


def get_sentence_iterator(
    path: Path,
    input_format: InputFormat,
    logger: logging.Logger
) -> Iterable[str]:
    """
    Restituire l'iteratore corretto per il formato richiesto o rilevato.
    """

    if input_format == InputFormat.AUTO:
        detected_format = detect_input_format(path)
    else:
        detected_format = input_format

    factories: dict[InputFormat, SentenceIteratorFactory] = {
        InputFormat.LEIPZIG_TAR: iter_sentences_from_leipzig_tar,
        InputFormat.TEXT: iter_sentences_from_text,
        InputFormat.SRT: iter_sentences_from_srt,
        InputFormat.VTT: iter_sentences_from_vtt,
        InputFormat.ASS: iter_sentences_from_ass,
    }

    if detected_format not in factories:
        raise ValueError(f"Formato input non supportato: {detected_format}")

    logger.info("Formato input: %s", detected_format.value)
    logger.debug("Iteratore input selezionato: %s", factories[detected_format].__name__)

    return factories[detected_format](path)


def normalize_lemma(lemma: str) -> str:
    """
    Normalizzare un lemma tedesco.
    """

    return lemma.strip().lower()


def is_candidate_token(token) -> bool:
    """
    Decidere se un token spaCy deve essere considerato.
    """

    if token.is_space:
        return False

    if token.is_punct:
        return False

    if token.like_num:
        return False

    text = token.text.strip()

    if not WORD_RE.match(text):
        return False

    return True


def count_german_lemmas(
    sentences: Iterable[str],
    model_name: str,
    limit_sentences: int | None = None,
    logger: logging.Logger | None = None
) -> Counter:
    """
    Contare lemmi tedeschi da una sequenza di frasi.
    """

    if logger:
        logger.info("Caricamento modello spaCy: %s", model_name)

    nlp = spacy.load(
        model_name,
        disable=["ner"]
    )

    counts: Counter = Counter()
    processed = 0

    for doc in nlp.pipe(sentences, batch_size=100):
        processed += 1

        if limit_sentences is not None and processed > limit_sentences:
            break

        for token in doc:
            if not is_candidate_token(token):
                continue

            lemma = normalize_lemma(token.lemma_)

            if not lemma:
                continue

            counts[lemma] += 1

        if processed % 2500 == 0:
            if logger:
                logger.info("Frasi/righe elaborate: %s", processed)
            else:
                print(f"Frasi/righe elaborate: {processed}", file=sys.stderr)

    if logger:
        logger.info("Frasi/righe totali elaborate: %s", processed)

    return counts


def ranked_rows(counts: Counter, max_rank: int, language: str) -> list[dict]:
    """
    Convertire il Counter in righe ordinate per frequenza.
    """

    rows = []

    for rank, (lemma, freq) in enumerate(counts.most_common(max_rank), start=1):
        band_number = ((rank - 1) // 1000) + 1

        rows.append(
            {
                "rank": rank,
                "lemma": lemma,
                "frequency": freq,
                "core_band": f"Core-{band_number * 1000}",
                "language": language,
            }
        )

    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    """
    Scrivere righe CSV UTF-8.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "rank",
        "lemma",
        "frequency",
        "core_band",
        "language",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_core_bands(
    output_dir: Path,
    rows: list[dict],
    max_rank: int,
    language: str
) -> None:
    """
    Scrivere la lista completa e i blocchi da 1000 lemmi senza overlap.
    """

    full_name = f"core_0001_{max_rank}_{language}.csv"
    write_csv(output_dir / full_name, rows)

    for start in range(1, max_rank + 1, 1000):
        end = min(start + 999, max_rank)
        band_rows = [
            row for row in rows
            if start <= int(row["rank"]) <= end
        ]

        if not band_rows:
            continue

        band_name = f"core_{end}_{language}.csv"
        write_csv(output_dir / band_name, band_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generare liste Core tedesche da corpora, testi e sottotitoli."
    )

    parser.add_argument(
        "--input",
        help="File locale: .tar.gz Leipzig, .txt, .srt, .vtt, .ass, .ssa."
    )

    parser.add_argument(
        "--url",
        help="URL di un file da scaricare prima dell'elaborazione."
    )

    parser.add_argument(
        "--input-format",
        choices=[item.value for item in InputFormat],
        default=InputFormat.AUTO.value,
        help="Formato input. Default: auto."
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Directory output opzionale. Se non indicata, viene usata "
            "la directory out_<radice input> accanto al file di input."
        )
    )

    parser.add_argument(
        "--model",
        default="de_core_news_sm",
        help="Modello spaCy tedesco."
    )

    parser.add_argument(
        "--language",
        default="de",
        help="Codice lingua da scrivere nei CSV. Default: de."
    )

    parser.add_argument(
        "--max-rank",
        type=int,
        default=5000,
        help="Numero massimo di lemmi da esportare."
    )

    parser.add_argument(
        "--limit-sentences",
        type=int,
        default=None,
        help="Limite righe/frasi per test rapido."
    )

    return parser.parse_args()


def resolve_input(args: argparse.Namespace) -> tuple[Path, Path]:
    """
    Ricavare input_path e output_dir da argomenti CLI.
    """

    if args.url:
        download_name = filename_from_url(args.url)
        input_path = Path.cwd() / download_name
    elif args.input:
        input_path = Path(args.input)
    else:
        default = ".\\deutsch\\data\\leipzig\\deu_news_2025_30K.tar.gz"
        input_path = Path(default)

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else default_output_dir_for_input(input_path)
    )

    return input_path, output_dir


def main() -> None:
    args = parse_args()
    logger: logging.Logger | None = None

    try:
        input_path, output_dir = resolve_input(args)
        logger = setup_logging(output_dir)

        logger.info("Working directory: %s", Path.cwd())

        if args.url:
            logger.info("Download URL: %s", args.url)
            logger.info("File scaricato/elaborato: %s", input_path)
            logger.info("Directory output: %s", output_dir)
            download_file(args.url, input_path)
            logger.debug("Download completato: %s", input_path)
        else:
            if not args.input:
                logger.info("Nessun input specificato, uso default: %s", input_path)

            logger.info("File elaborato: %s", input_path)
            logger.info("Directory output: %s", output_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"File non trovato: {input_path}")

        input_path = input_path.resolve()
        output_dir = output_dir.resolve()

        logger.debug("Input risolto: %s", input_path)
        logger.debug("Output risolto: %s", output_dir)
        logger.debug(
            "Parametri: model=%s, language=%s, max_rank=%s, limit_sentences=%s, input_format=%s",
            args.model,
            args.language,
            args.max_rank,
            args.limit_sentences,
            args.input_format,
        )

        sentences = get_sentence_iterator(
            path=input_path,
            input_format=InputFormat(args.input_format),
            logger=logger
        )

        counts = count_german_lemmas(
            sentences=sentences,
            model_name=args.model,
            limit_sentences=args.limit_sentences,
            logger=logger
        )

        logger.debug("Lemmi distinti contati: %s", len(counts))

        rows = ranked_rows(
            counts=counts,
            max_rank=args.max_rank,
            language=args.language
        )

        logger.debug("Righe generate per export: %s", len(rows))

        write_core_bands(
            output_dir=output_dir,
            rows=rows,
            max_rank=args.max_rank,
            language=args.language
        )

        logger.info("Generate %s righe in %s", len(rows), output_dir)
        logger.info("Log dettagliato: %s", output_dir / "build_core_de.log")

    except Exception:
        if logger:
            logger.exception("Errore durante l'elaborazione")
        else:
            print("ERRORE: errore durante l'elaborazione", file=sys.stderr)

        raise SystemExit(1)


if __name__ == "__main__":
    main()
