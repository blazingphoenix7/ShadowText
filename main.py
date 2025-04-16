import os
import ffmpeg
import whisper
import argparse
import tempfile
from helpers import get_filename, parse_bool, save_srt_file

import warnings
warnings.filterwarnings("ignore")


def run_subtitle_generator():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # Defining arguments
    parser.add_argument("media_files", nargs="+", type=str, help="List of video file paths to process.")
    parser.add_argument("--model_type", default="small", choices=whisper.available_models(), help="Select the Whisper model.")
    parser.add_argument("--output_folder", "-o", type=str, default=".", help="Directory for saving generated files.")
    parser.add_argument("--create_srt", type=parse_bool, default=False, help="Generate .srt subtitle files.")
    parser.add_argument("--srt_only", type=parse_bool, default=False, help="Only create .srt files without overlaying subtitles on video.")
    parser.add_argument("--verbose", type=parse_bool, default=False, help="Show processing logs.")
    parser.add_argument("--action", type=str, default="transcribe", choices=["transcribe", "translate"], help="Transcription or translation of audio.")
    parser.add_argument("--language", type=str, default="auto", 
                        choices=["auto", "en", "es", "fr", "de", "zh", "ja", "ko", "it", "pt", "ru", "ar"], 
                        help="Specify the audio language. If not set, the language is detected automatically.")

    args = parser.parse_args().__dict__
    
    # Extract and prepare key arguments
    selected_model = args.pop("model_type")
    output_directory = args.pop("output_folder")
    create_srt = args.pop("create_srt")
    srt_only_mode = args.pop("srt_only")
    language_choice = args.pop("language")
    
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)
    
    # Handle model-specific language constraints
    if selected_model.endswith(".en"):
        warnings.warn(f"The model {selected_model} supports only English.")
        args["language"] = "en"
    elif language_choice != "auto":
        args["language"] = language_choice
    
    model = whisper.load_model(selected_model)

    # Remove the `action` argument since Whisper doesn't expect it
    args.pop("action", None)

    audio_files = extract_audio_from_videos(args.pop("media_files"))
    subtitle_data = generate_subtitles(audio_files, create_srt or srt_only_mode, output_directory, lambda audio_path: model.transcribe(audio_path, **args))

    if srt_only_mode:
        return

    for video_path, srt_filepath in subtitle_data.items():
        final_video_path = os.path.join(output_directory, f"{get_filename(video_path)}.mp4")

        print(f"Embedding subtitles in {get_filename(video_path)}...")

        video_stream = ffmpeg.input(video_path)
        audio_stream = video_stream.audio

        ffmpeg.concat(
            video_stream.filter('subtitles', srt_filepath, force_style="OutlineColour=&H40000000,BorderStyle=3"),
            audio_stream, v=1, a=1
        ).output(final_video_path).run(quiet=True, overwrite_output=True)

        print(f"Completed video saved at {os.path.abspath(final_video_path)}.")

def extract_audio_from_videos(file_paths):
    temp_directory = tempfile.gettempdir()
    audio_output_paths = {}

    for video_path in file_paths:
        print(f"Extracting audio from {get_filename(video_path)}...")
        temp_audio_path = os.path.join(temp_directory, f"{get_filename(video_path)}.wav")

        ffmpeg.input(video_path).output(
            temp_audio_path, acodec="pcm_s16le", ac=1, ar="16000"
        ).run(quiet=True, overwrite_output=True)

        audio_output_paths[video_path] = temp_audio_path

    return audio_output_paths

def generate_subtitles(audio_files, create_srt_file, output_folder, transcriber):
    subtitle_paths = {}

    for original_path, audio_path in audio_files.items():
        srt_save_path = output_folder if create_srt_file else tempfile.gettempdir()
        srt_file_path = os.path.join(srt_save_path, f"{get_filename(original_path)}.srt")

        print(f"Creating subtitles for {get_filename(original_path)}. Please wait...")

        warnings.filterwarnings("ignore")
        transcription_result = transcriber(audio_path)
        warnings.filterwarnings("default")

        with open(srt_file_path, "w", encoding="utf-8") as srt_file:
            save_srt_file(transcription_result["segments"], file=srt_file)

        subtitle_paths[original_path] = srt_file_path

    return subtitle_paths

if __name__ == '__main__':
    run_subtitle_generator()
