# YouTube Video Translation Tool

# Overview

This GitHub repository contains a Python project that utilizes the Streamlit library to create a web application for translating YouTube videos. The application downloads YouTube videos, extracts their audio, transcribes the audio to text, translates the text from English to French, and then converts the translated text back to speech. The final output is a video with the translated audio track. This project leverages various libraries, including pytube, youtube_transcript_api, moviepy, whisper, transformers, pysrt, TTS, and pydub.


# Features

Download YouTube videos using the video's URL.
Extract audio from video files.
Transcribe audio to text using the Whisper model.
Translate text from English to French using MarianMT models.
Convert translated text back to speech.
Merge the translated audio with the original video.
Package and download the translated video and all intermediate files as a zip file.
Installation


# Install Libraries
pip install streamlit pandas pytube youtube_transcript_api moviepy whisper transformers pysrt TTS mutagen pydub torch

note: Ensure you have FFmpeg installed in your system as it is required by moviepy.


# Usage

To run the application, navigate to the project directory and execute the following command:

streamlit run <script_name>.py
Replace <script_name>.py with the actual name of the Python script.

**Start the application:** After running the command, Streamlit will start the application and provide a local URL to access it.
**Enter the YouTube video URL:** On the application's interface, input the URL of the YouTube video you wish to translate.
**Process the video:** Click the "Process Video" button to start the translation process. The application will display progress updates as it processes the video.
**Download translated files:** Once processing is complete, a download button will appear, allowing you to download a zip file containing the translated video and all intermediate files. 
