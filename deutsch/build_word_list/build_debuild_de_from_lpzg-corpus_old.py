"""
build_core_de_from_leipzig.py

Scopo
-----
Generare liste Core-1000, Core-2000, Core-3000, Core-4000 e Core-5000
per il tedesco, senza overlap, a partire da un corpus Leipzig Corpora
Collection.

Fonte consigliata
-----------------
Leipzig Corpora Collection:
https://wortschatz.uni-leipzig.de/en
https://aclanthology.org/L12-1154/

Idea
----
1. Leggere frasi da un archivio Leipzig .tar.gz oppure da un file locale.
2. Tokenizzare e lemmatizzare con spaCy.
3. Contare frequenze per lemma.
4. Ordinare per frequenza decrescente.
5. Generare blocchi senza overlap:

       Core-1000  = rank 1-1000
       Core-2000  = rank 1001-2000
       Core-3000  = rank 2001-3000
       Core-4000  = rank 3001-4000
       Core-5000  = rank 4001-5000

Installazione
-------------
    python -m pip install requests spacy
    python -m spacy download de_core_news_sm

Esempio uso con archivio locale
-------------------------------
    python build_core_de_from_leipzig.py ^
        --input deu_news_2023_1M.tar.gz ^
        --output-dir output_de ^
        --max-rank 5000

Esempio uso con URL
-------------------
    python build_core_de_from_leipzig.py ^
        --url "https://..." ^
        --output-dir output_de ^
        --max-rank 5000

Avvertenze
----------
- Il risultato dipende dal corpus Leipzig scelto: news, web, Wikipedia, anno, dimensione.
- Il tedesco ha flessione, maiuscole, composti e forme verbali: la lemmatizzazione
  riduce il rumore ma non è perfetta.
- Per uso didattico conviene rivedere manualmente le prime liste generate.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import tarfile
from collections import Counter
from pathlib import Path
from typing import Iterable

import requests
import spacy


WORD_RE = re.compile(r"^[A-Za-zÄÖÜäöüß]+(?:-[A-Za-zÄÖÜäöüß]+)?$")


def download_file(url: str, output_path: Path) -> Path:
    """
    Scaricare un archivio da URL.

    La funzione salva il file in output_path e restituisce il percorso.
    """

    response = requests.get(
        url,
        timeout=120
    )

    response.raise_for_status()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_bytes(
        response.content
    )

    return output_path


def iter_sentences_from_leipzig_tar(path: Path) -> Iterable[str]:
    """
    Estrarre frasi da un archivio Leipzig .tar.gz.

    Nei corpora Leipzig il file delle frasi ha normalmente un nome
    che termina con:

        sentences.txt

    Le righe hanno spesso struttura:

        ID<TAB>frase

    La funzione gestisce sia righe con tab sia righe senza tab.
    """

    with tarfile.open(
        path,
        mode="r:gz"
    ) as tar:

        members = [
            m for m in tar.getmembers()
            if m.name.endswith("sentences.txt")
        ]

        if not members:
            raise RuntimeError(
                "Nessun file sentences.txt trovato nell'archivio Leipzig."
            )

        member = members[0]

        extracted = tar.extractfile(
            member
        )

        if extracted is None:
            raise RuntimeError(
                f"Impossibile estrarre {member.name}"
            )

        text_stream = io.TextIOWrapper(
            extracted,
            encoding="utf-8",
            errors="replace"
        )

        for line in text_stream:

            line = line.strip()

            if not line:
                continue

            if "\t" in line:
                _, sentence = line.split(
                    "\t",
                    1
                )
            else:
                sentence = line

            sentence = sentence.strip()

            if sentence:
                yield sentence


def iter_sentences_from_text(path: Path) -> Iterable[str]:
    """
    Leggere frasi da un file di testo.

    Accetta:
    - una frase per riga;
    - formato Leipzig ID<TAB>frase.
    """

    with path.open(
        "r",
        encoding="utf-8",
        errors="replace"
    ) as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            if "\t" in line:
                _, sentence = line.split(
                    "\t",
                    1
                )
            else:
                sentence = line

            sentence = sentence.strip()

            if sentence:
                yield sentence


def normalize_lemma(lemma: str) -> str:
    """
    Normalizzare un lemma tedesco.

    Scelte:
    - rimuovere spazi;
    - conservare maiuscole/minuscole solo quando utili;
    - qui si usa lower() per evitare duplicati come Haus/haus.

    Nota:
    per un'applicazione avanzata si potrebbe conservare la maiuscola
    dei sostantivi e aggiungere part_of_speech.
    """

    return lemma.strip().lower()


def is_candidate_token(token) -> bool:
    """
    Decidere se un token spaCy deve essere considerato.

    Si escludono:
    - punteggiatura;
    - spazi;
    - numeri;
    - token non alfabetici;
    - stopword se si desidera una lista solo lessicale.

    In questa versione le stopword NON vengono escluse, perché un lessico core
    deve includere anche articoli, pronomi, preposizioni e connettivi.
    """

    if token.is_space:
        return False

    if token.is_punct:
        return False

    if token.like_num:
        return False

    text = token.text.strip()

    if not WORD_RE.match(
        text
    ):
        return False

    return True


def count_german_lemmas(
    sentences: Iterable[str],
    model_name: str,
    limit_sentences: int | None = None
) -> Counter:
    """
    Contare lemmi tedeschi da una sequenza di frasi.

    spaCy viene usato solo per tokenizzazione e lemmatizzazione.
    """

    nlp = spacy.load(
        model_name,
        disable=[
            "ner"
        ]
    )

    counts: Counter = Counter()

    processed = 0

    for doc in nlp.pipe(
        sentences,
        batch_size=100
    ):

        processed += 1

        if (
            limit_sentences is not None
            and
            processed > limit_sentences
        ):
            break

        for token in doc:

            if not is_candidate_token(
                token
            ):
                continue

            lemma = normalize_lemma(
                token.lemma_
            )

            if not lemma:
                continue

            counts[lemma] += 1

        if processed % 2500 == 0:
            print(
                f"Frasi elaborate: {processed}",
                file=sys.stderr
            )

    return counts


def ranked_rows(
    counts: Counter,
    max_rank: int
) -> list[dict]:
    """
    Convertire il Counter in righe ordinate per frequenza.

    Ogni riga contiene:
    - rank assoluto;
    - lemma;
    - frequency;
    - core_band.
    """

    rows = []

    for rank, (lemma, freq) in enumerate(
        counts.most_common(
            max_rank
        ),
        start=1
    ):

        band_number = ((rank - 1) // 1000) + 1

        rows.append(
            {
                "rank": rank,
                "lemma": lemma,
                "frequency": freq,
                "core_band": f"Core-{band_number * 1000}",
                "language": "de"
            }
        )

    return rows


def write_csv(
    path: Path,
    rows: list[dict]
) -> None:
    """
    Scrivere righe CSV UTF-8.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "rank",
        "lemma",
        "frequency",
        "core_band",
        "language"
    ]

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
    - lista completa core_0001_5000_de.csv;
    - blocchi senza overlap:
      core_1000_de.csv, core_2000_de.csv, ...
    """

    write_csv(
        output_dir / "core_0001_5000_de.csv",
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

        band_name = f"core_{end}_de.csv"

        write_csv(
            output_dir / band_name,
            band_rows
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generare liste Core tedesche da Leipzig Corpora Collection."
        )
    )

    parser.add_argument(
        "--input",
        help=(
            "Archivio .tar.gz Leipzig locale oppure file testo/sentences.txt."
        )
    )

    parser.add_argument(
        "--url",
        help=(
            "URL di un archivio Leipzig .tar.gz da scaricare."
        )
    )

    parser.add_argument(
        "--output-dir",
        default="output_de",
        help="Directory output."
    )

    parser.add_argument(
        "--model",
        default="de_core_news_sm",
        help="Modello spaCy tedesco."
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
        help="Limite frasi per test rapido."
    )

    return parser.parse_args()


def main() -> None:

    args = parse_args()

    output_dir = Path(
        args.output_dir
    )

    if args.url:
        input_path = output_dir / "downloaded_leipzig.tar.gz"
        print(
            f"Download: {args.url}",
            file=sys.stderr
        )
        download_file(
            args.url,
            input_path
        )

    elif args.input:
        input_path = Path(
            args.input
        )

    else:
        default = ".\\deutsch\\data\\leipzig\\deu_news_2025_30K.tar.gz"
        print(f"nessun iinput specificato, uso default: {default}", file=sys.stderr)
        input_path = Path(default)
        # raise SystemExit("Specificare --input oppure --url.")

    if not input_path.exists():
        raise SystemExit(
            f"File non trovato: {input_path}"
        )

    if input_path.suffixes[-2:] == [
        ".tar",
        ".gz"
    ]:
        sentences = iter_sentences_from_leipzig_tar(
            input_path
        )
    else:
        sentences = iter_sentences_from_text(
            input_path
        )

    counts = count_german_lemmas(
        sentences=sentences,
        model_name=args.model,
        limit_sentences=args.limit_sentences
    )

    rows = ranked_rows(
        counts=counts,
        max_rank=args.max_rank
    )

    write_core_bands(
        output_dir=output_dir,
        rows=rows
    )

    print(
        f"Generate {len(rows)} righe in {output_dir}"
    )


if __name__ == "__main__":

    print(f"working directory: {Path.cwd()}", file=sys.stderr)
    main()
