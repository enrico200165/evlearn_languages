#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline_audio_to_subtitles.py

Scopo
-----
Tratta della pipeline per generare sottotitoli a partire da file audio.

Lo script può essere usato in due modi:

1. Come modulo importato da uno script master.
2. Come script autonomo da riga di comando.

La trascrizione è locale e usa faster-whisper.

Installazione requisiti
-----------------------
    python -m pip install faster-whisper

Uso autonomo base
-----------------
    python pipeline_audio_to_subtitles.py audio.mp3 --output-dir out_subtitles

Uso con lingua esplicita
------------------------
    python pipeline_audio_to_subtitles.py audio.mp3 --output-dir out_subtitles --language ja

Uso su directory
----------------
    python pipeline_audio_to_subtitles.py ./audio_in --output-dir ./subtitles_out --recursive

Funzione principale per script master
-------------------------------------
    transcribe_audio_to_subtitles(
        target="./pipe_data/012_audio_in",
        output_dir="./pipe_data/014_subtitles_out",
        language="ja",
        model_size="small",
        write_srt=True,
        write_vtt=True,
        write_txt=True,
    )

Convenzione nomi output
-----------------------
Se language è specificato:
    mymovie_ja.srt
    mymovie_ja.vtt
    mymovie_ja.txt
    phrase_audio/phrase_<timestamp>_<prime_parole>.mp3

Se language non è specificato:
    mymovie.srt
    mymovie.vtt
    mymovie.txt

Questa convenzione è coerente con lo step video che riconosce:
    <nome_video>.srt
    <nome_video>_<codice_lingua>.srt

Requisiti esterni
-----------------
- Python 3.10+
- faster-whisper
- ffmpeg installato nel sistema, normalmente necessario per la decodifica audio
  usata dalle librerie di trascrizione.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable


AUDIO_EXTENSIONS = {
    ".mp3",
    ".ogg",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".wma",
    ".opus",
}


@dataclass(frozen=True)
class TranscriptSegment:
    """Segmento temporizzato prodotto dal riconoscimento del parlato."""

    index: int
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class AudioTranscriptionResult:
    """Risultato della trascrizione di un singolo file audio."""

    audio_path: Path
    output_dir: Path
    language: str | None = None
    detected_language: str | None = None
    srt_path: Path | None = None
    vtt_path: Path | None = None
    txt_path: Path | None = None
    json_path: Path | None = None
    phrase_audio_paths: list[Path] = field(default_factory=list)
    segments_count: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AudioToSubtitlesOptions:
    """Opzioni complete per la generazione sottotitoli da audio."""

    target: Path
    output_dir: Path

    language: str | None = None
    task: str = "transcribe"
    model_size: str = "small"
    device: str = "auto"
    compute_type: str = "auto"

    recursive: bool = False
    overwrite: bool = False
    per_audio_subdir: bool = False

    write_srt: bool = True
    write_vtt: bool = True
    write_txt: bool = True
    write_json: bool = True
    write_phrase_audio: bool = True

    phrase_audio_subdir: str = "phrase_audio"
    phrase_audio_format: str = "mp3"
    phrase_audio_bitrate: str = "64k"
    phrase_audio_sample_rate: int = 16000
    phrase_audio_channels: int = 1
    phrase_audio_padding_ms: int = 120
    phrase_audio_filename_prefix: str = "phrase"

    beam_size: int = 5
    vad_filter: bool = True
    initial_prompt: str | None = None

    log_filename: str = "pipeline_audio_to_subtitles.log"
    check_ffmpeg_available: bool = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generare sottotitoli da uno o più file audio con faster-whisper."
    )

    parser.add_argument(
        "target",
        help="File audio oppure directory contenente file audio."
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory di output."
    )

    parser.add_argument(
        "--language",
        default=None,
        help="Codice lingua, per esempio en, de, ja, it. Se omesso, rilevamento automatico."
    )

    parser.add_argument(
        "--model-size",
        default="small",
        help="Modello faster-whisper: tiny, base, small, medium, large-v3 ecc. Default: small."
    )

    parser.add_argument(
        "--task",
        default="transcribe",
        choices=["transcribe", "translate"],
        help="transcribe mantiene la lingua originale; translate traduce in inglese. Default: transcribe."
    )

    parser.add_argument(
        "--device",
        default="auto",
        help="Dispositivo faster-whisper: auto, cpu, cuda. Default: auto."
    )

    parser.add_argument(
        "--compute-type",
        default="auto",
        help="Tipo calcolo faster-whisper: auto, int8, float16, float32 ecc. Default: auto."
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Se target è una directory, cercare audio anche nelle sottodirectory."
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sovrascrivere file già esistenti."
    )

    parser.add_argument(
        "--per-audio-subdir",
        action="store_true",
        help="Creare una sottodirectory di output per ogni file audio."
    )

    parser.add_argument(
        "--no-srt",
        action="store_true",
        help="Non generare file SRT."
    )

    parser.add_argument(
        "--no-vtt",
        action="store_true",
        help="Non generare file VTT."
    )

    parser.add_argument(
        "--no-txt",
        action="store_true",
        help="Non generare file TXT."
    )

    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Non generare file JSON tecnico con segmenti e metadati."
    )

    parser.add_argument(
        "--no-phrase-audio",
        action="store_true",
        help="Non generare piccoli file audio per ogni frase/segmento."
    )

    parser.add_argument(
        "--phrase-audio-format",
        default="mp3",
        choices=["mp3", "ogg", "wav", "opus"],
        help="Formato dei piccoli file audio per frase. Default: mp3."
    )

    parser.add_argument(
        "--phrase-audio-bitrate",
        default="64k",
        help="Bitrate dei piccoli file audio per frase, per esempio 48k, 64k, 96k. Default: 64k."
    )

    parser.add_argument(
        "--phrase-audio-padding-ms",
        type=int,
        default=120,
        help="Padding in millisecondi prima e dopo il segmento. Default: 120."
    )

    parser.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="Beam size per faster-whisper. Default: 5."
    )

    parser.add_argument(
        "--no-vad-filter",
        action="store_true",
        help="Disabilitare VAD filter."
    )

    parser.add_argument(
        "--initial-prompt",
        default=None,
        help="Prompt iniziale opzionale per aiutare la trascrizione."
    )

    return parser.parse_args()


def build_options_from_args(args: argparse.Namespace) -> AudioToSubtitlesOptions:
    return AudioToSubtitlesOptions(
        target=Path(args.target).expanduser().resolve(),
        output_dir=Path(args.output_dir).expanduser().resolve(),
        language=args.language,
        task=args.task,
        model_size=args.model_size,
        device=args.device,
        compute_type=args.compute_type,
        recursive=args.recursive,
        overwrite=args.overwrite,
        per_audio_subdir=args.per_audio_subdir,
        write_srt=not args.no_srt,
        write_vtt=not args.no_vtt,
        write_txt=not args.no_txt,
        write_json=not args.no_json,
        write_phrase_audio=not args.no_phrase_audio,
        phrase_audio_format=args.phrase_audio_format,
        phrase_audio_bitrate=args.phrase_audio_bitrate,
        phrase_audio_padding_ms=args.phrase_audio_padding_ms,
        beam_size=args.beam_size,
        vad_filter=not args.no_vad_filter,
        initial_prompt=args.initial_prompt,
    )


def create_logger(
    output_dir: Path,
    log_filename: str
) -> logging.Logger:
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    logger = logging.getLogger("audio_to_subtitles")
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
        output_dir / log_filename,
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


def check_runtime_requirements(options: AudioToSubtitlesOptions, logger: logging.Logger) -> None:
    if options.check_ffmpeg_available and shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg non trovato nel PATH. Installare ffmpeg e riprovare."
        )

    try:
        import faster_whisper  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper non installato. Installare con: python -m pip install faster-whisper"
        ) from exc

    logger.debug("Requisiti runtime verificati.")


def is_audio_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS


def discover_audio_files(target: Path, recursive: bool) -> list[Path]:
    if target.is_file():
        if not is_audio_file(target):
            raise RuntimeError(
                f"Il file non sembra un audio supportato: {target}"
            )
        return [target]

    if not target.is_dir():
        raise RuntimeError(
            f"Target non trovato: {target}"
        )

    iterator: Iterable[Path]

    if recursive:
        iterator = target.rglob("*")
    else:
        iterator = target.iterdir()

    audio_files = sorted(
        path for path in iterator
        if is_audio_file(path)
    )

    if not audio_files:
        raise RuntimeError(
            f"Nessun file audio trovato in: {target}"
        )

    return audio_files


def output_dir_for_audio(
    audio_path: Path,
    options: AudioToSubtitlesOptions,
    total_audio_files: int
) -> Path:
    if options.per_audio_subdir or total_audio_files > 1:
        return options.output_dir / f"out_{audio_path.stem}"

    return options.output_dir


def language_suffix(language: str | None) -> str:
    if not language:
        return ""

    safe = re.sub(r"[^A-Za-z0-9_-]", "_", language.strip())

    return f"_{safe}" if safe else ""


def output_stem(audio_path: Path, language: str | None) -> str:
    return f"{audio_path.stem}{language_suffix(language)}"


def format_srt_timestamp(seconds: float) -> str:
    millis_total = int(round(seconds * 1000))
    millis = millis_total % 1000
    seconds_total = millis_total // 1000
    sec = seconds_total % 60
    minutes_total = seconds_total // 60
    minute = minutes_total % 60
    hour = minutes_total // 60

    return f"{hour:02d}:{minute:02d}:{sec:02d},{millis:03d}"


def format_vtt_timestamp(seconds: float) -> str:
    return format_srt_timestamp(seconds).replace(",", ".")


def normalize_segment_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def write_srt(path: Path, segments: list[TranscriptSegment], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        return

    lines: list[str] = []

    for segment in segments:
        lines.append(str(segment.index))
        lines.append(
            f"{format_srt_timestamp(segment.start)} --> {format_srt_timestamp(segment.end)}"
        )
        lines.append(segment.text)
        lines.append("")

    path.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8"
    )


def write_vtt(path: Path, segments: list[TranscriptSegment], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        return

    lines: list[str] = ["WEBVTT", ""]

    for segment in segments:
        lines.append(
            f"{format_vtt_timestamp(segment.start)} --> {format_vtt_timestamp(segment.end)}"
        )
        lines.append(segment.text)
        lines.append("")

    path.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8"
    )


def write_txt(path: Path, segments: list[TranscriptSegment], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        return

    text = "\n".join(
        segment.text
        for segment in segments
    )

    path.write_text(
        text.rstrip() + "\n",
        encoding="utf-8"
    )


def write_json_report(
    path: Path,
    audio_path: Path,
    segments: list[TranscriptSegment],
    language: str | None,
    detected_language: str | None,
    options: AudioToSubtitlesOptions,
    overwrite: bool
) -> None:
    if path.exists() and not overwrite:
        return

    data = {
        "audio_path": str(audio_path),
        "language": language,
        "detected_language": detected_language,
        "task": options.task,
        "model_size": options.model_size,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "segments": [
            {
                "index": segment.index,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            }
            for segment in segments
        ],
    }

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )


def run_ffmpeg(command: list[str], logger: logging.Logger) -> None:
    logger.debug("Comando ffmpeg: %s", " ".join(command))

    import subprocess

    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    logger.debug("ffmpeg stdout: %s", completed.stdout)
    logger.debug("ffmpeg stderr: %s", completed.stderr)

    if completed.returncode != 0:
        raise RuntimeError(
            "Errore ffmpeg durante l'estrazione audio frase. Dettagli nel log."
        )


def seconds_to_filename_label(seconds: float) -> str:
    millis_total = int(round(seconds * 1000))
    millis = millis_total % 1000
    seconds_total = millis_total // 1000
    sec = seconds_total % 60
    minutes_total = seconds_total // 60
    minute = minutes_total % 60
    hour = minutes_total // 60

    return f"{hour:02d}-{minute:02d}-{sec:02d}-{millis:03d}"


def first_words_for_filename(text: str, max_words: int = 4, max_length: int = 60) -> str:
    words = re.findall(
        r"[\wÀ-ÖØ-öø-ÿĀ-ſ一-龯ぁ-んァ-ンー]+",
        text,
        flags=re.UNICODE
    )

    selected = words[:max_words]

    if not selected:
        return "senza_testo"

    joined = "_".join(selected)
    joined = re.sub(r"[^A-Za-z0-9_À-ÖØ-öø-ÿĀ-ſ一-龯ぁ-んァ-ンー-]", "_", joined)
    joined = re.sub(r"_+", "_", joined).strip("_")

    return joined[:max_length] or "senza_testo"


def safe_ascii_filename_part(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_\-]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")

    return value or "item"


def phrase_audio_output_path(
    phrase_audio_dir: Path,
    segment: TranscriptSegment,
    options: AudioToSubtitlesOptions
) -> Path:
    timestamp = seconds_to_filename_label(segment.start)
    words = safe_ascii_filename_part(first_words_for_filename(segment.text))

    return phrase_audio_dir / f"{options.phrase_audio_filename_prefix}_{timestamp}_{words}.{options.phrase_audio_format}"


def ffmpeg_audio_codec_args(options: AudioToSubtitlesOptions) -> list[str]:
    if options.phrase_audio_format == "mp3":
        return [
            "-codec:a",
            "libmp3lame",
            "-b:a",
            options.phrase_audio_bitrate,
        ]

    if options.phrase_audio_format == "ogg":
        return [
            "-codec:a",
            "libvorbis",
            "-b:a",
            options.phrase_audio_bitrate,
        ]

    if options.phrase_audio_format == "opus":
        return [
            "-codec:a",
            "libopus",
            "-b:a",
            options.phrase_audio_bitrate,
        ]

    if options.phrase_audio_format == "wav":
        return [
            "-codec:a",
            "pcm_s16le",
        ]

    raise RuntimeError(
        f"Formato audio frase non supportato: {options.phrase_audio_format}"
    )


def extract_phrase_audio_files(
    audio_path: Path,
    audio_output_dir: Path,
    segments: list[TranscriptSegment],
    options: AudioToSubtitlesOptions,
    logger: logging.Logger
) -> list[Path]:
    phrase_audio_dir = audio_output_dir / options.phrase_audio_subdir
    phrase_audio_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_paths: list[Path] = []
    padding_seconds = max(0, options.phrase_audio_padding_ms) / 1000

    for segment in segments:
        start = max(0.0, segment.start - padding_seconds)
        end = max(start, segment.end + padding_seconds)
        duration = max(0.05, end - start)

        output_path = phrase_audio_output_path(
            phrase_audio_dir=phrase_audio_dir,
            segment=segment,
            options=options
        )

        if output_path.exists() and not options.overwrite:
            logger.info("Audio frase già esistente, salto: %s", output_path)
            output_paths.append(output_path)
            continue

        logger.info("Estrazione audio frase: %s", output_path)

        command = [
            "ffmpeg",
            "-y" if options.overwrite else "-n",
            "-ss",
            f"{start:.3f}",
            "-i",
            str(audio_path),
            "-t",
            f"{duration:.3f}",
            "-vn",
            "-ac",
            str(options.phrase_audio_channels),
            "-ar",
            str(options.phrase_audio_sample_rate),
            *ffmpeg_audio_codec_args(options),
            str(output_path),
        ]

        run_ffmpeg(command, logger)
        output_paths.append(output_path)

    return output_paths


def transcribe_one_audio(
    audio_path: Path,
    audio_output_dir: Path,
    model,
    options: AudioToSubtitlesOptions,
    logger: logging.Logger
) -> AudioTranscriptionResult:
    audio_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    logger.info("File audio elaborato: %s", audio_path)
    logger.info("Directory output audio: %s", audio_output_dir)

    errors: list[str] = []

    try:
        whisper_segments, info = model.transcribe(
            str(audio_path),
            language=options.language,
            task=options.task,
            beam_size=options.beam_size,
            vad_filter=options.vad_filter,
            initial_prompt=options.initial_prompt,
        )

        detected_language = getattr(info, "language", None)

        segments: list[TranscriptSegment] = []

        for idx, segment in enumerate(whisper_segments, start=1):
            text = normalize_segment_text(segment.text)

            if not text:
                continue

            segments.append(
                TranscriptSegment(
                    index=len(segments) + 1,
                    start=float(segment.start),
                    end=float(segment.end),
                    text=text,
                )
            )

        logger.info("Segmenti trascritti: %s", len(segments))
        logger.info("Lingua rilevata: %s", detected_language)

        effective_language = options.language
        stem = output_stem(audio_path, effective_language)

        srt_path = audio_output_dir / f"{stem}.srt"
        vtt_path = audio_output_dir / f"{stem}.vtt"
        txt_path = audio_output_dir / f"{stem}.txt"
        json_path = audio_output_dir / f"{stem}.json"

        written_srt = None
        written_vtt = None
        written_txt = None
        written_json = None
        phrase_audio_paths: list[Path] = []

        if options.write_srt:
            write_srt(srt_path, segments, options.overwrite)
            written_srt = srt_path
            logger.info("SRT scritto: %s", srt_path)

        if options.write_vtt:
            write_vtt(vtt_path, segments, options.overwrite)
            written_vtt = vtt_path
            logger.info("VTT scritto: %s", vtt_path)

        if options.write_txt:
            write_txt(txt_path, segments, options.overwrite)
            written_txt = txt_path
            logger.info("TXT scritto: %s", txt_path)

        if options.write_json:
            write_json_report(
                path=json_path,
                audio_path=audio_path,
                segments=segments,
                language=effective_language,
                detected_language=detected_language,
                options=options,
                overwrite=options.overwrite,
            )
            written_json = json_path
            logger.info("JSON scritto: %s", json_path)

        if options.write_phrase_audio:
            phrase_audio_paths = extract_phrase_audio_files(
                audio_path=audio_path,
                audio_output_dir=audio_output_dir,
                segments=segments,
                options=options,
                logger=logger
            )
            logger.info("File audio frase generati: %s", len(phrase_audio_paths))

        return AudioTranscriptionResult(
            audio_path=audio_path,
            output_dir=audio_output_dir,
            language=effective_language,
            detected_language=detected_language,
            srt_path=written_srt,
            vtt_path=written_vtt,
            txt_path=written_txt,
            json_path=written_json,
            phrase_audio_paths=phrase_audio_paths,
            segments_count=len(segments),
            errors=errors,
        )

    except Exception as exc:
        message = f"Errore trascrivendo {audio_path}: {exc}"
        errors.append(message)
        logger.exception(message)

        return AudioTranscriptionResult(
            audio_path=audio_path,
            output_dir=audio_output_dir,
            language=options.language,
            errors=errors,
        )


def transcribe_audio_to_subtitles(
    target: str | Path,
    output_dir: str | Path,
    *,
    language: str | None = None,
    task: str = "transcribe",
    model_size: str = "small",
    device: str = "auto",
    compute_type: str = "auto",
    recursive: bool = False,
    overwrite: bool = False,
    per_audio_subdir: bool = False,
    write_srt: bool = True,
    write_vtt: bool = True,
    write_txt: bool = True,
    write_json: bool = True,
    write_phrase_audio: bool = True,
    phrase_audio_format: str = "mp3",
    phrase_audio_bitrate: str = "64k",
    phrase_audio_padding_ms: int = 120,
    beam_size: int = 5,
    vad_filter: bool = True,
    initial_prompt: str | None = None,
    check_ffmpeg_available: bool = True,
    logger: logging.Logger | None = None,
) -> list[AudioTranscriptionResult]:
    """
    Funzione principale da invocare dal pipeline master.

    target:
        File audio oppure directory di file audio.

    output_dir:
        Directory di output dei sottotitoli.

    language:
        Codice lingua opzionale. Se specificato, viene usato anche nel nome
        dei file di output: <audio_stem>_<language>.srt.
        Se non specificato, viene usato <audio_stem>.srt.
    """

    options = AudioToSubtitlesOptions(
        target=Path(target).expanduser().resolve(),
        output_dir=Path(output_dir).expanduser().resolve(),
        language=language,
        task=task,
        model_size=model_size,
        device=device,
        compute_type=compute_type,
        recursive=recursive,
        overwrite=overwrite,
        per_audio_subdir=per_audio_subdir,
        write_srt=write_srt,
        write_vtt=write_vtt,
        write_txt=write_txt,
        write_json=write_json,
        write_phrase_audio=write_phrase_audio,
        phrase_audio_format=phrase_audio_format,
        phrase_audio_bitrate=phrase_audio_bitrate,
        phrase_audio_padding_ms=phrase_audio_padding_ms,
        beam_size=beam_size,
        vad_filter=vad_filter,
        initial_prompt=initial_prompt,
        check_ffmpeg_available=check_ffmpeg_available,
    )

    if logger is None:
        logger = create_logger(
            output_dir=options.output_dir,
            log_filename=options.log_filename
        )

    logger.info("Avvio step audio-to-subtitles.")
    logger.debug("Opzioni: %s", options)

    check_runtime_requirements(options, logger)

    audio_files = discover_audio_files(
        target=options.target,
        recursive=options.recursive
    )

    logger.info("File audio trovati: %s", len(audio_files))
    logger.info("Caricamento modello faster-whisper: %s", options.model_size)

    from faster_whisper import WhisperModel

    model = WhisperModel(
        options.model_size,
        device=options.device,
        compute_type=options.compute_type,
    )

    results: list[AudioTranscriptionResult] = []

    for audio_path in audio_files:
        audio_output_dir = output_dir_for_audio(
            audio_path=audio_path,
            options=options,
            total_audio_files=len(audio_files)
        )

        result = transcribe_one_audio(
            audio_path=audio_path,
            audio_output_dir=audio_output_dir,
            model=model,
            options=options,
            logger=logger
        )

        results.append(result)

    logger.info("Step audio-to-subtitles completato. File elaborati: %s", len(results))

    return results


def main() -> int:
    args = parse_args()
    options = build_options_from_args(args)

    logger = create_logger(
        output_dir=options.output_dir,
        log_filename=options.log_filename
    )

    try:
        results = transcribe_audio_to_subtitles(
            target=options.target,
            output_dir=options.output_dir,
            language=options.language,
            task=options.task,
            model_size=options.model_size,
            device=options.device,
            compute_type=options.compute_type,
            recursive=options.recursive,
            overwrite=options.overwrite,
            per_audio_subdir=options.per_audio_subdir,
            write_srt=options.write_srt,
            write_vtt=options.write_vtt,
            write_txt=options.write_txt,
            write_json=options.write_json,
            write_phrase_audio=options.write_phrase_audio,
            phrase_audio_format=options.phrase_audio_format,
            phrase_audio_bitrate=options.phrase_audio_bitrate,
            phrase_audio_padding_ms=options.phrase_audio_padding_ms,
            beam_size=options.beam_size,
            vad_filter=options.vad_filter,
            initial_prompt=options.initial_prompt,
            check_ffmpeg_available=options.check_ffmpeg_available,
            logger=logger,
        )

        failures = sum(
            1 for result in results
            if result.errors
        )

        print(
            f"File audio elaborati: {len(results)}",
            file=sys.stderr
        )

        if failures:
            print(
                f"File con errori: {failures}",
                file=sys.stderr
            )
            return 1

        print(
            "Completato senza errori.",
            file=sys.stderr
        )
        return 0

    except Exception as exc:
        logger.exception("Errore generale nello step audio-to-subtitles.")
        print(
            f"ERRORE: {exc}",
            file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
