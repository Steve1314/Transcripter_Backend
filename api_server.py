from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from werkzeug.utils import secure_filename
from transcriber import AudioTranscriber, format_transcript
import tempfile

import subprocess

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
KEYS_FILE = "keys.json"

def get_ffmpeg_path():
    """Get the path to ffmpeg executable."""
    # Check current dir, parent dir, and system PATH
    cwd = os.getcwd()
    parent = os.path.dirname(cwd)
    
    search_dirs = [cwd, parent]
    
    for base in search_dirs:
        local_paths = [
            os.path.join(base, "ffmpeg", "ffmpeg.exe"),
            os.path.join(base, "ffmpeg", "bin", "ffmpeg.exe"),
            os.path.join(base, "ffmpeg", "ffmpeg"),
            os.path.join(base, "ffmpeg", "bin", "ffmpeg"),
        ]
        for path in local_paths:
            if os.path.exists(path):
                return path
    return "ffmpeg"

# Add ffmpeg to PATH if found locally
ffmpeg_path = get_ffmpeg_path()
if ffmpeg_path != "ffmpeg":
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

transcriber = AudioTranscriber()

def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    return {}

def require_api_key(f):
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        keys = load_keys()
        if api_key not in keys:
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "EchoLock API"})

@app.route('/transcribe', methods=['POST'])
@require_api_key
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    model_name = request.form.get('model', 'base')
    language = request.form.get('language', 'en')
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp:
        file.save(temp.name)
        temp_path = temp.name
    
    try:
        success, result, segments_data = transcriber.transcribe(temp_path, model_name=model_name, language=language)
        
        if success:
            formatted_text = format_transcript(result)
            return jsonify({
                "success": True,
                "transcript": formatted_text,
                "segments": segments_data.get("segments", []),
                "duration": segments_data.get("duration"),
                "language": segments_data.get("language")
            })
        else:
            return jsonify({"success": False, "error": result}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    # You may want to change host to '0.0.0.0' for remote access
    app.run(host='0.0.0.0', port=5000, debug=False)
