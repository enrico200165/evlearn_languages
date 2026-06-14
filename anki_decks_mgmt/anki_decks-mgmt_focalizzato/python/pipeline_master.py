#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline_master.py

Orchestratore generale della pipeline Anki.

Il master coordina gli step, ma non contiene la logica tecnica dei singoli step.
Gli step sono implementati in moduli separati:

    step_015_video.py
    step_020_audio.py

Regola architetturale
---------------------
Le directory principali della pipeline sono definite come pseudo-costanti nella
sezione PIPELINE DIRECTORY CONSTANTS. Le funzioni non devono contenere stringhe
hard-coded per le directory della pipeline.
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

from step_015_video import process_video_audio_subtitles
from step_020_audio import transcribe_audio_to_subtitles


# =============================================================================
# PIPELINE DIRECTORY CONSTANTS
# =============================================================================

PIPE_BASE_DIR = "./pipe_data"
PIPE_LOGS_DIR = "_logs"

PIPE_DIR_VIDEO_IN = "010_video_in"
PIPE_DIR_VIDEO_OUT = "020_video_out"
PIPE_DIR_VIDEO_AUDIO = f"{PIPE_DIR_VIDEO_OUT}/audio"

PIPE_DIR_AUDIO_OUT = "030_audio_out"


# =============================================================================
# STEP CONSTANTS
# =============================================================================

STEP_ID_VIDEO = "015_video"
STEP_ID_AUDIO = "020_audio"

STEP_DESCRIPTION_VIDEO = "Estrazione audio, sottotitoli, fotogrammi e frasi da video."
STEP_DESCRIPTION_AUDIO = "Generazione sottotitoli e piccoli audio frase da file audio."


@dataclass(frozen=True)
class PipelineConfig:
    """Configurazione generale della pipeline."""

    base_dir: Path = Path(PIPE_BASE_DIR)
    logs_dir_name: str = PIPE_LOGS_DIR

    only_step: str | None = None
    skip_steps: tuple[str, ...] = ()
    dry_run: bool = False
    overwrite: bool = False

    video_input_dir_name: str = PIPE_DIR_VIDEO_IN
    video_output_dir_name: str = PIPE_DIR_VIDEO_OUT

    audio_input_dir_name: str = PIPE_DIR_VIDEO_AUDIO
    audio_output_dir_name: str = PIPE_DIR_AUDIO_OUT

    recursive_video_search: bool = False
    auto_find_video_subtitles: bool = True

    write_video_mp3: bool = True
    write_video_ogg: bool = True
    write_video_frames: bool = True
    write_video_phrase_files: bool = True
    copy_video_subtitles: bool = True

    audio_language: str | None = None
    audio_model_size: str = "small"
    audio_device: str = "auto"
    audio_compute_type: str = "auto"

    write_audio_srt: bool = True
    write_audio_vtt: bool = True
    write_audio_txt: bool = True
    write_audio_json: bool = True
    write_phrase_audio: bool = True

    phrase_audio_format: str = "mp3"
    phrase_audio_bitrate: str = "64k"
    phrase_audio_padding_ms: int = 120

    @property
    def logs_dir(self) -> Path:
        return self.base_dir / self.logs_dir_name

    def path_in_base(self, dir_name: str) -> Path:
        return self.base_dir / Path(dir_name)


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
        default=PIPE_BASE_DIR,
        help=f"Directory base della pipeline. Default: {PIPE_BASE_DIR}"
    )

    parser.add_argument(
        "--only-step",
        default=None,
        help=f"Eseguire solo lo step indicato, per esempio {STEP_ID_VIDEO} oppure {STEP_ID_AUDIO}."
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
        "--video-input-dir",
        default=PIPE_DIR_VIDEO_IN,
        help=f"Directory input dello step video, relativa a base-dir. Default: {PIPE_DIR_VIDEO_IN}"
    )

    parser.add_argument(
        "--video-output-dir",
        default=PIPE_DIR_VIDEO_OUT,
        help=f"Directory output dello step video, relativa a base-dir. Default: {PIPE_DIR_VIDEO_OUT}"
    )

    parser.add_argument(
        "--audio-input-dir",
        default=PIPE_DIR_VIDEO_AUDIO,
        help=f"Directory input dello step audio, relativa a base-dir. Default: {PIPE_DIR_VIDEO_AUDIO}"
    )

    parser.add_argument(
        "--audio-output-dir",
        default=PIPE_DIR_AUDIO_OUT,
        help=f"Directory output dello step audio, relativa a base-dir. Default: {PIPE_DIR_AUDIO_OUT}"
    )

    parser.add_argument(
        "--recursive-video-search",
        action="store_true",
        help="Cercare video anche nelle sottodirectory dello step video. Default: disattivato."
    )

    parser.add_argument(
        "--no-auto-find-video-subtitles",
        action="store_true",
        help="Non cercare automaticamente sottotitoli accanto ai video."
    )

    parser.add_argument(
        "--no-video-mp3",
        action="store_true",
        help="Non estrarre audio MP3 nello step video."
    )

    parser.add_argument(
        "--no-video-ogg",
        action="store_true",
        help="Non estrarre audio OGG Vorbis nello step video."
    )

    parser.add_argument(
        "--no-video-frames",
        action="store_true",
        help="Non estrarre fotogrammi nello step video."
    )

    parser.add_argument(
        "--no-video-phrase-files",
        action="store_true",
        help="Non scrivere file frase nello step video."
    )

    parser.add_argument(
        "--no-copy-video-subtitles",
        action="store_true",
        help="Non copiare i sottotitoli trovati nello step video."
    )

    parser.add_argument(
        "--audio-language",
        default=None,
        help="Codice lingua per lo step audio, per esempio en, de, ja, it."
    )

    parser.add_argument(
        "--audio-model-size",
        default="small",
        help="Modello faster-whisper per lo step audio. Default: small."
    )

    parser.add_argument(
        "--audio-device",
        default="auto",
        help="Dispositivo faster-whisper: auto, cpu, cuda. Default: auto."
    )

    parser.add_argument(
        "--audio-compute-type",
        default="auto",
        help="Compute type faster-whisper: auto, int8, float16, float32. Default: auto."
    )

    parser.add_argument(
        "--no-audio-srt",
        action="store_true",
        help="Non generare SRT nello step audio."
    )

    parser.add_argument(
        "--no-audio-vtt",
        action="store_true",
        help="Non generare VTT nello step audio."
    )

    parser.add_argument(
        "--no-audio-txt",
        action="store_true",
        help="Non generare TXT nello step audio."
    )

    parser.add_argument(
        "--no-audio-json",
        action="store_true",
        help="Non generare JSON nello step audio."
    )

    parser.add_argument(
        "--no-phrase-audio",
        action="store_true",
        help="Non generare piccoli file audio frase nello step audio."
    )

    parser.add_argument(
        "--phrase-audio-format",
        default="mp3",
        choices=["mp3", "ogg", "wav", "opus"],
        help="Formato dei piccoli file audio frase. Default: mp3."
    )

    parser.add_argument(
        "--phrase-audio-bitrate",
        default="64k",
        help="Bitrate dei piccoli file audio frase. Default: 64k."
    )

    parser.add_argument(
        "--phrase-audio-padding-ms",
        type=int,
        default=120,
        help="Padding in millisecondi per piccoli file audio frase. Default: 120."
    )

    return parser.parse_args()


def build_config(args: argparse.Namespace) -> PipelineConfig:
    return PipelineConfig(
        base_dir=Path(args.base_dir).expanduser().resolve(),
        only_step=args.only_step,
        skip_steps=tuple(args.skip_step or []),
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        video_input_dir_name=args.video_input_dir,
        video_output_dir_name=args.video_output_dir,
        audio_input_dir_name=args.audio_input_dir,
        audio_output_dir_name=args.audio_output_dir,
        recursive_video_search=args.recursive_video_search,
        auto_find_video_subtitles=not args.no_auto_find_video_subtitles,
        write_video_mp3=not args.no_video_mp3,
        write_video_ogg=not args.no_video_ogg,
        write_video_frames=not args.no_video_frames,
        write_video_phrase_files=not args.no_video_phrase_files,
        copy_video_subtitles=not args.no_copy_video_subtitles,
        audio_language=args.audio_language,
        audio_model_size=args.audio_model_size,
        audio_device=args.audio_device,
        audio_compute_type=args.audio_compute_type,
        write_audio_srt=not args.no_audio_srt,
        write_audio_vtt=not args.no_audio_vtt,
        write_audio_txt=not args.no_audio_txt,
        write_audio_json=not args.no_audio_json,
        write_phrase_audio=not args.no_phrase_audio,
        phrase_audio_format=args.phrase_audio_format,
        phrase_audio_bitrate=args.phrase_audio_bitrate,
        phrase_audio_padding_ms=args.phrase_audio_padding_ms,
    )


def create_master_logger(config: PipelineConfig) -> logging.Logger:
    config.logs_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    logger = logging.getLogger("pipeline_master")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(levelname)s: %(message)s")
    )
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        config.logs_dir / "pipeline_master.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )
    logger.addHandler(file_handler)

    return logger


def should_run_step(step: PipelineStep, config: PipelineConfig) -> bool:
    if config.only_step is not None and step.step_id != config.only_step:
        return False

    if step.step_id in config.skip_steps:
        return False

    return True


def create_empty_result(step_id: str) -> StepRunResult:
    return StepRunResult(
        step_id=step_id,
        ok=False,
        started_at=datetime.now()
    )


def finalize_result(result: StepRunResult) -> StepRunResult:
    result.ended_at = datetime.now()
    return result


def run_015_video(config: PipelineConfig, logger: logging.Logger) -> StepRunResult:
    step_id = STEP_ID_VIDEO
    result = create_empty_result(step_id)

    input_dir = config.path_in_base(config.video_input_dir_name)
    output_dir = config.path_in_base(config.video_output_dir_name)

    logger.info("Step %s - input: %s", step_id, input_dir)
    logger.info("Step %s - output: %s", step_id, output_dir)

    if config.dry_run:
        result.ok = True
        result.details = {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "dry_run": True,
        }
        return finalize_result(result)

    try:
        video_results = process_video_audio_subtitles(
            target=input_dir,
            output_dir=output_dir,
            subtitles=None,
            recursive=config.recursive_video_search,
            overwrite=config.overwrite,
            auto_find_subtitles=config.auto_find_video_subtitles,
            write_mp3=config.write_video_mp3,
            write_ogg=config.write_video_ogg,
            write_frames=config.write_video_frames,
            write_phrase_files=config.write_video_phrase_files,
            copy_subtitles=config.copy_video_subtitles,
            per_video_subdir=False,
            logger=None,
        )

        result.processed_items = len(video_results)
        result.details = {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "videos": [str(item.video_path) for item in video_results],
        }

        for video_result in video_results:
            logger.info("Video elaborato: %s", video_result.video_path)
            if video_result.errors:
                for error in video_result.errors:
                    result.errors.append(f"{video_result.video_path}: {error}")

        result.ok = len(result.errors) == 0

    except Exception as exc:
        result.errors.append(str(exc))
        logger.error("Errore nello step %s: %s", step_id, exc)
        logger.debug("Traceback:\n%s", traceback.format_exc())

    return finalize_result(result)


def run_020_audio(config: PipelineConfig, logger: logging.Logger) -> StepRunResult:
    step_id = STEP_ID_AUDIO
    result = create_empty_result(step_id)

    input_dir = config.path_in_base(config.audio_input_dir_name)
    output_dir = config.path_in_base(config.audio_output_dir_name)

    logger.info("Step %s - input: %s", step_id, input_dir)
    logger.info("Step %s - output: %s", step_id, output_dir)

    if config.dry_run:
        result.ok = True
        result.details = {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "dry_run": True,
        }
        return finalize_result(result)

    try:
        audio_results = transcribe_audio_to_subtitles(
            target=input_dir,
            output_dir=output_dir,
            language=config.audio_language,
            model_size=config.audio_model_size,
            device=config.audio_device,
            compute_type=config.audio_compute_type,
            recursive=True,
            overwrite=config.overwrite,
            per_audio_subdir=True,
            write_srt=config.write_audio_srt,
            write_vtt=config.write_audio_vtt,
            write_txt=config.write_audio_txt,
            write_json=config.write_audio_json,
            write_phrase_audio=config.write_phrase_audio,
            phrase_audio_format=config.phrase_audio_format,
            phrase_audio_bitrate=config.phrase_audio_bitrate,
            phrase_audio_padding_ms=config.phrase_audio_padding_ms,
            logger=None,
        )

        result.processed_items = len(audio_results)
        result.details = {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "audio_files": [str(item.audio_path) for item in audio_results],
        }

        for audio_result in audio_results:
            logger.info("Audio elaborato: %s", audio_result.audio_path)
            if audio_result.errors:
                for error in audio_result.errors:
                    result.errors.append(f"{audio_result.audio_path}: {error}")

        result.ok = len(result.errors) == 0

    except Exception as exc:
        result.errors.append(str(exc))
        logger.error("Errore nello step %s: %s", step_id, exc)
        logger.debug("Traceback:\n%s", traceback.format_exc())

    return finalize_result(result)


def build_steps() -> list[PipelineStep]:
    return [
        PipelineStep(
            step_id=STEP_ID_VIDEO,
            description=STEP_DESCRIPTION_VIDEO,
            input_dir_name=PIPE_DIR_VIDEO_IN,
            output_dir_name=PIPE_DIR_VIDEO_OUT,
            runner=run_015_video,
        ),
        PipelineStep(
            step_id=STEP_ID_AUDIO,
            description=STEP_DESCRIPTION_AUDIO,
            input_dir_name=PIPE_DIR_VIDEO_AUDIO,
            output_dir_name=PIPE_DIR_AUDIO_OUT,
            runner=run_020_audio,
        ),
    ]


def log_pipeline_summary(results: list[StepRunResult], logger: logging.Logger) -> None:
    ok_count = sum(1 for item in results if item.ok)
    error_count = len(results) - ok_count

    logger.info("Riepilogo pipeline: step=%s ok=%s errori=%s", len(results), ok_count, error_count)

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


def run_pipeline(config: PipelineConfig) -> list[StepRunResult]:
    logger = create_master_logger(config)

    logger.info("Avvio pipeline.")
    logger.info("Base directory: %s", config.base_dir)
    logger.info("Log master: %s", config.logs_dir / "pipeline_master.log")
    logger.debug("Configurazione completa: %s", config)

    steps = [step for step in build_steps() if should_run_step(step, config)]

    if not steps:
        logger.warning("Nessuno step selezionato.")
        return []

    results: list[StepRunResult] = []

    for step in steps:
        logger.info("Avvio step: %s - %s", step.step_id, step.description)
        result = step.runner(config, logger)
        results.append(result)

        if result.ok:
            logger.info("Step completato: %s", step.step_id)
        else:
            logger.error("Step completato con errori: %s", step.step_id)

    log_pipeline_summary(results, logger)

    return results


def main() -> int:
    args = parse_args()
    config = build_config(args)
    results = run_pipeline(config)

    if not results:
        return 1

    has_errors = any(not result.ok for result in results)

    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
