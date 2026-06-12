# NLP Deck Management Platform

Versione: 1.0

## Obiettivo

Il sistema è una piattaforma per la gestione, generazione, arricchimento e manutenzione di deck linguistici.

Le funzionalità principali comprendono:

- creazione di nuovi deck;
- aggiunta di nuove notes;
- aggiornamento di notes esistenti;
- correzione massiva di notes;
- arricchimento automatico delle notes;
- analisi di deck esistenti;
- importazione di dati da corpora, sottotitoli e testi;
- integrazione con traduttori, dizionari, servizi AI e codice personalizzato;
- gestione di una base lessicale globale per lingua.

Il sistema è progettato per essere multilingua.

Le lingue di interesse primario sono:

- Tedesco (de)
- Giapponese (ja)

ma l'architettura deve consentire l'aggiunta di altre lingue senza modifiche sostanziali.

---

# Visione generale

## Diagramma generale

    @startuml

    artifact "Corpus / Sottotitoli / Testi" as INPUT

    component "Readers"

    component "Normalizer"

    component "NLP"

    database "Language Reference DB"

    component "Deck Manager"

    component "Note Processing Pipeline"

    artifact "Anki Deck"

    INPUT --> Readers
    Readers --> Normalizer
    Normalizer --> NLP

    NLP --> "Language Reference DB"

    "Language Reference DB" --> "Deck Manager"

    "Deck Manager" --> "Note Processing Pipeline"

    "Note Processing Pipeline" --> "Anki Deck"

    @enduml

---

# Concetti fondamentali

## Deck

Un deck rappresenta una raccolta logica di notes.

Esempi:

- German A1
- German Core 1000
- German Travel
- JLPT N5
- Japanese Core Vocabulary

Un deck è identificato da:

- nome
- lingua
- descrizione

---

## Note

La note è l'entità principale del sistema.

Una note può contenere:

- lemma
- traduzione
- lettura
- frase esempio
- traduzione frase
- audio
- immagini
- tag
- campi personalizzati

Il contenuto effettivo dipende dal modello di note utilizzato.

---

## Lemma

Un lemma rappresenta un vocabolo normalizzato.

Esempi:

    Haus
    gehen
    食べる
    学校

Un lemma può essere:

- osservato nei corpora;
- importato da fonti esterne;
- inserito manualmente.

---

# Language Reference Database

## Scopo

Il Language Reference DB rappresenta il repository globale dei lemmi di una lingua.

Ogni lingua possiede il proprio database.

Esempio:

    vocab_reference_dbs/

        vocab_reference_de.sqlite

        vocab_reference_ja.sqlite

---

## Regola fondamentale

Tutti i lemmi osservati durante l'elaborazione dei testi di input devono essere inseriti nel Language Reference DB.

Possono inoltre essere presenti:

- lemmi inseriti manualmente;
- lemmi importati da altre fonti;
- lemmi non ancora osservati nei corpora elaborati.

---

## Ruolo del Reference DB

Il Reference DB consente di:

- tracciare globalmente i lemmi;
- evitare duplicazioni indesiderate;
- sapere in quali deck compare un lemma;
- supportare la generazione di nuovi deck;
- supportare analisi e statistiche;
- fungere da base dati lessicale comune a tutti i deck.

---

# Modello dati

## Diagramma concettuale

    @startuml

    entity Lemma

    entity LemmaTag

    entity Deck

    entity LemmaDeckRelation

    Lemma ||--o{ LemmaTag

    Lemma ||--o{ LemmaDeckRelation

    Deck ||--o{ LemmaDeckRelation

    @enduml

---

## Entità Lemma

Campi principali:

    id

    language

    lemma

    normalized_lemma

    created_at

    updated_at

Vincolo:

    UNIQUE(language, normalized_lemma)

---

## Entità LemmaTag

I tag appartengono al lemma.

Non appartengono al deck.

Non appartengono alla relazione lemma-deck.

Sono stringhe libere.

Esempi:

    noun

    verb

    adjective

    building

    food

    travel

    common

    jlpt_n5

    jlpt_n4

    a1

    a2

    b1

Un lemma può avere:

- nessun tag;
- uno o più tag.

---

## Entità Deck

Campi principali:

    id

    language

    deck_name

    description

    created_at

    updated_at

---

## Entità LemmaDeckRelation

Rappresenta la presenza di un lemma in un deck.

Un lemma può:

- non appartenere ad alcun deck;
- appartenere ad un deck;
- apparten