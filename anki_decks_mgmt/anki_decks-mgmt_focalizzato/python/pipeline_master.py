#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline_master.py

Scopo
-----
Orchestratore generale della pipeline per la generazione di materiale destinato
alla costruzione di deck Anki.

Questo file non contiene la logica tecnica dei singoli step, ma coordina le
tratte della pipeline, gestisce configurazione, logging, errori e riepiloghi.

Step attualmente configurato
----------------------------
015_video_out
    Input : ./pipe_data/010_video_in
    Output: ./pipe_data/015_video_out

Lo step invoca la funzione:
    process_video_audio_subtitles(...)

contenuta nel modulo:
    pipeline_video_audio_subtitles_extract_v2.py

Uso base
--------
    python pipeline_master.py

Uso con base directory diversa
------------------------------
    python pipeline_master.py --base-dir ./pipe_data

Eseguire solo uno step
----------------------
    python pipeline_master.py --only-step 015_video_out

Sovrascrivere output già esistenti
----------------------------------
    python pipeline_master.py --overwrite

Disabilitare singoli output dello step video
--------------------------------------------
    python pipeline_master.py --no-mp3
    python pipeline_master.py --no-ogg
    python pipeline_master.py --no-frames
    python pipeline_master.py --no-phrase-files

Logging
-------
Console:
    informazioni essenziali su step, file elaborati ed errori.

File:
    log dettagliato generale in:
        ./pipe_data/_logs/pipeline_master.log

    log dettagliato per step in:
        ./pipe_data/_logs/<step_id>.log
"""

from __future__ import annotations

import argparse
import logging
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from pipeline_video_audio_subtitles_extract_v2 import (
    VideoPipelineResult,
    process_video_audio_subtitles,
)


@dataclass(frozen=True)
class PipelineConfig:
    """Configurazione generale della pipeline."""

    base_dir: Path = Path("./pipe_data")
    logs_dir_name: str = "_logs"

    only_step: str | None = None
    skip_steps: tuple[str, ...] = ()
    dry_run: bool = False
    overwrite: bool = False

    recursive_video_search: bool = True
    auto_find_subtitles: bool = True

    write_mp3: bool = True
    write_ogg: bool = True
    write_frames: bool = True
    write_phrase_files: bool = True

    create_step_log_files: bool = True

    @property
    def logs_dir(self) -> Path:
        return self.base_dir / self.logs_dir_name

    def step_input_dir(self, name: str) -> Path:
        return self.base_dir / name

    def step_output_dir(self, name: str) -> Path:
        return self.base_dir / name


@dataclass(frozen=True)
class PipelineStep:
    """Descrizione di uno step della pipeline."""

    step_id: str
    description: str
    input_dir_name: str
    output_dir_name: str
    runner: Callable[[PipelineConfig, logging.Logger], "StepRunResult"]


@dataclass
class StepRunResult:
    """Risultato standard di uno step."""

    step_id: str
    ok: bool
    started_at: datetime
    ended_at: datetime | None = None
    processed_items: int = 0
    errors: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orchestratore generale della pipeline Anki."
    )

    parser.add_argument(
        "--base-dir",
        default="./pipe_data",
        help="Directory base della pipeline. Default: ./pipe_data"
    )

    parser.add_argument(
        "--only-step",
        default=None,
        help="Eseguire solo lo step indicato, per esempio 015_video_out."
    )

    parser.add_argument(
        "--skip-step",
        action="append",
        default=[],
        help="Saltare uno step. Può essere specificato più volte."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrare cosa verrebbe eseguito senza elaborare file."
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sovrascrivere output già esistenti."
    )

    parser.add_argument(
        "--no-recursive-video-search",
        action="store_true",
        help="Non cercare video nelle sottodirectory di 010_video_in."
    )

    parser.add_argument(
        "--no-auto-find-subtitles",
        action="store_true",
        help="Non cercare automaticamente sottotitoli accanto ai video."
    )

    parser.add_argument(
        "--no-mp3",
        action="store_true",
        help="Disabilitare estrazione MP3 nello step video."
    )

    parser.add_argument(
        "--no-ogg",
        action="store_true",
        help="Disabilitare estrazione OGG Vorbis nello step video."
    )

    parser.add_argument(
        "--no-frames",
        action="store_true",
        help="Disabilitare estrazione fotogrammi nello step video."
    )

    parser.add_argument(
        "--no-phrase-files",
        action="store_true",
        help="Disabilitare scrittura file frase nello step video."
    )

    parser.add_argument(
        "--no-step-log-files",
        action="store_true",
        help="Non creare log file separati per ciascuno step."
    )

    return parser.parse_args()


def build_config(args: argparse.Namespace) -> PipelineConfig:
    return PipelineConfig(
        base_dir=Path(args.base_dir).expanduser().resolve(),
        only_step=args.only_step,
        skip_steps=tuple(args.skip_step or []),
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        recursive_video_search=not args.no_recursive_video_search,
        auto_find_subtitles=not args.no_auto_find_subtitles,
        write_mp3=not args.no_mp3,
        write_ogg=not args.no_ogg,
        write_frames=not args.no_frames,
        write_phrase_files=not args.no_phrase_files,
        create_step_log_files=not args.no_step_log_files,
    )


def create_logger(
    name: str,
    log_file: Path | None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(
        logging.Formatter("%(levelname)s: %(message)s")
    )
    logger.addHandler(console_handler)

    if log_file is not None:
        log_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
        )
        logger.addHandler(file_handler)

    return logger


def create_master_logger(config: PipelineConfig) -> logging.Logger:
    return create_logger(
        name="pipeline_master",
        log_file=config.logs_dir / "pipeline_master.log",
    )


def create_step_logger(
    config: PipelineConfig,
    step_id: str
) -> logging.Logger:
    log_file = None

    if config.create_step_log_files:
        log_file = config.logs_dir / f"{step_id}.log"

    return create_logger(
        name=f"pipeline_step.{step_id}",
        log_file=log_file,
    )


def should_run_step(
    step: PipelineStep,
    config: PipelineConfig
) -> bool:
    if config.only_step is not None and step.step_id != config.only_step:
        return False

    if step.step_id in config.skip_steps:
        return False

    return True


def log_pipeline_start(
    config: PipelineConfig,
    logger: logging.Logger
) -> None:
    logger.info("Avvio pipeline.")
    logger.info("Base directory: %s", config.base_dir)
    logger.info("Directory log: %s", config.logs_dir)
    logger.debug("Configurazione completa: %s", config)


def log_pipeline_summary(
    results: list[StepRunResult],
    logger: logging.Logger
) -> None:
    ok_count = sum(1 for result in results if result.ok)
    error_count = len(results) - ok_count

    logger.info("Riepilogo pipeline: step eseguiti=%s ok=%s errori=%s", len(results), ok_count, error_count)

    for result in results:
        duration = result.duration_seconds
        duration_text = f"{duration:.2f}s" if duration is not None else "n/d"

        logger.info(
            "Step %s | ok=%s | elementi=%s | errori=%s | durata=%s",
            result.step_id,
            result.ok,
            result.processed_items,
            len(result.errors),
            duration_text,
        )

        for error in result.errors:
            logger.error("Step %s | %s", result.step_id, error)


def run_015_video_out(
    config: PipelineConfig,
    logger: logging.Logger
) -> StepRunResult:
    step_id = "015_video_out"
    started_at = datetime.now()

    result = StepRunResult(
        step_id=step_id,
        ok=False,
        started_at=started_at,
    )

    input_dir = config.step_input_dir("010_video_in")
    output_dir = config.step_output_dir("015_video_out")

    logger.info("Step %s - input: %s", step_id, input_dir)
    logger.info("Step %s - output: %s", step_id, output_dir)

    if config.dry_run:
        logger.info("Step %s - dry-run attivo: nessun file elaborato.", step_id)
        result.ok = True
        result.ended_at = datetime.now()
        result.details = {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "dry_run": True,
        }
        return result

    try:
        video_results: list[VideoPipelineResult] = process_video_audio_subtitles(
            target=input_dir,
            output_dir=output_dir,
            subtitles=None,
            recursive=config.recursive_video_search,
            overwrite=config.overwrite,
            auto_find_subtitles=config.auto_find_subtitles,
            write_mp3=config.write_mp3,
            write_ogg=config.write_ogg,
            write_frames=config.write_frames,
            write_phrase_files=config.write_phrase_files,
            per_video_subdir=True,
            create_log_file=False,
            logger=logger,
        )

        result.processed_items = len(video_results)

        for video_result in video_results:
            logger.info("Video elaborato: %s", video_result.video_path)
            logger.info("Output video: %s", video_result.output_dir)

            if video_result.errors:
                for error in video_result.errors:
                    message = f"{video_result.video_path}: {error}"
                    result.errors.append(message)
                    logger.error(message)

        result.ok = len(result.errors) == 0
        result.details = {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "videos": [str(item.video_path) for item in video_results],
        }

    except Exception as exc:
        result.errors.append(str(exc))
        logger.error("Errore nello step %s: %s", step_id, exc)
        logger.debug("Traceback:\n%s", traceback.format_exc())

    result.ended_at = datetime.now()
    return result


def build_steps() -> list[PipelineStep]:
    return [
        PipelineStep(
            step_id="015_video_out",
            description="Estrazione audio, fotogrammi e frasi da video/sottotitoli.",
            input_dir_name="010_video_in",
            output_dir_name="015_video_out",
            runner=run_015_video_out,
        ),
    ]


def run_pipeline(config: PipelineConfig) -> list[StepRunResult]:
    master_logger = create_master_logger(config)
    log_pipeline_start(config, master_logger)

    steps = build_steps()
    results: list[StepRunResult] = []

    selected_steps = [
        step for step in steps
        if should_run_step(step, config)
    ]

    if not selected_steps:
        master_logger.warning("Nessuno step selezionato.")
        return results

    for step in selected_steps:
        step_logger = create_step_logger(
            config=config,
            step_id=step.step_id
        )

        master_logger.info("Avvio step: %s - %s", step.step_id, step.description)
        step_logger.info("Avvio step: %s - %s", step.step_id, step.description)

        result = step.runner(config, step_logger)
        results.append(result)

        if result.ok:
            master_logger.info("Step completato: %s", step.step_id)
        else:
            master_logger.error("Step completato con errori: %s", step.step_id)
            for error in result.errors:
                master_logger.error("%s | %s", step.step_id, error)

    log_pipeline_summary(results, master_logger)

    return results


def main() -> int:
    args = parse_args()
    config = build_config(args)

    results = run_pipeline(config)

    if not results:
        return 1

    has_errors = any(
        not result.ok
        for result in results
    )

    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
