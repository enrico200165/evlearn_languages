import argparse
import re
from collections import Counter

import spacy


def iter_tokens(doc):
    for t in doc:
        if t.is_space or t.is_punct:
            continue
        s = t.text.strip()
        if not s:
            continue
        if re.fullmatch(r"\d+", s):
            continue
        yield t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_txt", required=True, help="Percorso al testo tedesco (UTF-8)")
    ap.add_argument("--out_base", default="wordlist_de", help="Base nome file output (senza estensione)")
    ap.add_argument("--spacy_model", default="de_core_news_sm", help="Modello spaCy per tedesco")
    ap.add_argument("--min_len", type=int, default=2, help="Lunghezza minima token (default 2)")
    ap.add_argument("--remove_stop", action="store_true", help="Escludere stopword dalla lista")
    args = ap.parse_args()

    nlp = spacy.load(args.spacy_model)

    with open(args.input_txt, "r", encoding="utf-8") as f:
        text = f.read()

    doc = nlp(text)

    wordform_counter = Counter()
    lemma_counter = Counter()
    pos_counter = Counter()

    for t in iter_tokens(doc):
        if len(t.text) < args.min_len:
            continue
        if args.remove_stop and t.is_stop:
            continue

        wf = t.text.lower()
        lemma = (t.lemma_ or t.text).lower()

        wordform_counter[wf] += 1
        lemma_counter[lemma] += 1
        pos_counter[(lemma, t.pos_)] += 1

    # Output 1: TSV con lemma, count, pos più comune (approssimato)
    out_tsv = args.out_base + ".tsv"
    with open(out_tsv, "w", encoding="utf-8") as f:
        f.write("lemma\tcount\tpos_most_common\n")
        for lemma, c in lemma_counter.most_common():
            # POS più frequente per quel lemma
            pos = None
            best = 0
            for (lem, p), pc in pos_counter.items():
                if lem == lemma and pc > best:
                    best = pc
                    pos = p
            f.write(f"{lemma}\t{c}\t{pos or ''}\n")

    # Output 2: TXT “una riga per lemma” (ordinato per frequenza)
    out_txt = args.out_base + ".txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        for lemma, c in lemma_counter.most_common():
            f.write(f"{lemma}\n")

    print("OK")
    print("Creati:", out_tsv, out_txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
