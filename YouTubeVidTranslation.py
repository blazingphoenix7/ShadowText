# Import necessary libraries
import streamlit as sl
import pandas as pd
import os
from io import TextIOWrapper
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
import moviepy.editor as mpy
import whisper
from whisper.utils import get_writer
from transformers import MarianMTModel, MarianTokenizer
import pysrt
from TTS.api import TTS
from mutagen.wave import WAVE
from pydub import AudioSegment
import time
import shutil
from moviepy.editor import VideoFileClip, AudioFileClip
import zipfile
import torch 


# Function to apply custom CSS styles
def apply_style():
    # Markdown to inject CSS styles
    sl.markdown(
        """
        <style>
            .main {
                padding: 20px;
            }
            .title {
                font-size: 36px;
                font-weight: bold;
                margin-bottom: 20px;
            }
            .sub-title {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .file-input {
                margin-bottom: 10px;
            }
            .result {
                margin-top: 20px;
            }
        </style>
        """,
        unsafe_allow_html=True,  # Allow HTML in markdown
    )

# Function to fetch video from YouTube and download it
def fetch_video(url_list, output_path, output_path_srt):
    for u in url_list:
        yt = YouTube(u)  # Create YouTube object
        video_stream = yt.streams.get_highest_resolution()  # Get highest resolution stream
        vid_id = yt.video_id  # Get video id
        video_stream.download(output_path, filename=f"{vid_id}.mp4")  # Download video
        transcript = YouTubeTranscriptApi.get_transcript(vid_id)  # Get transcript

        # Write the transcript to a .srt file
        with open(f"{output_path_srt}/{vid_id}.srt", 'w', encoding='utf-8') as f:
            for segment in transcript:
                f.write(f"{segment['start']} --> {segment['start']+segment['duration']}\n")
                f.write(f"{segment['text']}\n\n")

    return vid_id

# Function to extract audio from video files
def extract_audio(video_files, audio_path):
    for vf in video_files:
        n = vf.split('/')
        new_name = audio_path + '/' + n[-1].replace('4', '3')  # Create new name for audio file
        if os.path.isfile(new_name):
            continue  # If file already exists, skip
        clip = mpy.VideoFileClip(vf)  # Create VideoFileClip object
        clip.audio.write_audiofile(new_name)  # Write audio to file

    return new_name

# Function to transcribe audio files
def transcribe_audio(audio_files, output_dir):
    whisper_model = whisper.load_model("base")  # Load whisper model
    for af in audio_files:
        n = af.split('/')
        srt_name = output_dir + '/' + n[-1].replace(".mp3", ".srt")  # Create new name for .srt file
        if os.path.isfile(srt_name):
            continue  # If file already exists, skip
        res = whisper_model.transcribe(af)  # Transcribe audio file
        srt_writer = get_writer("srt", output_dir)  # Get .srt writer
        srt_writer(res, srt_name)  # Write transcription to .srt file

    return srt_name

# Function to get translation model
def get_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if os.path.isdir("./pretrained_model_en_fr.pt"):
        print("Model exists")
        m = MarianMTModel.from_pretrained("./pretrained_model_en_fr.pt").to(device)  # Move model to GPU if available
        t = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-fr")
    else:
        print("Downloading the model")
        model_name = "Helsinki-NLP/opus-mt-en-fr"
        t = MarianTokenizer.from_pretrained(model_name)
        m = MarianMTModel.from_pretrained(model_name).to(device)  # Move model to GPU if available
        m.save_pretrained("./pretrained_model_en_fr.pt")

    return m, t

# Function to translate text
def translate(en_text, model, tokenizer):
    device = model.device  # Get the device model is on
    sl = len(en_text)
    nb = (sl // 512) + (1 if sl % 512 != 0 else 0)  # Calculate number of batches
    fr_txt = ''
    for i in range(nb):
        input_ids = tokenizer.encode(en_text[i * 512:(i + 1) * 512], return_tensors="pt").to(device)  # Move input tensors to the same device as model
        output_ids = model.generate(input_ids)  # Generate translation
        out_txt = tokenizer.decode(output_ids[0], skip_special_tokens=True)  # Decode translation
        fr_txt += out_txt  # Append translation to output

    return fr_txt


# Function to translate a list of text files
def translate_text_list(text_list, output_dir):
    model, tokenizer = get_model()  # Get model and tokenizer
    for t in text_list:
        n = t.split('/')[-1]
        fr_srt = output_dir + '/' + n[:-3] + "_fr" + n[-4:]  # Create new name for French .srt file
        if os.path.isfile(fr_srt):
            continue  # If file already exists, skip
        srt = pysrt.open(t)  # Open .srt file
        for sub in srt:
            sub.text = translate(sub.text, model, tokenizer)  # Translate text
        srt.save(fr_srt, encoding='utf-8')  # Save French .srt file

    return fr_srt

# Function to read the content of a .srt file
def read_srt_content(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    subs = []
    for i in range(0, len(lines), 4):
        idx = lines[i].strip()  # Get index
        ts = lines[i + 1].strip()  # Get timestamp
        txt = lines[i + 2].strip()  # Get text
        subs.append({'Index': idx, 'Timestamp': ts, 'Text': txt})  # Append to list

    return subs

# Function to add delay to an audio file and export it
def delay_and_export(input_wav, output_wav, delay_seconds):
    audio = AudioSegment.from_wav(input_wav)  # Load audio
    delay = AudioSegment.silent(duration=int(delay_seconds * 1000))  # Create delay
    output_audio = audio + delay  # Add delay to audio
    output_audio.export(output_wav, format="wav")  # Export audio

# Function to generate audio files from a .srt file
def generate_audio(frl, api, output_dir):
    srt = pysrt.open(frl)  # Open .srt file
    i = 0
    for sub in srt:
        api.tts_to_file(sub.text, file_path=output_dir+'/'+str(i)+".wav")  # Generate audio
        audio = WAVE(output_dir+'/'+str(i)+".wav")  # Load audio
        audio_info = audio.info  # Get audio info
        length = int(audio_info.length)  # Get audio length
        if length < sub.duration.seconds:  # If audio is shorter than expected
            delay_and_export(output_dir+'/'+str(i)+".wav", output_dir+'/'+str(i)+".wav", sub.duration.seconds - length)  # Add delay
        i += 1

# Function to merge audio files
def merge_audio_files(frl, audio_output_dir, merged_output_dir):
    wav_files = [f for f in os.listdir(audio_output_dir) if f.endswith('.wav')]  # Get list of .wav files
    merged_audio = AudioSegment.silent(duration=0)  # Create silent audio segment

    for wav_file in wav_files:
        f_path = os.path.join(audio_output_dir, wav_file)  # Get file path
        audio_segment = AudioSegment.from_wav(f_path)  # Load audio
        merged_audio += audio_segment  # Add audio to merged audio
    n = frl.split('/')
    merged_audio.export(merged_output_dir+"/"+n[-1]+".wav", format="wav")  # Export merged audio
    print("DONE WITH "+merged_output_dir+"/"+n[-1]+".wav")
    time.sleep(5)
    shutil.rmtree(audio_output_dir)  # Remove audio output directory
    os.mkdir(audio_output_dir)  # Create audio output directory
    return merged_output_dir+"/"+n[-1]+".wav"  # Return path of merged audio

# Function to convert text to audio
def text_to_audio(fr_list, api):
    base_dir = "project_data"
    audio_output_dir = os.path.join(base_dir, "fr_srt_mp3")  # Updated to relative path
    merged_output_dir = os.path.join(base_dir, "fr_srt_wav")  # Updated to relative path

    for frl in fr_list:  # Iterate over the list of .srt files
        print(frl)  # Print the current .srt file
        generate_audio(frl, api, audio_output_dir)  # Generate audio files from the .srt file
        time.sleep(5)  # Wait for 5 seconds
        speech_file = merge_audio_files(frl, audio_output_dir, merged_output_dir)  # Merge the audio files
    return speech_file  # Return the path of the merged audio file

# Function to merge video and audio
def merge_media(video_path, audio_path, output_path):
    video_clip = VideoFileClip(video_path)  # Load the video clip
    audio_clip = AudioFileClip(audio_path)  # Load the audio clip

    video_clip = video_clip.set_audio(audio_clip)  # Set the audio of the video clip

    video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')  # Write the video file with the new audio

# Function to zip files
def zip_files(file_paths, output_zip):
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for file in file_paths:
            zipf.write(file, os.path.basename(file))

def main():
    apply_style()  # Apply custom CSS styles

    # Display the main title of the project
    sl.markdown("<div class='main'>", unsafe_allow_html=True)
    sl.markdown("<div class='title'>YouTube Video Translation: </div>", unsafe_allow_html=True)

    # Base directory for storing data
    base_dir = "project_data"  

    # Define paths for the videos, subtitles, and audio files
    streamlit_video_path = os.path.join(base_dir, "input_videos")
    streamlit_srt_path = os.path.join(base_dir, "input_videos_srt")
    streamlit_extract_audio_path = os.path.join(base_dir, "streamlit_extract_audio_path")
    audio_og_srt_path = os.path.join(base_dir, "audio_og_srt_path")
    audio_fr_srt_path = os.path.join(base_dir, "audio_fr_srt_path")

    audio_output_dir = os.path.join(base_dir, "fr_srt_mp3")
    merged_output_dir = os.path.join(base_dir, "fr_srt_wav")

    # Check if directories exist, if not create them
    directories = [streamlit_video_path, streamlit_srt_path, streamlit_extract_audio_path, 
                   audio_og_srt_path, audio_fr_srt_path, audio_output_dir, merged_output_dir]
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True) 

    # Display text
    sl.markdown("<div class='sub-title'>Once done processing, scroll to the bottom of the page to download the translated </div>", unsafe_allow_html=True)
    sl.markdown("<div class='sub-title'>Aaryan Mehta </div>", unsafe_allow_html=True)


    # Get the URL of the video from the user
    video_url = sl.text_input("Enter URL:", "")
    process_button = sl.button("Process Video")

    # If the user clicks the "Process Video" button and a URL is provided
    if process_button and video_url:
        progress_bar = sl.progress(0)  # Initialize a progress bar

        # Fetch the video from the URL and save it to the specified path
        video_id = fetch_video([video_url], streamlit_video_path, streamlit_srt_path)
        progress_bar.progress(20)  # Update progress bar to 20%

        # Extract the audio from the video
        audio_name = extract_audio([f"{streamlit_video_path}/{video_id}.mp4"], streamlit_extract_audio_path)
        progress_bar.progress(40)  # Update progress bar to 40%

        # Transcribe the audio to text
        audio_og_srt_name = transcribe_audio([audio_name], audio_og_srt_path)
        progress_bar.progress(60)  # Update progress bar to 60%

        # Translate the transcribed text
        audio_fr_srt_name = translate_text_list([audio_og_srt_name], audio_fr_srt_path)
        progress_bar.progress(80)  # Update progress bar to 80%

        audio_fr_srt_name = translate_text_list([audio_og_srt_name], audio_fr_srt_path)
        progress_bar.progress(100)  # Update progress bar to 100%
        
        # Display the video ID
        sl.write(f"Video ID: {video_id}")

        # Extract the audio from the video
        audio_name = extract_audio([f"{streamlit_video_path}/{video_id}.mp4"], streamlit_extract_audio_path)
        # Display the name of the audio file
        sl.write(f"Audio File: {audio_name}")

        # Transcribe the audio to text
        audio_og_srt_name = transcribe_audio([audio_name], audio_og_srt_path)
        # Display the name of the original SRT file
        sl.write(f"Original SRT File: {audio_og_srt_name}")

        # Translate the transcribed text
        audio_fr_srt_name = translate_text_list([audio_og_srt_name], audio_fr_srt_path)
        # Display the name of the translated SRT file
        sl.write(f"Translated SRT File: {audio_fr_srt_name}")

        # Read the content of the original and translated SRT files
        subtitles_1 = read_srt_content(audio_og_srt_name)
        subtitles_2 = read_srt_content(audio_fr_srt_name)

        # Merge the original and translated subtitles into a DataFrame
        merged_df = pd.merge(pd.DataFrame(subtitles_1), pd.DataFrame(subtitles_2), on='Timestamp', how='outer',
                            suffixes=('Speech to text original', 'Speech to text after translation'))

        # Display the merged DataFrame
        sl.header("TTL")
        sl.table(merged_df)

        # Initialize the text-to-speech API
        api = TTS(model_name="tts_models/fr/css10/vits").to("cuda")
        # Convert the translated text to speech
        speech_file = text_to_audio([audio_fr_srt_name], api)
        # Convert the WAV file to MP3
        f_name = speech_file.replace(".wav", ".mp3")
        AudioSegment.from_wav(speech_file).export(f_name, format="mp3")
        # Display the name of the translated text-to-speech file
        sl.write(f"Translated text to speech File: {f_name}")


        # Merge the original video with the translated audio
        video_with_translated_audio = f"{streamlit_video_path}/{video_id}_translated.mp4"
        merge_media(f"{streamlit_video_path}/{video_id}.mp4", f_name, video_with_translated_audio)

        # List of files to be zipped
        files_to_zip = [f"{streamlit_video_path}/{video_id}.mp4",
                        audio_og_srt_name,
                        audio_fr_srt_name,
                        f_name,
                        video_with_translated_audio]

        # Output zip file path
        zip_file = f"{streamlit_video_path}/translated_files_{video_id}.zip"

        # Create a zip file
        zip_files(files_to_zip, zip_file)

        # Add a download button for the zip file
        with open(zip_file, "rb") as file:
            btn = sl.download_button(
                label="Download Translated Files",
                data=file,
                file_name=f"translated_files_{video_id}.zip",
                mime="application/zip"
            )

if __name__ == "__main__":
    main()
