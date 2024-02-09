# # YouTube Video Translation Tool

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

Clone the repository:
bash
Copy code
git clone <repository-url>
Install the required dependencies:
bash
Copy code
pip install streamlit pandas pytube youtube_transcript_api moviepy whisper transformers pysrt TTS mutagen pydub torch
Ensure you have FFmpeg installed in your system as it is required by moviepy.
Usage

To run the application, navigate to the project directory and execute the following command:

bash
Copy code
streamlit run <script_name>.py
Replace <script_name>.py with the actual name of the Python script.

Start the application: After running the command, Streamlit will start the application and provide a local URL to access it.
Enter the YouTube video URL: On the application's interface, input the URL of the YouTube video you wish to translate.
Process the video: Click the "Process Video" button to start the translation process. The application will display progress updates as it processes the video.
Download translated files: Once processing is complete, a download button will appear, allowing you to download a zip file containing the translated video and all intermediate files.
Functions Overview

apply_style(): Applies custom CSS styles to the Streamlit app.
fetch_video(): Downloads the YouTube video and its transcript.
extract_audio(): Extracts the audio from the downloaded video files.
transcribe_audio(): Transcribes audio files to text using the Whisper model.
get_model(), translate(), translate_text_list(): Functions for translating text from English to French.
read_srt_content(): Reads the content of an SRT file.
delay_and_export(), generate_audio(), merge_audio_files(), text_to_audio(): Functions for handling audio files, including text-to-speech conversion and merging audio files.
merge_media(): Merges the original video with the translated audio track.
zip_files(): Packages the video, audio, and transcript files into a zip file for download.
main(): Main function that orchestrates the video translation workflow.
Project Structure

The project is structured to handle video downloading, audio extraction, transcription, translation, text-to-speech conversion, and merging of audio with the original video. It includes error handling and progress tracking to enhance user experience.

Contributing

Contributions to enhance the functionality, improve efficiency, or fix bugs are welcome. Please follow the standard pull request process to contribute to this project.

License

Specify your project's license here, ensuring it aligns with the libraries used.
