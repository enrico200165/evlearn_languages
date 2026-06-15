# de_token2lexinfo.py - documentazione funzionale e tecnica

## Scopo del modulo

`de_token2lexinfo.py` è un modulo linguistico puro per la lingua tedesca.
Riceve una parola o forma tedesca in input e restituisce una struttura dati articolata con informazioni lessicali, morfologiche e di esempio.

Il modulo non deve:

- aprire connessioni SQLite;
- scrivere nel database;
- generare deck Anki;
- produrre campi specifici per Anki.

Il suo compito è produrre un oggetto dati coerente e serializzabile. La persistenza nel reference database deve essere gestita da un modulo separato.

## Funzione top

La funzione principale è:

    build_de_lexical_reference(word, pos_hint=None, cache_dir=DEFAULT_CACHE_DIR, allow_download=True, use_wiktionary=True, examples_count=5)

Input principale:

    word
        Parola, token o forma tedesca da analizzare.

Parametri importanti:

    pos_hint
        Suggerimento opzionale sulla parte del discorso, per esempio NOUN, VERB, ADJ.

    cache_dir
        Directory locale per i dati scaricati e riutilizzabili.

    allow_download
        Se True permette il download automatico di risorse esterne cacheabili.

    use_wiktionary
        Se True permette il recupero opzionale di dati nominali da Wiktionary.

    examples_count
        Numero di frasi di esempio da generare.

Output:

    LexicalReferenceRecord

## Struttura dati restituita

`LexicalReferenceRecord` contiene:

    language
        Codice lingua, attualmente de.

    input_word
        Forma originale ricevuta in input.

    normalized_input
        Forma normalizzata per elaborazioni interne.

    lemma
        Lemma principale stimato.

    lemma_source
        Fonte usata per determinare il lemma.

    lemma_alternatives
        Lemmi alternativi rilevati.

    pos
        Parte del discorso principale stimata.

    pos_candidates
        Parti del discorso candidate.

    lexical_family
        Informazioni sulla famiglia lessicale, se ricavabili.

    common
        Dati morfologici comuni e forme disponibili.

    pos_specific
        Dati specifici per la parte del discorso.

    example_sentences
        Frasi di esempio semplici che includono la parola o il lemma.

    sources
        Fonti usate per costruire il record.

    warnings
        Avvisi su dati mancanti, incerti o non determinati.

    confidence
        Stima qualitativa complessiva dell'affidabilità del record.

## Fonti linguistiche usate

Il modulo usa tre livelli di fonte.

### UniMorph

UniMorph è la fonte principale per lemma e forme flesse.
Il file viene scaricato una volta e poi letto dalla cache locale.

URL usato dal codice:

    https://raw.githubusercontent.com/unimorph/deu/master/deu

### spaCy

spaCy è un fallback opzionale per la lemmatizzazione, se installato.
Non è obbligatorio.

Installazione opzionale:

    python -m pip install spacy
    python -m spacy download de_core_news_sm

### Wiktionary tedesco

Wiktionary viene usato come fonte ausiliaria, soprattutto per dati nominali come genere e plurale.

Endpoint usato dal codice:

    https://de.wiktionary.org/w/api.php

Il parser è prudente: se un dato non è riconosciuto con sufficiente affidabilità, il modulo preferisce lasciare il campo mancante e inserire un warning.

## Dati specifici per parte del discorso

Il campo `pos_specific` varia in base alla parte del discorso.

### Sostantivi

Per i sostantivi il modulo cerca di produrre:

    gender
    plural
    wiktionary_data
    inflection_with_articles

`inflection_with_articles` contiene, quando disponibili, forme per casi e numeri con articolo determinativo e indeterminativo.

### Verbi

Per i verbi il modulo produce:

    forms_count
    present_forms
    past_forms
    participles
    all_verb_forms

Le forme derivano principalmente da UniMorph.

### Aggettivi

Per gli aggettivi il modulo produce:

    forms_count
    forms

### Altre parti del discorso

Per le parti del discorso non ancora specializzate il modulo produce un payload generico con le forme disponibili.

## Frasi di esempio

Le frasi di esempio sono generate in modo deterministico tramite template semplici.

Questa scelta è intenzionale:

- produce risultati riproducibili;
- evita chiamate AI non tracciate;
- consente test automatici;
- fornisce esempi iniziali per il reference database.

Le frasi generate non sostituiscono esempi autentici da corpus. In una fase successiva potranno essere affiancate o sostituite da frasi estratte da corpora, purché siano conservati fonte, qualità e stato di revisione.

## Conversione in dizionario

Per facilitare l'uso da parte del modulo database, è disponibile:

    lexical_reference_to_dict(record)

Questa funzione non salva nulla. Converte il dataclass in un dizionario serializzabile, adatto a essere mappato da un modulo esterno su tabelle SQLite o su JSON.

## Uso minimo

    from de_token2lexinfo import (
        build_de_lexical_reference,
        lexical_reference_to_dict,
    )

    record = build_de_lexical_reference(
        "Häuser",
        pos_hint="NOUN",
    )

    data = lexical_reference_to_dict(record)

    print(data["lemma"])
    print(data["pos"])
    print(data["pos_specific"])
    print(data["example_sentences"])

## Uso da riga di comando

Il modulo contiene una funzione dimostrativa CLI.

Esempio:

    python de_token2lexinfo.py Häuser --pos NOUN

L'output è JSON leggibile su console.

## Contratto architetturale

Il modulo garantisce questo contratto:

    input: parola o token tedesco
    output: oggetto linguistico strutturato
    nessuna persistenza
    nessuna generazione Anki
    nessuna assunzione sullo schema SQLite

La persistenza dovrà essere gestita da moduli come:

    de_reference_schema.py
    de_reference_db.py
    de_reference_populate.py

La generazione dei deck Anki dovrà appartenere a una fase successiva e indipendente.

## Limiti noti

Il modulo non deve essere considerato una fonte infallibile.

Limiti principali:

- UniMorph non contiene necessariamente tutte le informazioni utili per un dizionario didattico completo;
- Wiktionary ha markup non sempre uniforme;
- la famiglia lessicale è stimata con euristiche conservative;
- le frasi di esempio sono template-based;
- la confidence deve essere usata dal modulo database per decidere se marcare il record come da revisionare.

Regola progettuale:

    meglio un campo mancante con warning che un dato non verificato presentato come certo.
