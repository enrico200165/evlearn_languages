# Lezione 2 - Manipolare Collezioni, Deck e Note Anki da Python

## Obiettivo

Nella lezione precedente è stata definita l'architettura generale di una pipeline per:

* creare deck da liste esterne;
* arricchire deck esistenti;
* correggere contenuti;
* filtrare parole per frequenza;
* generare contenuti tramite IA o servizi online.

In questa lezione verranno introdotte le API Anki realmente necessarie per:

* aprire una collezione;
* cercare note;
* leggere campi;
* modificare campi;
* aggiungere tag;
* individuare note incomplete;
* preparare il terreno per la generazione automatica dei contenuti.

Non verranno ancora affrontati:

* Google Translate;
* ChatGPT;
* generazione contenuti;
* coniugazioni;
* creazione di nuove note.

Questi argomenti saranno trattati nelle lezioni successive.

---

# Obiettivo reale

Per il tipo di progetto che si vuole sviluppare, la maggior parte del lavoro consiste nel trasformare dati.

Schema tipico:

```
parola -> frequenza -> generazione contenuti -> nota Anki
```

oppure:

```
nota Anki esistente -> analisi -> completamento -> salvataggio
```

Per fare questo è necessario saper manipolare correttamente una collezione.

---

# Apertura della collezione

Come visto nella lezione precedente, durante lo sviluppo si lavora normalmente fuori da Anki.

Import:

```
from anki.collection import Collection
```

Apertura:

```
col = Collection(
    "collection_test.anki2"
)
```

Chiusura:

```
col.close(save=True)
```

Schema completo:

```
from anki.collection import Collection

col = Collection(
    "collection_test.anki2"
)

try:
    pass

finally:
    col.close(save=True)
```

---

# La collezione

L'oggetto principale è:

```
col
```

Attraverso questo oggetto è possibile:

* cercare note;
* leggere note;
* modificare note;
* creare note;
* creare deck;
* salvare modifiche.

Nelle prossime lezioni verranno utilizzate continuamente istruzioni come:

```
col.find_notes(...)

col.get_note(...)
```

---

# Cercare note

## Ricerca globale

Tutte le note:

```
note_ids = col.find_notes("")
```

Esempio:

```
note_ids = col.find_notes("")

print(f"Note trovate: {len(note_ids)}")
```

---

## Ricerca per tag

Esempio:

```
note_ids = col.find_notes(
    "tag:da_controllare"
)
```

---

## Ricerca per deck

Esempio:

```
note_ids = col.find_notes(
    "deck:Tedesco"
)
```

---

## Ricerca per tipo di nota

Esempio:

```
note_ids = col.find_notes(
    "note:Vocabulary"
)
```

---

## Combinare criteri

Esempio:

```
note_ids = col.find_notes(
    "deck:Tedesco tag:da_controllare"
)
```

---

## Perché è importante

La ricerca consente di selezionare soltanto le note che richiedono elaborazione.

Esempio:

```
tag:missing_examples
```

oppure:

```
tag:needs_translation
```

oppure:

```
deck:German_B1
```

Questo evita elaborazioni inutili.

---

# Ottenere una nota

Una ricerca restituisce ID.

Per ottenere la nota:

```
note = col.get_note(
    note_id
)
```

Esempio:

```
note_ids = col.find_notes("")

note = col.get_note(
    note_ids[0]
)
```

---

# Elencare i campi disponibili

Prima di leggere o scrivere conviene controllare i campi presenti.

Esempio:

```
print(
    note.keys()
)
```

Output possibile:

```
dict_keys([
    "Word",
    "Translation",
    "Examples",
    "Notes"
])
```

---

# Leggere un campo

I campi si leggono come un dizionario.

Esempio:

```
word = note["Word"]

print(word)
```

---

## Accesso sicuro

Esempio:

```
if "Word" in note.keys():

    word = note["Word"]
```

---

## Funzione riutilizzabile

```
def get_field_safe(
    note,
    field_name
):

    if (
        field_name
        not in note.keys()
    ):
        raise KeyError(
            f"Campo mancante: "
            f"{field_name}"
        )

    return note[field_name]
```

Uso:

```
word = get_field_safe(
    note,
    "Word"
)
```

---

# Scrivere un campo

Esempio:

```
note["Translation"] = "casa"
```

Per rendere permanente la modifica:

```
note.flush()
```

Schema completo:

```
note["Translation"] = "casa"

note.flush()
```

---

# Aggiornare più campi

Esempio:

```
note["Translation"] = "andare"

note["Examples"] = (
    "Ich gehe nach Hause."
)

note.flush()
```

---

# Individuare campi vuoti

Uno degli utilizzi più frequenti consiste nel trovare note incomplete.

Esempio:

```
if not note["Examples"].strip():

    print(
        "Campo Examples vuoto"
    )
```

---

## Caso pratico

Trovare note senza esempi.

```
note_ids = col.find_notes(
    "deck:Tedesco"
)

for note_id in note_ids:

    note = col.get_note(
        note_id
    )

    if ("Examples" not in note.keys() ):
        continue

    if (not note["Examples"].strip()):
        print(f"Nota {note_id} "
            f"senza esempi"
        )
```

Questo tipo di controllo verrà utilizzato spesso nelle lezioni successive.

---

# Aggiungere tag

I tag sono utili per tenere traccia dello stato di elaborazione.

Esempio:

```
note.add_tag("processed")

note.flush()
```

---

# Rimuovere tag

Esempio:

```
note.del_tag("needs_translation")

note.flush()
```

---

# Workflow basato su tag

Esempio:

```
needs_translation
```

dopo la traduzione:

```
translated
```

Schema:

```
note.del_tag("needs_translation")

note.add_tag("translated")

note.flush()
```

Questo consente di evitare elaborazioni duplicate.

---

# Aggiornamento condizionale

Non sempre si vuole sovrascrivere un campo.

Esempio:

```
if (not note["Examples"].strip()):

    note["Examples"] = (
        generated_examples
    )

    note.flush()
```

Questo approccio è molto più sicuro.

---

# Elaborare un insieme di note

Schema generale:

```
note_ids = col.find_notes("tag:needs_examples")

for note_id in note_ids:

    note = col.get_note(note_id)

    ...
```

Questa struttura sarà alla base della maggior parte delle pipeline.

---

# Funzione generica di elaborazione

È utile creare funzioni indipendenti dal contenuto.

Esempio:

```
def process_notes(
    col,
    query,
    callback
):

    note_ids = col.find_notes(
        query
    )

    for note_id in note_ids:

        note = col.get_note(note_id)

        callback(note)
```

Uso:

```
process_notes(
    col=col,
    query="tag:needs_examples",
    callback=process_note
)
```

Questo approccio favorisce il riuso del codice.

---

# Analizzare un deck esistente

Uno degli obiettivi principali del progetto è correggere e completare deck già esistenti.

Esempio:

```
report = {
    "missing_translation": 0,
    "missing_examples": 0,
    "missing_notes": 0
}

note_ids = col.find_notes(
    "deck:Tedesco"
)

for note_id in note_ids:

    note = col.get_note(
        note_id
    )

    if (
        not note["Translation"]
        .strip()
    ):
        report["missing_translation"] += 1

    if (not note["Examples"].strip()):
        report["missing_examples"] += 1

print(report)
```

Output possibile:

```
{
    "missing_translation": 42,
    "missing_examples": 187,
    "missing_notes": 0
}
```

Questo tipo di analisi dovrebbe sempre precedere una modifica massiva.

---

# Salvare report

Durante le elaborazioni è utile produrre report.

Esempio CSV:

```
note_id,status,reason
1234,updated,examples_added
1235,skipped,already_present
1236,error,missing_field
```

Questo consente di verificare facilmente il risultato.

---

# Gestione degli errori

Mai interrompere l'intera elaborazione per una singola nota problematica.

Schema:

```
for note_id in note_ids:

    try:

        note = col.get_note(note_id)

        ...

    except Exception as e:

        print(
            f"Errore nota "
            f"{note_id}: {e}"
        )
```

---

# Preparazione alla lezione successiva

Nella prossima lezione verranno introdotti:

* Google Translate;
* ChatGPT;
* generazione di esempi;
* generazione di coniugazioni;
* trasformazione automatica dei campi.

Le API Anki viste in questa lezione costituiranno la base su cui verranno innestate le chiamate ai servizi esterni.

---

# Regole pratiche

1. Aprire sempre una copia della collezione durante lo sviluppo.

2. Usare sempre:

   ```
   note.flush()
   ```

   dopo una modifica.

3. Non assumere mai che un campo esista.

4. Controllare sempre i campi vuoti prima di generare contenuti.

5. Usare tag per tracciare lo stato di elaborazione.

6. Creare report dopo elaborazioni massive.

7. Gestire sempre le eccezioni.

8. Analizzare il deck prima di modificarlo.

9. Separare la logica Anki dalla logica AI.

10. Preparare il codice in modo che possa funzionare sia con:

    ```
    Collection(path)
    ```

    sia con:

    ```
    mw.col
    ```

---

## Alcuni riferimenti

Anki Python Module https://addon-docs.ankiweb.net/the-anki-module.html

Searching https://docs.ankiweb.net/searching.html

Python API Documentation https://dev-docs.ankiweb.net/en/latest/api-python-modules.html

evread: 1
