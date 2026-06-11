
# Lezione focalizzata: gestione programmativa di note Anki per add-on semplici

## Obiettivo

Costruire add-on Anki semplici che:

- cercano note con query Anki;
- leggono campi specifici;
- chiamano servizi online;
- scrivono il risultato in altri campi;
- salvano le modifiche in modo sicuro;
- mostrano solo messaggi essenziali.

Non vengono trattate GUI avanzate, finestre personalizzate, editor, reviewer, importatori o QTableWidget.

## Prerequisito operativo

Un add-on minimo si trova in una cartella dentro `addons21` e contiene almeno:

    my_translate_addon/
        __init__.py
        config.json

La cartella degli add-on si apre da Anki con:

    Strumenti > Add-on > Visualizza file

La documentazione ufficiale descrive questo flusso nella pagina “Add-on Folders”: https://addon-docs.ankiweb.net/addon-folders.html

## 1. Oggetti realmente usati nel codice

Per add-on semplici servono quasi sempre questi oggetti:

    from aqt import mw

    mw
    mw.col
    mw.addonManager

Significato operativo:

    mw

è la finestra principale di Anki. Serve come punto di accesso globale.

    mw.col

è l’oggetto collezione. Serve per cercare, leggere e modificare note.

    mw.addonManager

serve per leggere la configurazione dell’add-on.

Esempio minimo:

    from aqt import mw

    def run() -> None:
        col = mw.col
        note_ids = col.find_notes("deck:Inglese")
        print(note_ids)

## 2. Cercare note con query Anki

Il metodo più utile è:

    mw.col.find_notes(query)

Restituisce una lista di ID nota.

Esempi:

    note_ids = mw.col.find_notes("deck:Inglese")
    note_ids = mw.col.find_notes("tag:da_tradurre")
    note_ids = mw.col.find_notes("note:Vocabulary")
    note_ids = mw.col.find_notes("deck:Inglese tag:da_tradurre")
    note_ids = mw.col.find_notes('"Front:dog"')

Le query usano la sintassi di ricerca standard di Anki, la stessa del browser. La pagina ufficiale è: https://docs.ankiweb.net/searching.html

Esempio pratico:

    from aqt import mw
    from aqt.utils import showInfo

    def count_notes_to_translate() -> None:
        query = "tag:da_tradurre"
        note_ids = mw.col.find_notes(query)
        showInfo(f"Note trovate: {len(note_ids)}")

## 3. Recuperare una nota

Dato un ID nota:

    note = mw.col.get_note(note_id)

Esempio:

    note_ids = mw.col.find_notes("tag:da_tradurre")

    for note_id in note_ids:
        note = mw.col.get_note(note_id)
        print(note)

## 4. Leggere campi

I campi si leggono con sintassi dizionario:

    testo = note["Front"]

Esempio:

    note = mw.col.get_note(note_id)

    source_text = note["Front"]
    current_translation = note["Back"]

Attenzione: i nomi dei campi sono case-sensitive. `Front` e `front` non sono equivalenti. La documentazione ufficiale sulle sostituzioni di campo conferma che i nomi dei campi sono sensibili alle maiuscole/minuscole: https://docs.ankiweb.net/templates/fields.html

## 5. Verificare se un campo esiste

Prima di leggere o scrivere conviene controllare i campi disponibili.

    def has_field(note, field_name: str) -> bool:
        return field_name in note.keys()

Uso:

    if "Front" not in note.keys():
        return

    text = note["Front"]

Versione più utile:

    def get_field_safe(note, field_name: str) -> str:
        if field_name not in note.keys():
            raise KeyError(f"Campo mancante: {field_name}")
        return note[field_name]

## 6. Scrivere campi

Per scrivere:

    note["Back"] = "traduzione"

Poi bisogna salvare:

    note.flush()

Esempio:

    note = mw.col.get_note(note_id)
    note["Back"] = "cane"
    note.flush()

Schema tipico:

    for note_id in note_ids:
        note = mw.col.get_note(note_id)
        source = note["Front"]

        translated = translate_text(source)

        note["Back"] = translated
        note.flush()

## 7. Aggiornare l’interfaccia dopo modifiche

Dopo modifiche massive:

    mw.reset()

Esempio:

    def process_notes() -> None:
        note_ids = mw.col.find_notes("tag:da_tradurre")

        for note_id in note_ids:
            note = mw.col.get_note(note_id)
            note["Back"] = "test"
            note.flush()

        mw.reset()

## 8. Evitare sovrascritture involontarie

Per add-on di traduzione, conviene non sovrascrivere campi già compilati.

    def should_update_field(note, target_field: str, overwrite: bool) -> bool:
        current = note[target_field].strip()

        if overwrite:
            return True

        return current == ""

Uso:

    if should_update_field(note, "Back", overwrite=False):
        note["Back"] = translated
        note.flush()

## 9. Configurazione dell’add-on

File:

    config.json

Esempio:

    {
        "query": "tag:da_tradurre",
        "source_field": "Front",
        "target_field": "Back",
        "overwrite": false,
        "service_url": "https://example.com/translate"
    }

Lettura:

    from aqt import mw

    config = mw.addonManager.getConfig(__name__)

Documentazione ufficiale: https://addon-docs.ankiweb.net/addon-config.html

Funzione consigliata:

    def get_config() -> dict:
        cfg = mw.addonManager.getConfig(__name__) or {}

        return {
            "query": cfg.get("query", "tag:da_tradurre"),
            "source_field": cfg.get("source_field", "Front"),
            "target_field": cfg.get("target_field", "Back"),
            "overwrite": bool(cfg.get("overwrite", False)),
            "service_url": cfg.get("service_url", "")
        }

## 10. Aggiungere una voce di menu

Per add-on semplici basta una voce nel menu Strumenti.

    from aqt import mw
    from aqt.qt import QAction

    def run() -> None:
        pass

    action = QAction("Traduci note selezionate", mw)
    action.triggered.connect(run)
    mw.form.menuTools.addAction(action)

Questo è l’unico uso di Qt necessario per il caso trattato.

## 11. Messaggi utente essenziali

Import:

    from aqt.utils import showInfo, showCritical

Uso:

    showInfo("Operazione completata.")
    showCritical("Errore durante la traduzione.")

Esempio:

    try:
        process_notes()
        showInfo("Traduzione completata.")
    except Exception as e:
        showCritical(f"Errore: {e}")

## 12. Chiamare un servizio online

Per servizi esterni serve gestire:

- timeout;
- errori HTTP;
- risposte non valide;
- rate limit;
- rete assente;
- cache locale.

Esempio generico con `requests`:

    import requests

    def translate_text(text: str, service_url: str) -> str:
        response = requests.post(
            service_url,
            json={"text": text, "source": "en", "target": "it"},
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if "translation" not in data:
            raise RuntimeError("Risposta non valida: manca 'translation'.")

        return data["translation"]

Nota: Google Translate non offre una semplice API pubblica gratuita non autenticata per questo uso. Per codice stabile conviene usare API ufficiali o servizi con contratto/API key.

## 13. Template completo: leggere campo, tradurre, scrivere campo

File:

    __init__.py

Codice:

    import os
    import datetime
    import requests

    from aqt import mw
    from aqt.qt import QAction
    from aqt.utils import showInfo, showCritical


    def addon_dir() -> str:
        return os.path.dirname(__file__)


    def log_line(message: str) -> None:
        path = os.path.join(addon_dir(), "translate_addon.log")
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {message}\n")
        except Exception:
            pass


    def get_config() -> dict:
        cfg = mw.addonManager.getConfig(__name__) or {}

        return {
            "query": cfg.get("query", "tag:da_tradurre"),
            "source_field": cfg.get("source_field", "Front"),
            "target_field": cfg.get("target_field", "Back"),
            "overwrite": bool(cfg.get("overwrite", False)),
            "service_url": cfg.get("service_url", "")
        }


    def translate_text(text: str, service_url: str) -> str:
        response = requests.post(
            service_url,
            json={
                "text": text,
                "source": "en",
                "target": "it"
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        translation = data.get("translation")
        if not translation:
            raise RuntimeError("Traduzione mancante nella risposta del servizio.")

        return translation.strip()


    def validate_note_fields(note, source_field: str, target_field: str) -> None:
        fields = note.keys()

        if source_field not in fields:
            raise KeyError(f"Campo sorgente mancante: {source_field}")

        if target_field not in fields:
            raise KeyError(f"Campo destinazione mancante: {target_field}")


    def process_notes() -> dict:
        cfg = get_config()

        query = cfg["query"]
        source_field = cfg["source_field"]
        target_field = cfg["target_field"]
        overwrite = cfg["overwrite"]
        service_url = cfg["service_url"]

        if not service_url:
            raise RuntimeError("service_url non configurato.")

        note_ids = mw.col.find_notes(query)

        result = {
            "found": len(note_ids),
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }

        for note_id in note_ids:
            try:
                note = mw.col.get_note(note_id)

                validate_note_fields(note, source_field, target_field)

                source_text = note[source_field].strip()

                if not source_text:
                    result["skipped"] += 1
                    log_line(f"Nota {note_id}: campo sorgente vuoto.")
                    continue

                current_target = note[target_field].strip()

                if current_target and not overwrite:
                    result["skipped"] += 1
                    log_line(f"Nota {note_id}: destinazione già compilata.")
                    continue

                translated = translate_text(source_text, service_url)

                note[target_field] = translated
                note.flush()

                result["updated"] += 1
                log_line(f"Nota {note_id}: aggiornata.")

            except Exception as e:
                result["errors"] += 1
                log_line(f"Nota {note_id}: errore: {e}")

        mw.reset()
        return result


    def run() -> None:
        try:
            result = process_notes()

            showInfo(
                "Operazione completata.\n\n"
                f"Note trovate: {result['found']}\n"
                f"Note aggiornate: {result['updated']}\n"
                f"Note saltate: {result['skipped']}\n"
                f"Errori: {result['errors']}"
            )

        except Exception as e:
            log_line(f"Errore generale: {e}")
            showCritical(f"Errore: {e}")


    action = QAction("Traduci campi note", mw)
    action.triggered.connect(run)
    mw.form.menuTools.addAction(action)

## 14. Variante: processare solo note con campo destinazione vuoto

Query consigliata:

    tag:da_tradurre

Il controllo sul campo vuoto conviene farlo nel codice, non solo nella query, perché è più chiaro e controllabile:

    if note[target_field].strip():
        continue

## 15. Variante: aggiungere un tag dopo la traduzione

Per evitare di riprocessare le stesse note:

    note.add_tag("tradotta")
    note.flush()

Esempio:

    note[target_field] = translated
    note.add_tag("tradotta")
    note.flush()

Query iniziale:

    tag:da_tradurre -tag:tradotta

La sintassi di ricerca con tag e negazioni è documentata nella pagina ufficiale di ricerca: https://docs.ankiweb.net/searching.html

## 16. Variante: rimuovere un tag dopo la traduzione

    note.del_tag("da_tradurre")
    note.add_tag("tradotta")
    note.flush()

Schema:

    note[target_field] = translated
    note.del_tag("da_tradurre")
    note.add_tag("tradotta")
    note.flush()

## 17. Variante: cache locale per non richiamare il servizio

Per servizi online è utile evitare richieste duplicate.

Esempio semplice:

    import json
    import os

    def cache_path() -> str:
        return os.path.join(addon_dir(), "translation_cache.json")


    def load_cache() -> dict:
        path = cache_path()

        if not os.path.exists(path):
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


    def save_cache(cache: dict) -> None:
        path = cache_path()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)


    def translate_with_cache(text: str, service_url: str, cache: dict) -> str:
        key = text.strip()

        if key in cache:
            return cache[key]

        translated = translate_text(text, service_url)
        cache[key] = translated

        return translated

Uso nel ciclo:

    cache = load_cache()

    translated = translate_with_cache(source_text, service_url, cache)

    save_cache(cache)

Per file grandi, salvare la cache alla fine o ogni N note.

## 18. Variante: limite massimo di note per test

Nel config:

    {
        "max_notes": 20
    }

Nel codice:

    max_notes = int(cfg.get("max_notes", 0))

    if max_notes > 0:
        note_ids = note_ids[:max_notes]

Serve per evitare di lanciare per errore centinaia di richieste online.

## 19. Variante: dry run

Nel config:

    {
        "dry_run": true
    }

Nel codice:

    if dry_run:
        log_line(f"DRY RUN nota {note_id}: {source_text} -> {translated}")
    else:
        note[target_field] = translated
        note.flush()

## 20. Regole pratiche per add-on che modificano note

1. Non modificare direttamente `collection.anki2`.

La documentazione ufficiale avverte di non manipolare direttamente i file della collezione mentre Anki è aperto: https://docs.ankiweb.net/files.html

2. Usare sempre `mw.col`, `get_note()`, accesso ai campi e `flush()`.

3. Fare prima prove con:

    "max_notes": 5,
    "dry_run": true

4. Non sovrascrivere campi già compilati salvo configurazione esplicita.

5. Loggare sempre ogni errore per nota.

6. Usare timeout nelle chiamate HTTP.

7. Non fare affidamento su servizi web non ufficiali o non documentati.

8. Dopo modifiche massive chiamare:

    mw.reset()

## 21. Struttura consigliata del progetto reale

Per restare semplice ma ordinato:

    translate_addon/
        __init__.py
        config.json
        net.py
        anki_ops.py
        logging_utils.py

Divisione:

    __init__.py

menu e funzione principale.

    anki_ops.py

ricerca note, lettura campi, scrittura campi.

    net.py

chiamate HTTP.

    logging_utils.py

logging.

Esempio di `anki_ops.py`:

    from aqt import mw


    def find_note_ids(query: str) -> list[int]:
        return mw.col.find_notes(query)


    def get_note(note_id: int):
        return mw.col.get_note(note_id)


    def read_field(note, field_name: str) -> str:
        if field_name not in note.keys():
            raise KeyError(f"Campo mancante: {field_name}")

        return note[field_name].strip()


    def write_field(note, field_name: str, value: str) -> None:
        if field_name not in note.keys():
            raise KeyError(f"Campo mancante: {field_name}")

        note[field_name] = value
        note.flush()


    def add_tag(note, tag: str) -> None:
        note.add_tag(tag)
        note.flush()


    def remove_tag(note, tag: str) -> None:
        note.del_tag(tag)
        note.flush()


    def refresh_anki() -> None:
        mw.reset()

## 22. Cosa studiare dopo

Per l’obiettivo indicato, l’ordine utile è:

1. `mw.col.find_notes()`
2. `mw.col.get_note()`
3. `note.keys()`
4. `note["Campo"]`
5. `note["Campo"] = valore`
6. `note.flush()`
7. `note.add_tag()`
8. `note.del_tag()`
9. `mw.addonManager.getConfig(__name__)`
10. gestione HTTP con timeout e cache

Solo dopo ha senso studiare:

- hook;
- task asincroni;
- GUI;
- editor;
- reviewer;
- webview.

## Alcuni riferimenti

Writing Anki Add-ons – Add-on Folders
https://addon-docs.ankiweb.net/addon-folders.html

Writing Anki Add-ons – Add-on Config
https://addon-docs.ankiweb.net/addon-config.html

Writing Anki Add-ons – Hooks & Filters
https://addon-docs.ankiweb.net/hooks-and-filters.html

Anki Manual – Searching
https://docs.ankiweb.net/searching.html

Anki Manual – Field Replacements
https://docs.ankiweb.net/templates/fields.html

Anki Manual – Managing Files
https://docs.ankiweb.net/files.html

