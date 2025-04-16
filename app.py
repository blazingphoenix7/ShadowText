from flask import Flask, request, jsonify, send_file, render_template
import os
import tempfile
import uuid
import threading
import whisper
import ffmpeg
import subprocess
from werkzeug.utils import secure_filename
import logging
from helpers import get_filename, save_srt_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Configuration
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'videotext_uploads')
RESULT_FOLDER = os.path.join(tempfile.gettempdir(), 'videotext_results')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'mkv', 'webm'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Dictionary to store job status
jobs = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check file type
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate unique ID for the job
    job_id = str(uuid.uuid4())
    
    # Create job folder
    job_folder = os.path.join(app.config['RESULT_FOLDER'], job_id)
    os.makedirs(job_folder, exist_ok=True)
    
    # Save the file
    filename = secure_filename(file.filename)
    file_path = os.path.join(job_folder, filename)
    file.save(file_path)
    
    # Get options from request
    options = {
        'model_type': request.form.get('model_type', 'small'),
        'language': request.form.get('language', 'auto'),
        'action': request.form.get('action', 'transcribe'),
        'create_srt': request.form.get('create_srt', 'false').lower() == 'true',
        'srt_only': request.form.get('srt_only', 'false').lower() == 'true',
    }
    
    # Initialize job status
    jobs[job_id] = {
        'status': 'queued',
        'progress': 0,
        'message': 'Job queued',
        'file_path': file_path,
        'options': options,
        'result_srt': None,
        'result_video': None
    }
    
    # Start processing in a separate thread
    threading.Thread(target=process_video, args=(job_id, file_path, options, job_folder)).start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'message': 'File uploaded successfully. Processing started.'
    }), 200

@app.route('/api/status/<job_id>', methods=['GET'])
def job_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id]), 200

@app.route('/api/download/<job_id>/<file_type>', methods=['GET'])
def download_file(job_id, file_type):
    if job_id not in jobs or jobs[job_id]['status'] != 'completed':
        return jsonify({'error': 'Job not found or not completed'}), 404
    
    job = jobs[job_id]
    
    if file_type == 'srt' and job['result_srt']:
        return send_file(job['result_srt'], as_attachment=True)
    elif file_type == 'video' and job['result_video']:
        return send_file(job['result_video'], as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

def extract_audio(video_path, job_id):
    """Extract audio from video file"""
    jobs[job_id]['status'] = 'extracting_audio'
    jobs[job_id]['progress'] = 10
    jobs[job_id]['message'] = 'Extracting audio from video'
    
    temp_audio_path = os.path.join(os.path.dirname(video_path), f"{get_filename(video_path)}.wav")
    
    try:
        ffmpeg.input(video_path).output(
            temp_audio_path, acodec="pcm_s16le", ac=1, ar="16000"
        ).run(quiet=True, overwrite_output=True)
        
        jobs[job_id]['progress'] = 30
        jobs[job_id]['message'] = 'Audio extraction complete'
        
        return temp_audio_path
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['message'] = f'Error extracting audio: {str(e)}'
        raise

def process_video(job_id, video_path, options, job_folder):
    """Process video file with Whisper"""
    try:
        # Extract audio
        audio_path = extract_audio(video_path, job_id)
        
        # Load model
        jobs[job_id]['status'] = 'loading_model'
        jobs[job_id]['progress'] = 40
        jobs[job_id]['message'] = 'Loading transcription model'
        
        model = whisper.load_model(options['model_type'])
        
        # Transcribe audio
        jobs[job_id]['status'] = 'transcribing'
        jobs[job_id]['progress'] = 50
        jobs[job_id]['message'] = 'Transcribing audio'
        
        transcribe_options = {
            'verbose': False
        }
        
        # Set language if not auto
        if options['language'] != 'auto':
            transcribe_options['language'] = options['language']
        
        # Set task based on action
        if options['action'] == 'translate':
            transcribe_options['task'] = 'translate'
        
        transcription_result = model.transcribe(audio_path, **transcribe_options)
        
        jobs[job_id]['progress'] = 70
        jobs[job_id]['message'] = 'Transcription complete'
        
        # Generate SRT file
        srt_file_path = os.path.join(job_folder, f"{get_filename(video_path)}.srt")
        
        with open(srt_file_path, "w", encoding="utf-8") as srt_file:
            save_srt_file(transcription_result["segments"], file=srt_file)
        
        jobs[job_id]['result_srt'] = srt_file_path
        jobs[job_id]['progress'] = 80
        jobs[job_id]['message'] = 'SRT file generated'
        
        # If not SRT only, create video with subtitles
        if not options['srt_only']:
            jobs[job_id]['status'] = 'embedding_subtitles'
            jobs[job_id]['progress'] = 90
            jobs[job_id]['message'] = 'Embedding subtitles in video'
            
            output_video_path = os.path.join(job_folder, f"{get_filename(video_path)}_subtitled.mp4")
            
            try:
                # Using ffmpeg to add subtitles
                subprocess.run([
                    'ffmpeg',
                    '-i', video_path,
                    '-vf', f"subtitles={srt_file_path}:force_style='OutlineColour=&H40000000,BorderStyle=3'",
                    '-c:a', 'copy',
                    output_video_path
                ], check=True)
                
                jobs[job_id]['result_video'] = output_video_path
            except subprocess.CalledProcessError as e:
                logger.error(f"Error embedding subtitles: {e}")
                jobs[job_id]['message'] += '. Error embedding subtitles, but SRT file is available.'
        
        # Update job status
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['message'] = 'Processing complete'
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['message'] = f'Error processing video: {str(e)}'

if __name__ == '__main__':
    app.run(debug=True)