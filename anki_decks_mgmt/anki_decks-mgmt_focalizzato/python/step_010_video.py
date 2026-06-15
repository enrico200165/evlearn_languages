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
- write_ogg: estrazione audio OGG Vorbis, disattivata per default.
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
- Se subtitles è None e auto_find_subtitles=True, vengono cercati file .srt o
  .vtt accanto al video. Sono riconosciuti sia <video>.srt sia
  <video>_<codice_lingua>.srt, per esempio mymovie_en.srt, mymovie_ja.srt,
  mymovie_de.srt e mymovie.srt.
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

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class SubtitleCue:
    """Singolo segmento/frase ricavato dal file sottotitoli."""

    index: int
    start_seconds: float
    end_seconds: float | None
    start_label: str
    text: str


@dataclass(frozen=True)
class SubtitleTrack:
    """File sottotitoli associato a un video e alla sua lingua."""

    path: Path
    language_code: str
    is_language_explicit: bool


@dataclass(frozen=True)
class VideoPipelineResult:
    """Risultato dell'elaborazione di un singolo video."""

    video_path: Path
    output_dir: Path
    mp3_path: Path | None = None
    ogg_path: Path | None = None
    subtitles_path: Path | None = None
    copied_subtitles_path: Path | None = None
    subtitles_paths: list[Path] = field(default_factory=list)
    copied_subtitles_paths: list[Path] = field(default_factory=list)
    subtitle_languages: list[str] = field(default_factory=list)
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
    write_ogg: bool = False
    write_frames: bool = True
    write_phrase_files: bool = True
    copy_subtitles: bool = True

    per_video_subdir: bool = True

    audio_subdir: str = "audio"
    frames_subdir: str = "frames"
    phrases_subdir: str = "phrases"
    subtitles_subdir: str = "subtitles"
    logs_subdir: str = "logs"

    mp3_quality: int = 2
    ogg_quality: int = 5
    jpg_quality: int = 8
    frame_max_width: int = 480
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
        "--write-ogg",
        action="store_true",
        help="Estrarre anche audio OGG Vorbis. Default: disattivato."
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
        "--no-copy-subtitles",
        action="store_true",
        help="Non copiare i file sottotitoli trovati nella directory di output."
    )

    parser.add_argument(
        "--frame-max-width",
        type=int,
        default=480,
        help="Larghezza massima dei fotogrammi estratti. Default: 480."
    )

    parser.add_argument(
        "--jpg-quality",
        type=int,
        default=8,
        help=(
            "Qualità JPEG per ffmpeg -q:v. Valori più bassi indicano qualità maggiore. "
            "Default: 8, per file più piccoli."
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
        write_ogg=args.write_ogg,
        write_frames=not args.no_frames,
        write_phrase_files=not args.no_phrase_files,
        copy_subtitles=not args.no_copy_subtitles,
        per_video_subdir=not args.no_per_video_subdir,
        jpg_quality=args.jpg_quality,
        frame_max_width=args.frame_max_width,
    )


def ensure_logger(
    options: VideoPipelineOptions,
    logger: logging.Logger | None
) -> logging.Logger:
    """
    Creare sempre un logger proprio dello step video.

    Il log dello step video deve essere indipendente dal log del pipeline master.
    Anche quando la funzione viene invocata dal master, il dettaglio operativo
    viene scritto nel file di log della directory di output dello step.

    Il parametro logger resta nella firma per compatibilità, ma non viene usato
    per scrivere il log dettagliato dello step.
    """

    step_logger = logging.getLogger("video_audio_subtitles_step")
    step_logger.setLevel(logging.DEBUG)
    step_logger.handlers.clear()
    step_logger.propagate = False

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    )
    step_logger.addHandler(console_handler)

    options.output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    log_file = options.output_dir / "pipeline_video_audio_subtitles_extract.log"
    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    )
    step_logger.addHandler(file_handler)

    step_logger.debug("Log indipendente dello step video: %s", log_file)

    return step_logger


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


LANGUAGE_CODE_RE = re.compile(r"^[a-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})?$")


def infer_subtitle_language(
    video_path: Path,
    subtitle_path: Path
) -> SubtitleTrack | None:
    """
    Riconoscere sottotitoli associati a un video.

    Formati supportati:
    - <video_stem>.<ext>
    - <video_stem>_<language_code>.<ext>

    Esempi:
    - mymovie.srt      -> lingua non determinata: und
    - mymovie_en.srt   -> en
    - mymovie_ja.srt   -> ja
    - mymovie_de.vtt   -> de
    """

    if subtitle_path.suffix.lower() not in SUBTITLE_EXTENSIONS:
        return None

    video_stem = video_path.stem
    subtitle_stem = subtitle_path.stem

    if subtitle_stem == video_stem:
        return SubtitleTrack(
            path=subtitle_path,
            language_code="und",
            is_language_explicit=False
        )

    prefix = f"{video_stem}_"

    if subtitle_stem.startswith(prefix):
        language_code = subtitle_stem[len(prefix):]
        normalized = language_code.replace("_", "-")

        if LANGUAGE_CODE_RE.match(normalized):
            return SubtitleTrack(
                path=subtitle_path,
                language_code=normalized.lower(),
                is_language_explicit=True
            )

    return None


def find_subtitle_tracks_for_video(
    video_path: Path,
    options: VideoPipelineOptions
) -> list[SubtitleTrack]:
    """Trovare tutti i file sottotitoli associati al video."""

    candidates: list[Path] = []

    if options.subtitles is not None:
        subtitles_path = options.subtitles

        if subtitles_path.is_file():
            track = infer_subtitle_language(
                video_path=video_path,
                subtitle_path=subtitles_path
            )
            if track is None:
                raise RuntimeError(
                    f"Il file sottotitoli non corrisponde al video o ha formato non supportato: {subtitles_path}"
                )
            return [track]

        if subtitles_path.is_dir():
            candidates.extend(
                path for path in subtitles_path.iterdir()
                if path.is_file() and path.suffix.lower() in SUBTITLE_EXTENSIONS
            )
        else:
            raise RuntimeError(
                f"Percorso sottotitoli non trovato: {subtitles_path}"
            )

    elif options.auto_find_subtitles:
        candidates.extend(
            path for path in video_path.parent.iterdir()
            if path.is_file() and path.suffix.lower() in SUBTITLE_EXTENSIONS
        )
    else:
        return []

    tracks: list[SubtitleTrack] = []
    seen: set[Path] = set()

    for candidate in sorted(candidates):
        track = infer_subtitle_language(
            video_path=video_path,
            subtitle_path=candidate
        )

        if track is None:
            continue

        resolved = track.path.resolve()
        if resolved in seen:
            continue

        seen.add(resolved)
        tracks.append(track)

    return tracks


def find_subtitles_for_video(
    video_path: Path,
    options: VideoPipelineOptions
) -> Path | None:
    """Compatibilità con versioni precedenti: restituisce il primo sottotitolo trovato."""

    tracks = find_subtitle_tracks_for_video(
        video_path=video_path,
        options=options
    )

    if not tracks:
        return None

    return tracks[0].path


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
    logger: logging.Logger,
    language_code: str
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

    safe_language_code = safe_ascii_filename_part(language_code)
    frame_path = frames_dir / f"{video_path.stem}_{options.frame_filename_prefix}_{cue.start_label}_{safe_language_code}_{words}.jpg"

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
        "-vf",
        f"scale=w='min({options.frame_max_width},iw)':h=-2",
        "-q:v",
        str(options.jpg_quality),
        str(frame_path),
    ], logger)

    return frame_path


def write_phrase_file(
    cue: SubtitleCue,
    phrases_dir: Path,
    options: VideoPipelineOptions,
    logger: logging.Logger,
    video_stem: str,
    language_code: str
) -> Path:
    phrases_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_video_stem = safe_ascii_filename_part(video_stem)
    safe_language_code = safe_ascii_filename_part(language_code)
    phrase_path = phrases_dir / f"{safe_video_stem}_{options.phrase_filename_prefix}_{cue.start_label}_{safe_language_code}.txt"

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
    subtitle_track: SubtitleTrack,
    video_output_dir: Path,
    options: VideoPipelineOptions,
    logger: logging.Logger
) -> tuple[list[Path], list[Path], list[str]]:
    subtitles_path = subtitle_track.path
    language_code = subtitle_track.language_code

    logger.info("File sottotitoli: %s", subtitles_path)
    logger.info("Lingua sottotitoli: %s", language_code)

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
                        logger=logger,
                        language_code=language_code
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
                        logger=logger,
                        video_stem=video_path.stem,
                        language_code=language_code
                    )
                )
            except Exception as exc:
                message = f"Errore file frase segmento {cue.index} {cue.start_label}: {exc}"
                errors.append(message)
                logger.error(message)

    return frame_paths, phrase_paths, errors


def copy_subtitles_to_output(
    subtitles_path: Path,
    video_output_dir: Path,
    options: VideoPipelineOptions,
    logger: logging.Logger
) -> Path:
    """Copiare il file sottotitoli trovato nella directory di output del video."""

    subtitles_dir = video_output_dir / options.subtitles_subdir
    subtitles_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = subtitles_dir / subtitles_path.name

    if destination.exists() and not options.overwrite:
        logger.info("Sottotitoli già copiati, salto: %s", destination)
        return destination

    shutil.copy2(
        subtitles_path,
        destination
    )

    logger.info("File sottotitoli copiato in output: %s", destination)

    return destination


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
    copied_subtitles_path: Path | None = None
    subtitles_paths: list[Path] = []
    copied_subtitles_paths: list[Path] = []
    subtitle_languages: list[str] = []
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

    if options.write_frames or options.write_phrase_files or options.copy_subtitles:
        try:
            subtitle_tracks = find_subtitle_tracks_for_video(
                video_path=video_path,
                options=options
            )

            if not subtitle_tracks:
                logger.info("Nessun file sottotitoli trovato per: %s", video_path)
            else:
                logger.info("File sottotitoli trovati per %s: %s", video_path.name, len(subtitle_tracks))

                for subtitle_track in subtitle_tracks:
                    subtitles_paths.append(subtitle_track.path)
                    subtitle_languages.append(subtitle_track.language_code)

                    if subtitles_path is None:
                        subtitles_path = subtitle_track.path

                    if options.copy_subtitles:
                        copied = copy_subtitles_to_output(
                            subtitles_path=subtitle_track.path,
                            video_output_dir=video_output_dir,
                            options=options,
                            logger=logger
                        )
                        copied_subtitles_paths.append(copied)

                        if copied_subtitles_path is None:
                            copied_subtitles_path = copied

                    if options.write_frames or options.write_phrase_files:
                        lang_frame_paths, lang_phrase_paths, subtitle_errors = process_subtitles_for_video(
                            video_path=video_path,
                            subtitle_track=subtitle_track,
                            video_output_dir=video_output_dir,
                            options=options,
                            logger=logger
                        )
                        frame_paths.extend(lang_frame_paths)
                        phrase_paths.extend(lang_phrase_paths)
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
        copied_subtitles_path=copied_subtitles_path,
        subtitles_paths=subtitles_paths,
        copied_subtitles_paths=copied_subtitles_paths,
        subtitle_languages=subtitle_languages,
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
    write_ogg: bool = False,
    write_frames: bool = True,
    write_phrase_files: bool = True,
    copy_subtitles: bool = True,
    per_video_subdir: bool = True,
    audio_subdir: str = "audio",
    frames_subdir: str = "frames",
    phrases_subdir: str = "phrases",
    logs_subdir: str = "logs",
    mp3_quality: int = 2,
    ogg_quality: int = 5,
    jpg_quality: int = 8,
    frame_max_width: int = 480,
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

    write_mp3, write_ogg, write_frames, write_phrase_files, copy_subtitles:
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
        copy_subtitles=copy_subtitles,
        per_video_subdir=per_video_subdir,
        audio_subdir=audio_subdir,
        frames_subdir=frames_subdir,
        phrases_subdir=phrases_subdir,
        logs_subdir=logs_subdir,
        mp3_quality=mp3_quality,
        ogg_quality=ogg_quality,
        jpg_quality=jpg_quality,
        frame_max_width=frame_max_width,
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
            copy_subtitles=options.copy_subtitles,
            per_video_subdir=options.per_video_subdir,
            jpg_quality=options.jpg_quality,
            frame_max_width=options.frame_max_width,
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
