import os
from typing import Iterator, TextIO

def parse_bool(value):
    lowered_value = value.lower()
    boolean_map = {"true": True, "false": False}
    
    if lowered_value in boolean_map:
        return boolean_map[lowered_value]
    else:
        raise ValueError(f"Expected 'true' or 'false', got {value}.")

def format_timecode(seconds: float, include_hours: bool = False):
    assert seconds >= 0, "Expected a non-negative timestamp."
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3600000
    milliseconds -= hours * 3600000

    minutes = milliseconds // 60000
    milliseconds -= minutes * 60000

    seconds = milliseconds // 1000
    milliseconds -= seconds * 1000

    hour_marker = f"{hours:02d}:" if include_hours or hours > 0 else ""
    return f"{hour_marker}{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def save_srt_file(transcription: Iterator[dict], file: TextIO):
    for idx, segment in enumerate(transcription, start=1):
        print(
            f"{idx}\n"
            f"{format_timecode(segment['start'], include_hours=True)} --> "
            f"{format_timecode(segment['end'], include_hours=True)}\n"
            f"{segment['text'].strip().replace('-->', '->')}\n",
            file=file,
            flush=True,
        )

def get_filename(path):
    return os.path.splitext(os.path.basename(path))[0]
