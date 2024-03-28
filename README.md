# YouTube Video Translator Project README

Welcome to the YouTube Video Translator project! This Python application utilizes Streamlit for a user-friendly web interface, automating the translation of YouTube videos into French. The project streamlines and automates the process of downloading videos, extracting audio, transcribing the audio to text, translating the text, converting the translated text back into speech, and merging this new audio with the original video.

## Project Purpose
The YouTube Video Translator aims to enhance accessibility, support educational content in multiple languages, and aid in content localization. By automating the translation process, this project opens up a world of content for French-speaking audiences, making information and education more accessible. Also this was a part of my final project in CSGY-6613: Introduction to Artificial Intelligence under Prof. Pantelis Monogioudis at NYU.

## Core Functionality

**Download YouTube Videos:** Utilizes pytube to download videos.

**Extract Audio:** Uses moviepy to separate audio from video.

**Transcribe Audio:** Employs the whisper model to convert audio to text.

**Translate Text:** Leverages MarianMT model from transformers for translating English text to French.

**Text-to-Speech Conversion:** Converts translated text into speech using TTS.

**Merge Audio with Video:** Reintegrates the new audio track with the original video file using moviepy.

**Comprehensive Web Interface:** Built with streamlit, offering an intuitive platform for users to translate videos easily.


## Libraries Used
This project utilizes several Python libraries, including pytube, youtube_transcript_api, moviepy, whisper, transformers, pysrt, TTS, mutagen, pydub, and zipfile.

## Setup Instructions
1. Clone the Repository:
```bash
git clone https://github.com/blazingphoenix7/YouTube-Video-Translation.git
```
2. Create a Virtual Environment:
```bash
python3 -m venv env
env\Scripts\activate  #On Mac, use source env/bin/activate
```
3. Install the necessary dependencies.
  
4. Run the Streamlit Application:
```bash
streamlit run app.py
```

## Navigating the Streamlit Interface
**Enter the YouTube Video URL:** Input the URL of the video you wish to translate.

**Process the Video:** Click on the "Process Video" button to start the translation process.

**Download Translated Files:** After processing, download the zip file containing the translated video and all intermediate files.


## Example Input and Output
**Input:** YouTube video URL.

**Output:** 
  1. You can view the English to French translation timestamp after timestamp of the video of the website itself.
  2. A zip file containing the original video, the transcribed SRT files (original and translated), the translated speech audio file, and the final video with the translated audio track.


## Troubleshooting
Ensure all dependencies are correctly installed.

Check the video URL for accuracy.

For large videos, the process might take longer. Be patient and monitor the progress bar.


## Customizing Translation Languages
This project is designed with flexibility in mind, allowing users to easily adapt the application to translate videos into languages other than French. By following a few simple steps, you can modify the source code to accommodate any target language supported by the MarianMT model.

## Steps to Change the Translation Language:
1. **Locate the Translation Function:**
Within the ipynb file, find the function responsible for translating text. This function utilizes the MarianMTModel and MarianTokenizer from the transformers library.

2. **Modify the Model and Tokenizer:**
Replace the model_name variable in the get_model function with the appropriate model name for your desired language pair. Marian models follow a naming convention like **"Helsinki-NLP/opus-mt-{src}-{tgt}"**, where **{src}** is the source language code and **{tgt}** is the target language code. For example, to translate from English to Spanish, you would use **"Helsinki-NLP/opus-mt-en-es"**.

```bash
# Example for changing to English to Spanish translation
model_name = "Helsinki-NLP/opus-mt-en-es"
t = MarianTokenizer.from_pretrained(model_name)
m = MarianMTModel.from_pretrained(model_name).to(device)  # Ensure to use the correct device
```

3. **Adjust the Text-to-Speech (TTS) Language:**
If you're changing the translation language, ensure to modify the TTS language accordingly. Locate the TTS API initialization and change the model_name to match your target language's TTS model.
```bash
# Example for changing TTS to Spanish
api = TTS(model_name="tts_models/es/your_model_name").to("cuda")
```
Note: You'll need to replace "tts_models/es/your_model_name" with the actual path to the TTS model for your target language, if available.

4. **Update Language-Specific Settings:**
Depending on the target language, you may need to adjust language-specific settings such as encoding, punctuation rules, or specific API parameters related to the TTS and translation models.

5. **Test Your Changes:**
After making the necessary modifications, test the application with a video to ensure the translation and TTS conversion work as expected for the new language.


## Additional Tips:
**Explore Model Availability:** Before changing the language, verify that MarianMT and TTS models are available for your desired language pair.
**Language Codes:** Familiarize yourself with ISO language codes as they are required for specifying the source and target languages in model names.
**Community Models:** For languages not directly supported by MarianMT or TTS models, look for community-contributed models that might suit your needs.


## Contributions and Feedback
I welcome contributions to improve language support, enhance accuracy, and extend the project's capabilities. Please feel free to fork the repository, make your changes, and submit a pull request. For bugs, suggestions, or collaboration, contact me at adm8315@nyu.edu.


## Support and Star Us!
If you find this project useful, please consider starring it on GitHub to help it gain more visibility. Your support is greatly appreciated!
