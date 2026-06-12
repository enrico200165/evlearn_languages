from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nlp_deck_manager.core import (
    build_ranked_rows,
    write_core_exports,
    write_core_overlap_report,
    write_full_frequencies,
    write_reference_import_report,
)
from nlp_deck_manager.deck_management import (
    load_intentional_duplicates_csv,
    register_rows_as_deck_notes,
    write_deck_build_report,
)
from nlp_deck_manager.exporters import export_notes_to_anki_csv, export_notes_to_apkg
from nlp_deck_manager.logging_utils import setup_logging
from nlp_deck_manager.models import ProcessingContext
from nlp_deck_manager.nlp import AnalyzerConfig, LemmaAnalyzer
from nlp_deck_manager.processors import (
    CachedLemmaInfoProcessor,
    GermanFiveExamplesPlaceholderProcessor,
    GermanVanillaMorphologyProcessor,
    JapaneseVanillaFieldsProcessor,
    ProcessorPipeline,
    TranslationPlaceholderProcessor,
    load_processor_from_file,
)
from nlp_deck_manager.readers import iter_text_units_from_path
from nlp_deck_manager.reference_db import ReferenceDb


def input_root_name(path: Path) -> str:
    name = path.name
    if name.lower().endswith(".tar.gz"):
        return name[:-7]
    return path.stem or path.name


def default_output_dir_for_input(input_path: Path) -> Path:
    if input_path.is_dir():
        return input_path.resolve() / "out_directory_input"
    return input_path.resolve().parent / f"out_{input_root_name(input_path)}"


def default_reference_db_path(language: str) -> Path:
    return Path.cwd() / "vocab_reference_dbs" / f"vocab_reference_{language}.sqlite"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="nlp-deck-manager",
        description="Gestore deck linguistici con Reference DB, pipeline NLP, processor custom ed export.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_build_core(sub)
    add_build_context(sub)
    add_process_deck(sub)
    add_export_deck(sub)
    add_list_decks(sub)
    add_lemma_info_set(sub)
    add_lemma_info_get(sub)

    return parser.parse_args(argv)


def add_common_input_args(p):
    p.add_argument("--input", required=True, help="File o directory di input.")
    p.add_argument("--language", required=True, help="Codice lingua, per esempio de o ja.")
    p.add_argument("--model", default=None, help="Modello spaCy opzionale.")
    p.add_argument("--analyzer", choices=["auto", "spacy", "simple"], default="auto")
    p.add_argument("--output-dir", default=None)
    p.add_argument("--reference-db", default=None)
    p.add_argument("--max-rank", type=int, default=5000)
    p.add_argument("--band-size", type=int, default=1000)
    p.add_argument("--limit-units", type=int, default=None)
    p.add_argument("--write-normalized-text", action="store_true")


def add_build_core(sub):
    p = sub.add_parser("build-core", help="Creare ranking Core, aggiornare Reference DB e generare deck Core.")
    add_common_input_args(p)
    p.add_argument("--deck-name-prefix", default=None, help="Default: '<LANG> Core'.")
    p.add_argument("--no-create-notes", action="store_true", help="Non creare notes nel DB e non esportare CSV deck.")
    p.add_argument("--run-default-processors", action="store_true", help="Applicare processor vanilla prima dell'export.")
    p.add_argument("--export-apkg", action="store_true", help="Generare anche APKG se genanki è installato.")


def add_build_context(sub):
    p = sub.add_parser("build-context", help="Creare deck contestuale evitando duplicati Core non intenzionali.")
    add_common_input_args(p)
    p.add_argument("--deck-name", required=True)
    p.add_argument("--deck-description", default=None)
    p.add_argument("--intentional-duplicates-csv", default=None, help="CSV con lemma/normalized_lemma e deck_description.")
    p.add_argument("--allow-all-core-duplicates", action="store_true", help="Permette duplicati Core documentandoli automaticamente.")
    p.add_argument("--run-default-processors", action="store_true")
    p.add_argument("--export-apkg", action="store_true")


def add_process_deck(sub):
    p = sub.add_parser("process-deck", help="Applicare processor vanilla o custom a notes già presenti nel DB.")
    p.add_argument("--language", required=True)
    p.add_argument("--deck-name", required=True)
    p.add_argument("--reference-db", default=None)
    p.add_argument("--output-dir", default="out_process_deck")
    p.add_argument("--default-processors", action="store_true")
    p.add_argument("--custom-processor", action="append", default=[], help="Path file .py con classe CustomProcessor.")
    p.add_argument("--export-csv", action="store_true")
    p.add_argument("--export-apkg", action="store_true")


def add_export_deck(sub):
    p = sub.add_parser("export-deck", help="Esportare un deck locale in CSV Anki e opzionalmente APKG.")
    p.add_argument("--language", required=True)
    p.add_argument("--deck-name", required=True)
    p.add_argument("--reference-db", default=None)
    p.add_argument("--output-dir", default="out_export_deck")
    p.add_argument("--export-apkg", action="store_true")


def add_list_decks(sub):
    p = sub.add_parser("list-decks", help="Elencare deck nel Reference DB.")
    p.add_argument("--language", default=None)
    p.add_argument("--reference-db", required=True)


def add_lemma_info_set(sub):
    p = sub.add_parser("lemma-info-set", help="Salvare una informazione cache per un lemma.")
    p.add_argument("--language", required=True)
    p.add_argument("--lemma", required=True, help="Lemma visuale, per esempio Haus o arbeiten.")
    p.add_argument("--normalized-lemma", default=None, help="Forma normalizzata; default: lemma lower().")
    p.add_argument("--info-name", required=True, help="Esempio: flessione, coniugazione, frasi esempio.")
    p.add_argument("--info", default=None, help="Contenuto informazione. Alternativa a --info-file.")
    p.add_argument("--info-file", default=None, help="File UTF-8 contenente l'informazione.")
    p.add_argument("--origin", required=True, help="Esempio: API Duden, Wiktionary, OpenAI, revisione manuale.")
    p.add_argument("--reference-db", default=None)


def add_lemma_info_get(sub):
    p = sub.add_parser("lemma-info-get", help="Leggere informazioni cache memorizzate per un lemma.")
    p.add_argument("--language", required=True)
    p.add_argument("--lemma", required=True, help="Lemma o normalized lemma da cercare.")
    p.add_argument("--normalized-lemma", default=None)
    p.add_argument("--info-name", default=None, help="Se indicato restituisce solo questa informazione.")
    p.add_argument("--origin", default=None, help="Origine opzionale da filtrare.")
    p.add_argument("--reference-db", default=None)


def materialize_text_units(input_path: Path, output_dir: Path, write_normalized_text: bool, logger):
    units = list(iter_text_units_from_path(input_path))
    logger.info("Unità testuali lette: %s", len(units))
    if write_normalized_text:
        out = output_dir / "normalized_text_units.txt"
        with out.open("w", encoding="utf-8", newline="") as f:
            for unit in units:
                f.write(unit.text + "\n")
        logger.info("Testo normalizzato scritto: %s", out)
    return units


def analyze_input(args, logger):
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input non trovato: {input_path}")
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir_for_input(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    text_units = materialize_text_units(input_path, output_dir, args.write_normalized_text, logger)
    analyzer = LemmaAnalyzer(
        AnalyzerConfig(
            language=args.language.lower().strip(),
            model_name=args.model,
            limit_units=args.limit_units,
            mode=args.analyzer,
        )
    )
    occurrences = analyzer.count_lemmas(text_units, logger=logger)
    if not occurrences:
        raise RuntimeError("Nessun lemma trovato.")
    return output_dir, occurrences


def handle_build_core(args) -> int:
    input_path = Path(args.input)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir_for_input(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(output_dir)
    try:
        language = args.language.lower().strip()
        reference_db_path = Path(args.reference_db) if args.reference_db else default_reference_db_path(language)
        logger.info("Input: %s", input_path.resolve())
        logger.info("Lingua: %s", language)
        logger.info("Reference DB: %s", reference_db_path.resolve())

        output_dir, occurrences = analyze_input(args, logger)
        write_full_frequencies(output_dir / f"lemma_frequencies_full_{language}.csv", occurrences)

        with ReferenceDb(reference_db_path) as db:
            import_results = db.import_lemma_occurrences(occurrences)
            write_reference_import_report(output_dir / f"reference_db_import_report_{language}.csv", import_results)

            rows = build_ranked_rows(occurrences, language=language, max_rank=args.max_rank, band_size=args.band_size)
            write_core_exports(output_dir, rows, language=language, max_rank=args.max_rank, band_size=args.band_size)
            write_core_overlap_report(output_dir / f"core_overlap_report_{language}.csv", rows)

            if not args.no_create_notes:
                all_report_rows = []
                band_count = (args.max_rank + args.band_size - 1) // args.band_size
                prefix = args.deck_name_prefix or f"{language.upper()} Core"
                for band_number in range(1, band_count + 1):
                    start = ((band_number - 1) * args.band_size) + 1
                    end = band_number * args.band_size
                    band_rows = [row for row in rows if start <= row.rank <= end]
                    if not band_rows:
                        continue
                    deck_name = f"{prefix} {end}"
                    result = register_rows_as_deck_notes(
                        db=db,
                        rows=band_rows,
                        language=language,
                        deck_name=deck_name,
                        deck_kind="core",
                        deck_description=f"Deck Core {start}-{end} senza overlap con le bande precedenti.",
                        relation_description_template="Presente in {deck_name}; rank {rank}; frequenza {frequency}",
                    )
                    logger.info("Deck %s: note create/aggiornate %s", deck_name, result.created_notes)
                    all_report_rows.extend(result.report_rows)
                    if args.run_default_processors:
                        process_deck_notes(db, language, deck_name, output_dir, logger, use_default=True, custom_processor_paths=[])
                    notes = db.load_notes_for_deck(language=language, deck_name=deck_name)
                    export_notes_to_anki_csv(output_dir / f"{safe_filename(deck_name)}_anki.csv", notes)
                    if args.export_apkg:
                        export_notes_to_apkg(output_dir / f"{safe_filename(deck_name)}.apkg", deck_name, notes)
                write_deck_build_report(output_dir / f"deck_build_report_{language}.csv", all_report_rows)

        logger.info("Elaborazione completata")
        return 0
    except Exception:
        logger.exception("Errore durante build-core")
        return 1


def handle_build_context(args) -> int:
    input_path = Path(args.input)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir_for_input(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(output_dir)
    try:
        language = args.language.lower().strip()
        reference_db_path = Path(args.reference_db) if args.reference_db else default_reference_db_path(language)
        output_dir, occurrences = analyze_input(args, logger)
        write_full_frequencies(output_dir / f"lemma_frequencies_full_{language}.csv", occurrences)
        rows = build_ranked_rows(occurrences, language=language, max_rank=args.max_rank, band_size=args.band_size)
        with ReferenceDb(reference_db_path) as db:
            import_results = db.import_lemma_occurrences(occurrences)
            write_reference_import_report(output_dir / f"reference_db_import_report_{language}.csv", import_results)
            intentional = load_intentional_duplicates_csv(
                Path(args.intentional_duplicates_csv) if args.intentional_duplicates_csv else None
            )
            if args.allow_all_core_duplicates:
                for row in rows:
                    intentional.setdefault(
                        row.normalized_lemma,
                        f"Duplicazione intenzionale nel deck contestuale {args.deck_name}"[:255],
                    )
            result = register_rows_as_deck_notes(
                db=db,
                rows=rows,
                language=language,
                deck_name=args.deck_name,
                deck_kind="context",
                deck_description=args.deck_description,
                relation_description_template="Presente nel deck contestuale {deck_name}; rank locale {rank}; frequenza {frequency}",
                skip_core_duplicates=True,
                intentional_duplicates=intentional,
            )
            write_deck_build_report(output_dir / f"deck_build_report_{language}.csv", result.report_rows)
            if args.run_default_processors:
                process_deck_notes(db, language, args.deck_name, output_dir, logger, use_default=True, custom_processor_paths=[])
            notes = db.load_notes_for_deck(language=language, deck_name=args.deck_name)
            export_notes_to_anki_csv(output_dir / f"{safe_filename(args.deck_name)}_anki.csv", notes)
            if args.export_apkg:
                export_notes_to_apkg(output_dir / f"{safe_filename(args.deck_name)}.apkg", args.deck_name, notes)
        logger.info("Deck contestuale completato: %s", args.deck_name)
        return 0
    except Exception:
        logger.exception("Errore durante build-context")
        return 1


def default_processors_for_language(language: str):
    processors = [CachedLemmaInfoProcessor(), TranslationPlaceholderProcessor()]
    if language == "de":
        processors.insert(0, GermanVanillaMorphologyProcessor())
        processors.append(GermanFiveExamplesPlaceholderProcessor())
    elif language == "ja":
        processors.insert(0, JapaneseVanillaFieldsProcessor())
    return processors


def process_deck_notes(db, language, deck_name, output_dir, logger, *, use_default: bool, custom_processor_paths: list[str]):
    processors = []
    if use_default:
        processors.extend(default_processors_for_language(language))
    for custom_path in custom_processor_paths:
        processors.append(load_processor_from_file(Path(custom_path)))
    if not processors:
        logger.info("Nessun processor richiesto")
        return
    pipeline = ProcessorPipeline(processors)
    notes = db.load_notes_for_deck(language=language, deck_name=deck_name)
    context = ProcessingContext(language=language, deck_name=deck_name, reference_db=db, logger=logger)
    for note in notes:
        results = pipeline.process_note(note, context)
        note_id = db.save_note(note)
        for processor_name, result in results:
            db.record_processing_result(note_id=note_id, processor_name=processor_name, result=result)
    db.conn.commit()
    export_notes_to_anki_csv(output_dir / f"{safe_filename(deck_name)}_processed_anki.csv", db.load_notes_for_deck(language=language, deck_name=deck_name))
    logger.info("Processor applicati a %s note", len(notes))


def handle_process_deck(args) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(output_dir)
    try:
        language = args.language.lower().strip()
        reference_db_path = Path(args.reference_db) if args.reference_db else default_reference_db_path(language)
        with ReferenceDb(reference_db_path) as db:
            process_deck_notes(
                db,
                language,
                args.deck_name,
                output_dir,
                logger,
                use_default=args.default_processors,
                custom_processor_paths=args.custom_processor,
            )
            notes = db.load_notes_for_deck(language=language, deck_name=args.deck_name)
            if args.export_csv:
                export_notes_to_anki_csv(output_dir / f"{safe_filename(args.deck_name)}_anki.csv", notes)
            if args.export_apkg:
                export_notes_to_apkg(output_dir / f"{safe_filename(args.deck_name)}.apkg", args.deck_name, notes)
        return 0
    except Exception:
        logger.exception("Errore durante process-deck")
        return 1


def handle_export_deck(args) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(output_dir)
    try:
        language = args.language.lower().strip()
        reference_db_path = Path(args.reference_db) if args.reference_db else default_reference_db_path(language)
        with ReferenceDb(reference_db_path) as db:
            notes = db.load_notes_for_deck(language=language, deck_name=args.deck_name)
            if not notes:
                raise RuntimeError("Nessuna note trovata per il deck richiesto")
            export_notes_to_anki_csv(output_dir / f"{safe_filename(args.deck_name)}_anki.csv", notes)
            if args.export_apkg:
                export_notes_to_apkg(output_dir / f"{safe_filename(args.deck_name)}.apkg", args.deck_name, notes)
        logger.info("Export completato: %s note", len(notes))
        return 0
    except Exception:
        logger.exception("Errore durante export-deck")
        return 1


def handle_list_decks(args) -> int:
    with ReferenceDb(Path(args.reference_db)) as db:
        for row in db.list_decks(language=args.language):
            print(f"{row['language']}\t{row['deck_name']}\t{row['deck_kind'] or ''}\t{row['description'] or ''}")
    return 0


def handle_lemma_info_set(args) -> int:
    language = args.language.lower().strip()
    reference_db_path = Path(args.reference_db) if args.reference_db else default_reference_db_path(language)
    if args.info_file:
        informazione = Path(args.info_file).read_text(encoding="utf-8")
    elif args.info is not None:
        informazione = args.info
    else:
        print("ERRORE: indicare --info oppure --info-file", file=sys.stderr)
        return 2
    with ReferenceDb(reference_db_path) as db:
        info = db.upsert_lemma_info_by_lemma(
            language=language,
            lemma=args.lemma,
            normalized_lemma=args.normalized_lemma,
            nome_informazione=args.info_name,
            informazione=informazione,
            origine=args.origin,
            create_if_missing=True,
        )
    print(f"OK\t{language}\t{args.lemma}\t{info.nome_informazione}\t{info.origine}\t{info.tstamp}")
    return 0


def handle_lemma_info_get(args) -> int:
    language = args.language.lower().strip()
    normalized = (args.normalized_lemma or args.lemma).strip().lower()
    reference_db_path = Path(args.reference_db) if args.reference_db else default_reference_db_path(language)
    with ReferenceDb(reference_db_path) as db:
        if args.info_name:
            info = db.get_lemma_info_by_lemma(
                language=language,
                normalized_lemma=normalized,
                nome_informazione=args.info_name,
                origine=args.origin,
            )
            infos = [info] if info is not None else []
        else:
            infos = db.list_lemma_info_by_lemma(language=language, normalized_lemma=normalized)
    if not infos:
        print("NESSUNA_INFO")
        return 0
    for info in infos:
        print(f"nome_informazione: {info.nome_informazione}")
        print(f"origine: {info.origine}")
        print(f"tstamp: {info.tstamp}")
        print("informazione:")
        print(info.informazione)
        print("---")
    return 0


def safe_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name).strip("_") or "deck"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "build-core":
        return handle_build_core(args)
    if args.command == "build-context":
        return handle_build_context(args)
    if args.command == "process-deck":
        return handle_process_deck(args)
    if args.command == "export-deck":
        return handle_export_deck(args)
    if args.command == "list-decks":
        return handle_list_decks(args)
    if args.command == "lemma-info-set":
        return handle_lemma_info_set(args)
    if args.command == "lemma-info-get":
        return handle_lemma_info_get(args)
    raise RuntimeError(f"Comando non gestito: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
