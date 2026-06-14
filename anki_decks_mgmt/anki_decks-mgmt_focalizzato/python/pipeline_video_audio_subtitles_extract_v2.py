#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline_video_audio_subtitles_extract_v2.py

Scopo
-----
Tratta della pipeline per elaborare file video e produrre output utilizzabili
nelle fasi successive di generazione deck Anki.

Lo script può essere usato in due modi:

1. Come modulo importato da uno script master.
2. Come script autonomo da riga di comando.

Funzione principale per script master
-------------------------------------
    process_video_audio_subtitles(
        target=Path("video.mp4"),
        output_dir=Path("out_pipeline"),
        subtitles=Path("video.srt"),
        write_mp3=True,
        write_ogg=True,
        write_frames=True,
        write_phrase_files=True,
    )

Output controllabili singolarmente
----------------------------------
- write_mp3: estrazione audio MP3.
- write_ogg: estrazione audio OGG Vorbis.
- write_frames: estrazione fotogrammi da timestamp sottotitoli.
- write_phrase_files: scrittura file testo per ogni frase/segmento.

Requisiti
---------
- Python 3.10+
- ffmpeg installato e disponibile nel PATH.

Note
----
- Se target è una directory, vengono cercati tutti i file video supportati.
- Se subtitles è un file, viene usato quel file. Questo è adatto soprattutto
  quando target è un singolo video.
- Se subtitles è una directory, per ogni video viene cercato un file .srt o .vtt
  con lo stesso nome base del video.
- Se subtitles è None e auto_find_subtitles=True, viene cercato un file .srt o
  .vtt accanto al video.
- Ogni cue del file sottotitoli viene trattato come frase/segmento.
  Se un cue contiene più frasi reali, senza timestamp più granulari non è
  possibile generare fotogrammi distinti per ogni frase reale.
"""

from __future__ import annotations

import argparse
import html
import logging
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".wmv",
    ".m4v",
    ".webm",
    ".flv",
    ".mpeg",
    ".mpg",
}

SUBTITLE_EXTENSIONS = {
    ".srt",
    ".vtt",
}


@dataclass(frozen=True)
class SubtitleCue:
    """Singolo segmento/frase ricavato dal file sottotitoli."""

    index: int
    start_seconds: float
    end_seconds: float | None
    start_label: str
    text: str


@dataclass(frozen=True)
class VideoPipelineResult:
    """Risultato dell'elaborazione di un singolo video."""

    video_path: Path
    output_dir: Path
    mp3_path: Path | None = None
    ogg_path: Path | None = None
    subtitles_path: Path | None = None
    frame_paths: list[Path] = field(default_factory=list)
    phrase_paths: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class VideoPipelineOptions:
    """Opzioni complete per l'elaborazione video."""

    target: Path
    output_dir: Path
    subtitles: Path | None = None

    recursive: bool = False
    overwrite: bool = False
    auto_find_subtitles: bool = True

    write_mp3: bool = True
    write_ogg: bool = True
    write_frames: bool = True
    write_phrase_files: bool = True

    per_video_subdir: bool = True

    audio_subdir: str = "audio"
    frames_subdir: str = "frames"
    phrases_subdir: str = "phrases"
    logs_subdir: str = "logs"

    mp3_quality: int = 2
    ogg_quality: int = 5
    jpg_quality: int = 2
    phrase_encoding: str = "utf-8"

    frame_filename_prefix: str = "fotogr"
    phrase_filename_prefix: str = "phrase"
    max_words_in_frame_name: int = 4
    max_frame_word_part_length: int = 80

    check_ffmpeg_available: bool = True
    create_log_file: bool = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estrarre audio, fotogrammi e frasi da video e sottotitoli."
        )
    )

    parser.add_argument(
        "target",
        help="File video oppure directory contenente file video."
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory di output principale."
    )

    parser.add_argument(
        "--subtitles",
        default=None,
        help=(
            "File sottotitoli .srt/.vtt oppure directory di sottotitoli. "
            "Se omesso, viene cercato un file con lo stesso stem del video."
        )
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Se target è una directory, cercare video anche nelle sottodirectory."
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sovrascrivere file già esistenti."
    )

    parser.add_argument(
        "--no-auto-find-subtitles",
        action="store_true",
        help="Non cercare automaticamente sottotitoli accanto al video."
    )

    parser.add_argument(
        "--no-per-video-subdir",
        action="store_true",
        help=(
            "Non creare una sottodirectory per ogni video dentro output-dir. "
            "Da usare solo quando si elabora un singolo video o si gestiscono "
            "i nomi a livello superiore."
        )
    )

    parser.add_argument(
        "--no-mp3",
        action="store_true",
        help="Non estrarre audio MP3."
    )

    parser.add_argument(
        "--no-ogg",
        action="store_true",
        help="Non estrarre audio OGG Vorbis."
    )

    parser.add_argument(
        "--no-frames",
        action="store_true",
        help="Non estrarre fotogrammi dai sottotitoli."
    )

    parser.add_argument(
        "--no-phrase-files",
        action="store_true",
        help="Non scrivere file testo per le frasi dei sottotitoli."
    )

    parser.add_argument(
        "--jpg-quality",
        type=int,
        default=2,
        help=(
            "Qualità JPEG per ffmpeg -q:v. Valori più bassi indicano qualità maggiore. "
            "Default: 2."
        )
    )

    return parser.parse_args()


def build_options_from_args(args: argparse.Namespace) -> VideoPipelineOptions:
    return VideoPipelineOptions(
        target=Path(args.target).expanduser().resolve(),
        output_dir=Path(args.output_dir).expanduser().resolve(),
        subtitles=(
            Path(args.subtitles).expanduser().resolve()
            if args.subtitles
            else None
        ),
        recursive=args.recursive,
        overwrite=args.overwrite,
        auto_find_subtitles=not args.no_auto_find_subtitles,
        write_mp3=not args.no_mp3,
        write_ogg=not args.no_ogg,
        write_frames=not args.no_frames,
        write_phrase_files=not args.no_phrase_files,
        per_video_subdir=not args.no_per_video_subdir,
        jpg_quality=args.jpg_quality,
    )


def ensure_logger(
    options: VideoPipelineOptions,
    logger: logging.Logger | None
) -> logging.Logger:
    """Restituire un logger utilizzabile anche quando lo script è importato."""

    if logger is not None:
        return logger

    logger = logging.getLogger("video_pipeline")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(levelname)s: %(message)s")
    )
    logger.addHandler(console_handler)

    if options.create_log_file:
        log_dir = options.output_dir / options.logs_subdir
        log_dir.mkdir(
            parents=True,
            exist_ok=True
        )
        file_handler = logging.FileHandler(
            log_dir / "pipeline_video_audio_subtitles_extract.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )
        )
        logger.addHandler(file_handler)

    return logger


def check_ffmpeg(logger: logging.Logger) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg non trovato nel PATH. Installare ffmpeg e riprovare."
        )

    logger.debug("ffmpeg trovato nel PATH.")


def is_video_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS


def discover_videos(
    target: Path,
    recursive: bool
) -> list[Path]:
    if target.is_file():
        if not is_video_file(target):
            raise RuntimeError(
                f"Il file non sembra un video supportato: {target}"
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

    videos = sorted(
        path for path in iterator
        if is_video_file(path)
    )

    if not videos:
        raise RuntimeError(
            f"Nessun file video trovato in: {target}"
        )

    return videos


def output_dir_for_video(
    video_path: Path,
    options: VideoPipelineOptions,
    total_videos: int
) -> Path:
    if options.per_video_subdir or total_videos > 1:
        return options.output_dir / f"out_{video_path.stem}"

    return options.output_dir


def ffmpeg_overwrite_args(overwrite: bool) -> list[str]:
    return ["-y"] if overwrite else ["-n"]


def run_ffmpeg(
    command: list[str],
    logger: logging.Logger
) -> None:
    logger.debug("Comando ffmpeg: %s", " ".join(command))

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
            "Errore ffmpeg. Dettagli disponibili nel log."
        )


def extract_mp3(
    video_path: Path,
    audio_dir: Path,
    options: VideoPipelineOptions,
    logger: logging.Logger
) -> Path:
    audio_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    mp3_path = audio_dir / f"{video_path.stem}.mp3"

    logger.info("Estrazione audio MP3: %s", mp3_path)

    run_ffmpeg([
        "ffmpeg",
        *ffmpeg_overwrite_args(options.overwrite),
        "-i",
        str(video_path),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        str(options.mp3_quality),
        str(mp3_path),
    ], logger)

    return mp3_path


def extract_ogg(
    video_path: Path,
    audio_dir: Path,
    options: VideoPipelineOptions,
    logger: logging.Logger
) -> Path:
    audio_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    ogg_path = audio_dir / f"{video_path.stem}.ogg"

    logger.info("Estrazione audio OGG Vorbis: %s", ogg_path)

    run_ffmpeg([
        "ffmpeg",
        *ffmpeg_overwrite_args(options.overwrite),
        "-i",
        str(video_path),
        "-vn",
        "-codec:a",
        "libvorbis",
        "-q:a",
        str(options.ogg_quality),
        str(ogg_path),
    ], logger)

    return ogg_path


def find_subtitles_for_video(
    video_path: Path,
    options: VideoPipelineOptions
) -> Path | None:
    if options.subtitles is not None:
        subtitles_path = options.subtitles

        if subtitles_path.is_file():
            if subtitles_path.suffix.lower() not in SUBTITLE_EXTENSIONS:
                raise RuntimeError(
                    f"Formato sottotitoli non supportato: {subtitles_path}"
                )
            return subtitles_path

        if subtitles_path.is_dir():
            for ext in sorted(SUBTITLE_EXTENSIONS):
                candidate = subtitles_path / f"{video_path.stem}{ext}"
                if candidate.exists():
                    return candidate
            return None

        raise RuntimeError(
            f"Percorso sottotitoli non trovato: {subtitles_path}"
        )

    if not options.auto_find_subtitles:
        return None

    for ext in sorted(SUBTITLE_EXTENSIONS):
        candidate = video_path.with_suffix(ext)
        if candidate.exists():
            return candidate

    return None


def parse_timestamp_to_seconds(value: str) -> float:
    value = value.strip().replace(",", ".")

    match = re.match(
        r"^(?:(\d+):)?(\d{1,2}):(\d{1,2})(?:\.(\d{1,3}))?$",
        value
    )

    if not match:
        raise ValueError(
            f"Timestamp non valido: {value}"
        )

    hours_text, minutes_text, seconds_text, millis_text = match.groups()

    hours = int(hours_text or 0)
    minutes = int(minutes_text)
    seconds = int(seconds_text)
    millis = int((millis_text or "0").ljust(3, "0")[:3])

    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def seconds_to_label(seconds: float) -> str:
    total_millis = int(round(seconds * 1000))
    millis = total_millis % 1000
    total_seconds = total_millis // 1000
    sec = total_seconds % 60
    total_minutes = total_seconds // 60
    minute = total_minutes % 60
    hour = total_minutes // 60

    return f"{hour:02d}-{minute:02d}-{sec:02d}-{millis:03d}"


def clean_subtitle_text(lines: list[str]) -> str:
    text = " ".join(
        line.strip()
        for line in lines
        if line.strip()
    )

    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\{\\.*?\}", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def parse_subtitles(
    path: Path,
    logger: logging.Logger
) -> list[SubtitleCue]:
    raw_text = path.read_text(
        encoding="utf-8-sig",
        errors="replace"
    )

    raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    lines = raw_text.split("\n")

    cues: list[SubtitleCue] = []
    block: list[str] = []

    def flush_block(current_block: list[str]) -> None:
        if not current_block:
            return

        local = [line for line in current_block if line.strip()]

        if not local:
            return

        if local[0].strip().upper() == "WEBVTT":
            return

        if re.fullmatch(r"\d+", local[0].strip()) and len(local) >= 2:
            local = local[1:]

        time_line_index = None

        for i, line in enumerate(local):
            if "-->" in line:
                time_line_index = i
                break

        if time_line_index is None:
            return

        time_line = local[time_line_index]
        left, right = time_line.split("-->", 1)
        start_text = left.strip()
        end_text = right.strip().split()[0]

        try:
            start_seconds = parse_timestamp_to_seconds(start_text)
        except ValueError:
            logger.warning("Timestamp iniziale non valido nel blocco: %s", current_block)
            return

        try:
            end_seconds = parse_timestamp_to_seconds(end_text)
        except ValueError:
            end_seconds = None

        cue_text_lines = local[time_line_index + 1:]
        cue_text = clean_subtitle_text(cue_text_lines)

        if not cue_text:
            return

        cues.append(
            SubtitleCue(
                index=len(cues) + 1,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                start_label=seconds_to_label(start_seconds),
                text=cue_text
            )
        )

    for line in lines:
        if line.strip() == "":
            flush_block(block)
            block = []
        else:
            block.append(line)

    flush_block(block)

    return cues


def first_words_for_filename(
    text: str,
    max_words: int,
    max_length: int
) -> str:
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


def safe_ascii_filename_part(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_\-]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")

    return name or "item"


def extract_frame(
    video_path: Path,
    cue: SubtitleCue,
    frames_dir: Path,
    options: VideoPipelineOptions,
    logger: logging.Logger
) -> Path:
    frames_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    words = safe_ascii_filename_part(
        first_words_for_filename(
            text=cue.text,
            max_words=options.max_words_in_frame_name,
            max_length=options.max_frame_word_part_length
        )
    )

    frame_path = frames_dir / f"{options.frame_filename_prefix}_{cue.start_label}_{words}.jpg"

    logger.info("Estrazione fotogramma: %s", frame_path)

    run_ffmpeg([
        "ffmpeg",
        *ffmpeg_overwrite_args(options.overwrite),
        "-ss",
        f"{cue.start_seconds:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        str(options.jpg_quality),
        str(frame_path),
    ], logger)

    return frame_path


def write_phrase_file(
    cue: SubtitleCue,
    phrases_dir: Path,
    options: VideoPipelineOptions,
    logger: logging.Logger
) -> Path:
    phrases_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    phrase_path = phrases_dir / f"{options.phrase_filename_prefix}_{cue.start_label}.txt"

    if phrase_path.exists() and not options.overwrite:
        logger.info("File frase già esistente, salto: %s", phrase_path)
        return phrase_path

    phrase_path.write_text(
        cue.text + "\n",
        encoding=options.phrase_encoding
    )

    logger.info("File frase scritto: %s", phrase_path)

    return phrase_path


def process_subtitles_for_video(
    video_path: Path,
    subtitles_path: Path,
    video_output_dir: Path,
    options: VideoPipelineOptions,
    logger: logging.Logger
) -> tuple[list[Path], list[Path], list[str]]:
    logger.info("File sottotitoli: %s", subtitles_path)

    errors: list[str] = []
    frame_paths: list[Path] = []
    phrase_paths: list[Path] = []

    cues = parse_subtitles(
        subtitles_path,
        logger=logger
    )

    logger.info("Segmenti/frasi trovati nei sottotitoli: %s", len(cues))

    frames_dir = video_output_dir / options.frames_subdir
    phrases_dir = video_output_dir / options.phrases_subdir

    for cue in cues:
        if options.write_frames:
            try:
                frame_paths.append(
                    extract_frame(
                        video_path=video_path,
                        cue=cue,
                        frames_dir=frames_dir,
                        options=options,
                        logger=logger
                    )
                )
            except Exception as exc:
                message = f"Errore fotogramma segmento {cue.index} {cue.start_label}: {exc}"
                errors.append(message)
                logger.error(message)

        if options.write_phrase_files:
            try:
                phrase_paths.append(
                    write_phrase_file(
                        cue=cue,
                        phrases_dir=phrases_dir,
                        options=options,
                        logger=logger
                    )
                )
            except Exception as exc:
                message = f"Errore file frase segmento {cue.index} {cue.start_label}: {exc}"
                errors.append(message)
                logger.error(message)

    return frame_paths, phrase_paths, errors


def process_one_video(
    video_path: Path,
    video_output_dir: Path,
    options: VideoPipelineOptions,
    logger: logging.Logger
) -> VideoPipelineResult:
    logger.info("File video elaborato: %s", video_path)
    logger.info("Directory output video: %s", video_output_dir)

    video_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    errors: list[str] = []
    mp3_path: Path | None = None
    ogg_path: Path | None = None
    subtitles_path: Path | None = None
    frame_paths: list[Path] = []
    phrase_paths: list[Path] = []

    audio_dir = video_output_dir / options.audio_subdir

    if options.write_mp3:
        try:
            mp3_path = extract_mp3(
                video_path=video_path,
                audio_dir=audio_dir,
                options=options,
                logger=logger
            )
        except Exception as exc:
            message = f"Errore estrazione MP3: {exc}"
            errors.append(message)
            logger.error(message)

    if options.write_ogg:
        try:
            ogg_path = extract_ogg(
                video_path=video_path,
                audio_dir=audio_dir,
                options=options,
                logger=logger
            )
        except Exception as exc:
            message = f"Errore estrazione OGG: {exc}"
            errors.append(message)
            logger.error(message)

    if options.write_frames or options.write_phrase_files:
        try:
            subtitles_path = find_subtitles_for_video(
                video_path=video_path,
                options=options
            )

            if subtitles_path is None:
                logger.info("Nessun file sottotitoli trovato per: %s", video_path)
            else:
                frame_paths, phrase_paths, subtitle_errors = process_subtitles_for_video(
                    video_path=video_path,
                    subtitles_path=subtitles_path,
                    video_output_dir=video_output_dir,
                    options=options,
                    logger=logger
                )
                errors.extend(subtitle_errors)
        except Exception as exc:
            message = f"Errore gestione sottotitoli: {exc}"
            errors.append(message)
            logger.error(message)

    return VideoPipelineResult(
        video_path=video_path,
        output_dir=video_output_dir,
        mp3_path=mp3_path,
        ogg_path=ogg_path,
        subtitles_path=subtitles_path,
        frame_paths=frame_paths,
        phrase_paths=phrase_paths,
        errors=errors
    )


def process_video_audio_subtitles(
    target: str | Path,
    output_dir: str | Path,
    subtitles: str | Path | None = None,
    *,
    recursive: bool = False,
    overwrite: bool = False,
    auto_find_subtitles: bool = True,
    write_mp3: bool = True,
    write_ogg: bool = True,
    write_frames: bool = True,
    write_phrase_files: bool = True,
    per_video_subdir: bool = True,
    audio_subdir: str = "audio",
    frames_subdir: str = "frames",
    phrases_subdir: str = "phrases",
    logs_subdir: str = "logs",
    mp3_quality: int = 2,
    ogg_quality: int = 5,
    jpg_quality: int = 2,
    phrase_encoding: str = "utf-8",
    frame_filename_prefix: str = "fotogr",
    phrase_filename_prefix: str = "phrase",
    max_words_in_frame_name: int = 4,
    max_frame_word_part_length: int = 80,
    check_ffmpeg_available: bool = True,
    create_log_file: bool = True,
    logger: logging.Logger | None = None,
) -> list[VideoPipelineResult]:
    """
    Funzione principale flessibile da invocare da uno script master.

    Parametri principali
    --------------------
    target:
        File video o directory contenente video.

    output_dir:
        Directory di output principale. Se vengono elaborati più video,
        di default viene creata una sottodirectory per ogni video.

    subtitles:
        None, file sottotitoli o directory sottotitoli.

    write_mp3, write_ogg, write_frames, write_phrase_files:
        Controllano singolarmente la produzione degli output.

    Restituisce
    -----------
    Lista di VideoPipelineResult, uno per ogni video elaborato.
    """

    options = VideoPipelineOptions(
        target=Path(target).expanduser().resolve(),
        output_dir=Path(output_dir).expanduser().resolve(),
        subtitles=(
            Path(subtitles).expanduser().resolve()
            if subtitles is not None
            else None
        ),
        recursive=recursive,
        overwrite=overwrite,
        auto_find_subtitles=auto_find_subtitles,
        write_mp3=write_mp3,
        write_ogg=write_ogg,
        write_frames=write_frames,
        write_phrase_files=write_phrase_files,
        per_video_subdir=per_video_subdir,
        audio_subdir=audio_subdir,
        frames_subdir=frames_subdir,
        phrases_subdir=phrases_subdir,
        logs_subdir=logs_subdir,
        mp3_quality=mp3_quality,
        ogg_quality=ogg_quality,
        jpg_quality=jpg_quality,
        phrase_encoding=phrase_encoding,
        frame_filename_prefix=frame_filename_prefix,
        phrase_filename_prefix=phrase_filename_prefix,
        max_words_in_frame_name=max_words_in_frame_name,
        max_frame_word_part_length=max_frame_word_part_length,
        check_ffmpeg_available=check_ffmpeg_available,
        create_log_file=create_log_file,
    )

    logger = ensure_logger(
        options=options,
        logger=logger
    )

    logger.info("Avvio tratta video/audio/sottotitoli.")
    logger.debug("Opzioni: %s", options)

    if options.check_ffmpeg_available:
        check_ffmpeg(logger)

    options.output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    videos = discover_videos(
        target=options.target,
        recursive=options.recursive
    )

    logger.info("Video trovati: %s", len(videos))

    results: list[VideoPipelineResult] = []

    for video_path in videos:
        video_output_dir = output_dir_for_video(
            video_path=video_path,
            options=options,
            total_videos=len(videos)
        )

        result = process_one_video(
            video_path=video_path,
            video_output_dir=video_output_dir,
            options=options,
            logger=logger
        )

        results.append(result)

    logger.info("Tratta completata. Video elaborati: %s", len(results))

    return results


def main() -> int:
    args = parse_args()
    options = build_options_from_args(args)

    try:
        results = process_video_audio_subtitles(
            target=options.target,
            output_dir=options.output_dir,
            subtitles=options.subtitles,
            recursive=options.recursive,
            overwrite=options.overwrite,
            auto_find_subtitles=options.auto_find_subtitles,
            write_mp3=options.write_mp3,
            write_ogg=options.write_ogg,
            write_frames=options.write_frames,
            write_phrase_files=options.write_phrase_files,
            per_video_subdir=options.per_video_subdir,
            jpg_quality=options.jpg_quality,
        )

        failures = sum(
            1 for result in results
            if result.errors
        )

        print(
            f"Video elaborati: {len(results)}",
            file=sys.stderr
        )

        if failures:
            print(
                f"Video con errori: {failures}",
                file=sys.stderr
            )
            return 1

        print(
            "Completato senza errori.",
            file=sys.stderr
        )
        return 0

    except Exception as exc:
        print(
            f"ERRORE: {exc}",
            file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
