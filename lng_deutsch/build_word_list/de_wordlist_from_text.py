"""
extract_de_wordlist_from_text.py

Overview funzionale
-------------------
Questo script legge un file di testo tedesco in UTF-8 e produce una lista
di lemmi ordinati per frequenza.

Lo scopo principale è trasformare un testo tedesco libero in una wordlist
riutilizzabile in una pipeline linguistica, per esempio per:

- analizzare il lessico presente in un testo;
- generare una lista preliminare di lemmi;
- preparare input per un database lessicale;
- preparare materiale per deck linguistici;
- confrontare la frequenza relativa dei lemmi presenti nel testo.

Lo script produce due file:

1. Un file TSV con tre colonne:

       lemma
       count
       pos_most_common

   Questo file è utile per analisi, controllo manuale e importazione
   in strumenti successivi.

2. Un file TXT con un lemma per riga, ordinato per frequenza decrescente.

   Questo file è utile quando serve una lista semplice di lemmi,
   per esempio come input di altri script.

Esempio d'uso:

    python extract_de_wordlist_from_text.py ^
        --input_txt testo_tedesco.txt ^
        --out_base wordlist_de ^
        --spacy_model de_core_news_sm

Output generati:

    wordlist_de.tsv
    wordlist_de.txt

Opzioni principali:

    --input_txt
        Percorso del file di testo tedesco da analizzare.

    --out_base
        Nome base dei file di output, senza estensione.

    --spacy_model
        Nome del modello spaCy da usare.

    --min_len
        Lunghezza minima dei token da considerare.

    --remove_stop
        Esclude le stopword secondo il modello spaCy.

Avvertenze funzionali:

- La qualità dei lemmi dipende dal modello spaCy usato.
- Il campo pos_most_common è una stima basata sulle occorrenze trovate.
- La normalizzazione usa lower(), quindi non distingue tra maiuscole e minuscole.
- In tedesco questa scelta può fondere casi che, in analisi avanzate,
  sarebbe utile distinguere.

Overview tecnica
----------------
Lo script usa spaCy per tokenizzare e lemmatizzare il testo tedesco.

Flusso tecnico:

1. Leggere gli argomenti da riga di comando con argparse.
2. Caricare il modello spaCy indicato da --spacy_model.
3. Leggere tutto il file di input in memoria.
4. Analizzare il testo con spaCy.
5. Filtrare i token non utili tramite iter_tokens().
6. Applicare filtri aggiuntivi:
   - lunghezza minima;
   - eventuale esclusione delle stopword.
7. Aggiornare tre contatori:
   - frequenza delle forme osservate;
   - frequenza dei lemmi;
   - frequenza delle coppie lemma/POS.
8. Scrivere un file TSV con lemma, frequenza e POS più comune.
9. Scrivere un file TXT con un lemma per riga.

Strutture dati principali:

    Counter wordform_counter
        Conta le forme effettivamente osservate nel testo.
        In questa versione viene popolato ma non esportato.

    Counter lemma_counter
        Conta i lemmi normalizzati.

    Counter pos_counter
        Conta le coppie (lemma, POS) per stimare il POS più frequente.

Dipendenze:

    python -m pip install spacy
    python -m spacy download de_core_news_sm

Versione:
    Documentazione aggiunta senza modificare la logica originaria.
"""

import argparse
import re
from collections import Counter

import spacy


def iter_tokens(doc):
    """
    Iterare sui token spaCy utili per l'analisi lessicale.

    Parametri
    ---------
    doc
        Oggetto Doc prodotto da spaCy.

    Produce
    -------
    token spaCy
        Token non vuoti, non punteggiatura, non spazio e non numerici puri.

    Note
    ----
    Questa funzione applica solo un primo filtro generale.
    Altri filtri, come lunghezza minima e rimozione delle stopword,
    vengono applicati nel ciclo principale perché dipendono dagli
    argomenti forniti dall'utente.
    """

    for t in doc:

        # Ignorare spazi e punteggiatura: non sono unità lessicali utili
        # per una wordlist di lemmi.
        if t.is_space or t.is_punct:
            continue

        # Recuperare il testo del token rimuovendo eventuali spazi laterali.
        s = t.text.strip()

        # Ignorare token vuoti dopo la normalizzazione minima.
        if not s:
            continue

        # Ignorare numeri interi puri.
        # Esempi esclusi: 123, 2026.
        # Eventuali forme miste, come A1 o B2, non vengono escluse qui.
        if re.fullmatch(r"\d+", s):
            continue

        # Restituire il token originale spaCy, non solo la stringa,
        # perché nel main servono anche lemma_, pos_ e is_stop.
        yield t


def main() -> int:
    """
    Punto di ingresso principale dello script.

    Restituisce
    -----------
    int
        Codice di uscita del programma.

    Effetti
    -------
    Crea due file:

        <out_base>.tsv
        <out_base>.txt
    """

    # Configurazione degli argomenti da riga di comando.
    ap = argparse.ArgumentParser(
        description=(
            "Estrarre una wordlist di lemmi da un testo tedesco UTF-8 "
            "usando spaCy."
        )
    )

    ap.add_argument(
        "--input_txt",
        required=True,
        help="Percorso al testo tedesco (UTF-8)"
    )

    ap.add_argument(
        "--out_base",
        default="wordlist_de",
        help="Base nome file output (senza estensione)"
    )

    ap.add_argument(
        "--spacy_model",
        default="de_core_news_sm",
        help="Modello spaCy per tedesco"
    )

    ap.add_argument(
        "--min_len",
        type=int,
        default=2,
        help="Lunghezza minima token (default 2)"
    )

    ap.add_argument(
        "--remove_stop",
        action="store_true",
        help="Escludere stopword dalla lista"
    )

    args = ap.parse_args()

    # Caricare il modello spaCy indicato dall'utente.
    # Per il tedesco, il default previsto è de_core_news_sm.
    nlp = spacy.load(args.spacy_model)

    # Leggere l'intero file di input.
    # Questa scelta è semplice e adeguata per file piccoli o medi.
    # Per corpora molto grandi sarebbe preferibile una pipeline a streaming.
    with open(args.input_txt, "r", encoding="utf-8") as f:
        text = f.read()

    # Analizzare il testo con spaCy.
    # Il risultato contiene token, lemmi, POS e informazioni linguistiche.
    doc = nlp(text)

    # Contatore delle forme effettive osservate nel testo.
    # Esempio: geht, ging, gegangen.
    # In questa versione il contatore è calcolato ma non esportato.
    wordform_counter = Counter()

    # Contatore dei lemmi normalizzati.
    # Esempio: gehen.
    lemma_counter = Counter()

    # Contatore delle coppie lemma/POS.
    # Serve per stimare il POS più comune associato a ciascun lemma.
    pos_counter = Counter()

    for t in iter_tokens(doc):

        # Escludere token più corti della lunghezza minima richiesta.
        # Il controllo usa t.text, quindi la lunghezza è quella della forma
        # osservata nel testo, non del lemma.
        if len(t.text) < args.min_len:
            continue

        # Escludere le stopword solo se richiesto esplicitamente.
        # Per un vocabolario core può essere utile NON escluderle,
        # perché articoli, preposizioni e pronomi sono frequenti e importanti.
        if args.remove_stop and t.is_stop:
            continue

        # Normalizzare la forma osservata.
        # lower() riduce duplicati dovuti a maiuscole/minuscole.
        wf = t.text.lower()

        # Usare il lemma spaCy quando disponibile.
        # Se lemma_ è vuoto, usare la forma testuale originale.
        lemma = (t.lemma_ or t.text).lower()

        # Aggiornare i contatori.
        wordform_counter[wf] += 1
        lemma_counter[lemma] += 1
        pos_counter[(lemma, t.pos_)] += 1

    # Output 1:
    # File TSV con lemma, frequenza e POS più comune.
    # Il POS più comune è calcolato scorrendo pos_counter per ogni lemma.
    # Questa soluzione è chiara ma non ottimizzata per file molto grandi.
    out_tsv = args.out_base + ".tsv"

    with open(out_tsv, "w", encoding="utf-8") as f:

        # Header del file TSV.
        f.write("lemma	count	pos_most_common
")

        # I lemmi vengono esportati in ordine di frequenza decrescente.
        for lemma, c in lemma_counter.most_common():

            # Cercare il POS più frequente per il lemma corrente.
            pos = None
            best = 0

            for (lem, p), pc in pos_counter.items():
                if lem == lemma and pc > best:
                    best = pc
                    pos = p

            f.write(f"{lemma}	{c}	{pos or ''}
")

    # Output 2:
    # File TXT con un lemma per riga, sempre ordinato per frequenza.
    # Questo formato è adatto come input semplice per altri script.
    out_txt = args.out_base + ".txt"

    with open(out_txt, "w", encoding="utf-8") as f:
        for lemma, c in lemma_counter.most_common():
            f.write(f"{lemma}
")

    # Messaggio finale sintetico.
    print("OK")
    print("Creati:", out_tsv, out_txt)

    return 0


if __name__ == "__main__":

    # Convertire il valore restituito da main() in codice di uscita
    # del processo.
    raise SystemExit(main())
