
## Esempi vanilla: chiamate Google Translate e ChatGPT da un valore di campo Anki

Questi esempi non usano librerie client specifiche. Usano solo:

    requests

Obiettivo:

- leggere un campo di una nota Anki;
- inviare il testo a un servizio online;
- ricevere una risposta;
- scrivere il risultato in un altro campo;
- mostrare una messagebox se mancano le credenziali;
- scrivere sempre l’errore anche su file di log.

Riferimenti ufficiali:

Google Cloud Translation API
https://docs.cloud.google.com/translate/docs/reference/rest

OpenAI API - Text generation
https://developers.openai.com/api/docs/guides/text

OpenAI API - Responses API
https://developers.openai.com/api/reference/overview/

## Configurazione

File:

    config.json

Esempio:

    {
        "query": "tag:da_tradurre",
        "source_field": "Front",
        "target_field_google": "Back",
        "target_field_chatgpt": "Example",
        "overwrite": false,

        "google_translate_api_key": "",
        "google_source_language": "en",
        "google_target_language": "it",

        "openai_api_key": "",
        "openai_model": "gpt-5.5-mini",
        "openai_instruction": "Traduci in italiano in modo naturale e conciso il testo seguente."
    }

Nota importante:

- `google_translate_api_key` deve essere una API key valida di Google Cloud Translation.
- `openai_api_key` deve essere una API key valida OpenAI.
- Se una chiave è assente, l’add-on mostra `showCritical()` e scrive nel log.

## File completo: __init__.py

    import os
    import datetime
    import requests

    from aqt import mw
    from aqt.qt import QAction
    from aqt.utils import showInfo, showCritical


    LOG_FILE_NAME = "online_translation_addon.log"


    def addon_dir() -> str:
        return os.path.dirname(__file__)


    def log_line(message: str) -> None:
        log_path = os.path.join(addon_dir(), LOG_FILE_NAME)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {message}\n")
        except Exception:
            pass


    def get_config() -> dict:
        cfg = mw.addonManager.getConfig(__name__) or {}

        return {
            "query": cfg.get("query", "tag:da_tradurre"),
            "source_field": cfg.get("source_field", "Front"),
            "target_field_google": cfg.get("target_field_google", "Back"),
            "target_field_chatgpt": cfg.get("target_field_chatgpt", "Example"),
            "overwrite": bool(cfg.get("overwrite", False)),

            "google_translate_api_key": cfg.get("google_translate_api_key", ""),
            "google_source_language": cfg.get("google_source_language", "en"),
            "google_target_language": cfg.get("google_target_language", "it"),

            "openai_api_key": cfg.get("openai_api_key", ""),
            "openai_model": cfg.get("openai_model", "gpt-5.5-mini"),
            "openai_instruction": cfg.get(
                "openai_instruction",
                "Traduci in italiano in modo naturale e conciso il testo seguente."
            )
        }


    def require_config_value(cfg: dict, key: str, label: str) -> str:
        value = str(cfg.get(key, "")).strip()

        if not value:
            message = f"Credenziale mancante: {label}. Configurare '{key}' in config.json."
            log_line(message)
            showCritical(message)
            raise RuntimeError(message)

        return value


    def validate_note_fields(note, *field_names: str) -> None:
        available_fields = note.keys()

        for field_name in field_names:
            if field_name not in available_fields:
                message = f"Campo mancante nella nota: {field_name}"
                log_line(message)
                raise KeyError(message)


    def should_write(note, target_field: str, overwrite: bool) -> bool:
        current_value = note[target_field].strip()

        if overwrite:
            return True

        return current_value == ""


    def google_translate_vanilla(
        text: str,
        api_key: str,
        source_language: str,
        target_language: str
    ) -> str:
        endpoint = "https://translation.googleapis.com/language/translate/v2"

        response = requests.post(
            endpoint,
            params={
                "key": api_key
            },
            json={
                "q": text,
                "source": source_language,
                "target": target_language,
                "format": "text"
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        try:
            translated_text = data["data"]["translations"][0]["translatedText"]
        except Exception as e:
            raise RuntimeError(f"Risposta Google Translate non valida: {data}") from e

        return translated_text.strip()


    def chatgpt_translate_vanilla(
        text: str,
        api_key: str,
        model: str,
        instruction: str
    ) -> str:
        endpoint = "https://api.openai.com/v1/responses"

        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": [
                    {
                        "role": "system",
                        "content": instruction
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ]
            },
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        output_text = data.get("output_text")

        if not output_text:
            raise RuntimeError(f"Risposta OpenAI non valida o senza output_text: {data}")

        return output_text.strip()


    def process_with_google_translate() -> dict:
        cfg = get_config()

        api_key = require_config_value(
            cfg,
            "google_translate_api_key",
            "Google Cloud Translation API key"
        )

        query = cfg["query"]
        source_field = cfg["source_field"]
        target_field = cfg["target_field_google"]
        overwrite = cfg["overwrite"]

        source_language = cfg["google_source_language"]
        target_language = cfg["google_target_language"]

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
                    log_line(f"Google nota {note_id}: campo sorgente vuoto.")
                    continue

                if not should_write(note, target_field, overwrite):
                    result["skipped"] += 1
                    log_line(f"Google nota {note_id}: campo destinazione già compilato.")
                    continue

                translated = google_translate_vanilla(
                    text=source_text,
                    api_key=api_key,
                    source_language=source_language,
                    target_language=target_language
                )

                note[target_field] = translated
                note.flush()

                result["updated"] += 1
                log_line(f"Google nota {note_id}: aggiornata.")

            except Exception as e:
                result["errors"] += 1
                log_line(f"Google nota {note_id}: errore: {e}")

        mw.reset()
        return result


    def process_with_chatgpt() -> dict:
        cfg = get_config()

        api_key = require_config_value(
            cfg,
            "openai_api_key",
            "OpenAI API key"
        )

        query = cfg["query"]
        source_field = cfg["source_field"]
        target_field = cfg["target_field_chatgpt"]
        overwrite = cfg["overwrite"]

        model = cfg["openai_model"]
        instruction = cfg["openai_instruction"]

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
                    log_line(f"ChatGPT nota {note_id}: campo sorgente vuoto.")
                    continue

                if not should_write(note, target_field, overwrite):
                    result["skipped"] += 1
                    log_line(f"ChatGPT nota {note_id}: campo destinazione già compilato.")
                    continue

                generated_text = chatgpt_translate_vanilla(
                    text=source_text,
                    api_key=api_key,
                    model=model,
                    instruction=instruction
                )

                note[target_field] = generated_text
                note.flush()

                result["updated"] += 1
                log_line(f"ChatGPT nota {note_id}: aggiornata.")

            except Exception as e:
                result["errors"] += 1
                log_line(f"ChatGPT nota {note_id}: errore: {e}")

        mw.reset()
        return result


    def show_result(title: str, result: dict) -> None:
        showInfo(
            f"{title}\n\n"
            f"Note trovate: {result['found']}\n"
            f"Note aggiornate: {result['updated']}\n"
            f"Note saltate: {result['skipped']}\n"
            f"Errori: {result['errors']}\n\n"
            f"Log: {os.path.join(addon_dir(), LOG_FILE_NAME)}"
        )


    def run_google_translate() -> None:
        try:
            result = process_with_google_translate()
            show_result("Google Translate completato", result)
        except Exception as e:
            log_line(f"Errore generale Google Translate: {e}")


    def run_chatgpt_translate() -> None:
        try:
            result = process_with_chatgpt()
            show_result("ChatGPT completato", result)
        except Exception as e:
            log_line(f"Errore generale ChatGPT: {e}")


    action_google = QAction("Traduci campi con Google Translate", mw)
    action_google.triggered.connect(run_google_translate)
    mw.form.menuTools.addAction(action_google)


    action_chatgpt = QAction("Traduci campi con ChatGPT", mw)
    action_chatgpt.triggered.connect(run_chatgpt_translate)
    mw.form.menuTools.addAction(action_chatgpt)

## Note tecniche importanti

La chiamata Google usa l’endpoint REST:

    https://translation.googleapis.com/language/translate/v2

La chiamata OpenAI usa l’endpoint REST:

    https://api.openai.com/v1/responses

In entrambi i casi:

- si usa `requests.post`;
- si imposta un timeout;
- si controlla l’errore HTTP con `response.raise_for_status()`;
- si valida la struttura della risposta;
- si scrive nel campo Anki solo se la risposta è valida;
- si registra ogni errore nel file log.

## Variante consigliata: non scrivere API key in config.json

Per evitare di salvare chiavi nel file dell’add-on, si possono leggere da variabili d’ambiente.

Esempio:

    import os

    google_key = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

In questo caso `require_config_value()` va sostituita con una funzione che controlla prima la variabile d’ambiente e poi, eventualmente, il config.

Esempio:

    def get_secret(cfg: dict, config_key: str, env_key: str, label: str) -> str:
        value = os.environ.get(env_key, "").strip()

        if not value:
            value = str(cfg.get(config_key, "")).strip()

        if not value:
            message = (
                f"Credenziale mancante: {label}. "
                f"Configurare la variabile d'ambiente {env_key} "
                f"oppure '{config_key}' in config.json."
            )
            log_line(message)
            showCritical(message)
            raise RuntimeError(message)

        return value