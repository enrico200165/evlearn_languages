import os
import re
from datetime import datetime, timedelta

def clean_timestamp(line):
    """
    Extracts and normalizes the timestamp, discarding any extra attributes.
    Converts '.' to ',' for milliseconds.
    """
    parts = line.strip().split()
    # Keep only start and end timestamps
    if "-->" in parts:
        start = parts[0]
        end = parts[2]
        start_clean = start.replace('.', ',')
        end_clean = end.replace('.', ',')
        return f"{start_clean} --> {end_clean}"
    return None

def strip_tags(text):
    """
    Removes all markup tags like <c>...</c> or <00:...>.
    """
    return re.sub(r"<[^>]+>", "", text).strip()

def parse_timestamp(tstamp):
    """
    Parses an SRT timestamp string into datetime.
    """
    return datetime.strptime(tstamp, "%H:%M:%S,%f")

def duration_seconds(start, end):
    """
    Returns duration in seconds between two timestamp strings.
    """
    return (parse_timestamp(end) - parse_timestamp(start)).total_seconds()

def convert_vtt_to_srt(vtt_path, srt_path, min_duration=0.2):
    """
    Converts a VTT file with complex markup into clean SRT.
    """
    with open(vtt_path, "r", encoding="utf-8") as vtt_file:
        lines = vtt_file.readlines()

    blocks = []
    current_block = {"start": None, "end": None, "lines": []}

    for line in lines:
        stripped = line.strip()

        # Skip headers
        if not stripped or stripped in {"WEBVTT"} or stripped.startswith("Kind:") or stripped.startswith("Language:"):
            continue

        # Timestamp line
        if "-->" in stripped:
            if current_block["start"]:
                # Save previous block
                blocks.append(current_block)
                current_block = {"start": None, "end": None, "lines": []}

            # Clean timestamp
            ts_clean = clean_timestamp(stripped)
            if ts_clean:
                start, _, end = ts_clean.partition(" --> ")
                current_block["start"] = start
                current_block["end"] = end
        else:
            # Text line
            text_clean = strip_tags(stripped)
            if text_clean:
                current_block["lines"].append(text_clean)

    # Save last block
    if current_block["start"]:
        blocks.append(current_block)

    # Merge and filter blocks
    srt_blocks = []
    previous_text = None
    previous_end = None

    for block in blocks:
        start = block["start"]
        end = block["end"]
        text = " ".join(block["lines"])

        if not start or not end or not text:
            continue

        # Skip too short durations
        if duration_seconds(start, end) < min_duration:
            continue

        # Merge with previous if same text and contiguous
        if text == previous_text and previous_end == start:
            # Extend previous block's end time
            srt_blocks[-1]["end"] = end
            previous_end = end
        else:
            srt_blocks.append({"start": start, "end": end, "text": text})
            previous_text = text
            previous_end = end

    # Write SRT file
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        for idx, block in enumerate(srt_blocks, 1):
            srt_file.write(f"{idx}\n")
            srt_file.write(f"{block['start']} --> {block['end']}\n")
            srt_file.write(f"{block['text']}\n\n")

def generate_srt(vtt_dir):
    """
    Process all .vtt files in current directory.
    """
    files = [f for f in os.listdir(vtt_dir) if f.lower().endswith(".vtt")]

    for vtt_file in files:
        vtt_path = os.path.join(vtt_dir, vtt_file)
        srt_file = os.path.splitext(vtt_file)[0] + ".srt"
        srt_path = os.path.join(vtt_dir, srt_file)

        print(f"Processing: {vtt_file}")
        convert_vtt_to_srt(vtt_path, srt_path)
        print(f"  Created: {srt_file}")



if __name__ == "__main__":
    generate_srt("V:\\")
