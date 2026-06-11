Approccio consigliato per generare wordlist da un testo tedesco in input (Python)

1. Definire cosa deve contenere la wordlist
   Prima di scrivere codice, decidere la “unità” della lista:

A) Wordform (forma come appare nel testo)
Esempio: ging, geht, gehen sono tre voci diverse.
Uso tipico: studio di un testo specifico, esercizi basati sul brano.

B) Lemma (forma base)
Esempio: ging, geht, gehen → gehen.
Uso tipico: costruire liste “core”, ridurre duplicati, copertura migliore.

Per tedesco, per liste “core” conviene quasi sempre il lemma.

2. Pipeline consigliata (robusta e riutilizzabile)
   A) Pulizia minima del testo

* normalizzare newline e spazi
* mantenere caratteri tedeschi (ä ö ü ß)
* evitare di “latinizzare” (non convertire ß in ss, non togliere umlaut)

B) Tokenizzazione + analisi linguistica

* usare spaCy con modello tedesco (de)
* estrarre:

  * token.text (wordform)
  * token.lemma_ (lemma)
  * token.pos_ (categoria grammaticale)
  * token.is_stop (stopword)
* filtrare:

  * punteggiatura
  * spazi
  * numeri puri
  * token troppo corti (opzionale, es. 1 carattere)

C) Conteggio frequenze

* conteggiare occorrenze con collections.Counter
* produrre ranking (più frequenti prima)

D) Output

* TXT “una riga per lemma”
* oppure TSV/CSV con colonne (lemma, count, freq_norm, pos, is_stop)

3. Gestione delle particolarità del tedesco (consigli pratici)
   A) Maiuscole dei sostantivi

* per le wordlist, conviene mettere tutto in minuscolo sul lemma, perché spaCy restituisce lemma coerente e riduce duplicati.
* se si vuole mantenere informazione “nome proprio” o “sostantivo”, usare pos_ e/o entità (facoltativo).

B) Composti tedeschi

* parole come Krankenversicherung, Datenschutzgrundverordnung rimarranno singole.
* la scomposizione (compound splitting) è un passo aggiuntivo e non sempre desiderabile; conviene farla solo se serve.

C) Stopword

* per liste “core” spesso si vuole includere anche le stopword (perché sono essenziali).
* per liste “contenutistiche” (studio del testo) spesso si vogliono escludere.
  Conviene produrre due liste: “con stopword” e “senza stopword”.

4. Script Python pronto (input: file .txt; output: wordlist TSV + TXT)
   Requisiti:

* spaCy installato e modello tedesco disponibile.
  Riferimenti ufficiali:
* spaCy, modelli tedeschi: [https://spacy.io/models/de](https://spacy.io/models/de)
* spaCy, modelli e download: [https://spacy.io/usage/models](https://spacy.io/usage/models)
* spaCy, stop_words e Token.is_stop: [https://spacy.io/api/language](https://spacy.io/api/language)
* spaCy, lemmatizzazione e componenti: [https://spacy.io/usage/linguistic-features](https://spacy.io/usage/linguistic-features)

Codice (salvare come de_wordlist_from_text.py):

```
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
```

Esempi d’uso:

A) Wordlist per lemma (includendo stopword)
python de_wordlist_from_text.py --input_txt testo_de.txt --out_base wordlist_de

B) Wordlist senza stopword
python de_wordlist_from_text.py --input_txt testo_de.txt --out_base wordlist_de_nostop --remove_stop

5. Come installare spaCy e il modello tedesco
   Riferimento ufficiale installazione: [https://spacy.io/usage](https://spacy.io/usage)

Esempio tipico:

* installare spaCy
* scaricare il modello tedesco (de_core_news_sm)

Nota: per uno script di wordlist, il modello “sm” di solito è sufficiente; modelli più grandi servono soprattutto se si fa analisi semantica o parsing avanzato, non per il semplice conteggio.

Se serve, posso aggiungere:

* output nel formato esatto “w : …; freq: …; categorie : …”
* normalizzazione frequenze 0–1 (log o min-max)
* una fase di assegnazione categorie basata su POS + dizionario seed (come nello script precedente)
