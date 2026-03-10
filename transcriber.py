import os
import re
import whisper
import traceback
from datetime import datetime

def format_transcript(text: str) -> str:
    """
    Format transcript by replacing multiple spaces with newlines and organizing into notes.
    """
    # Replace sequences of two or more spaces (pause markers) with a newline
    out = re.sub(r" {2,}", "\n", text.strip())
    
    # Create better paragraph structure at sentence boundaries
    out = re.sub(r'(\.\s+)([A-Z])', r'.\n\n\1\2', out)
    
    # Collapse multiple blank lines to at most two
    out = re.sub(r"\n{3,}", "\n\n", out)
    
    # Add better formatting: trim excess spaces on each line
    lines = out.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # Add spacing between natural breaks
    formatted_lines = []
    for i, line in enumerate(lines):
        formatted_lines.append(line)
        
        # Add extra line break after sentences that end with period/exclamation/question
        if i < len(lines) - 1 and re.search(r'[.!?]$', line):
            if not re.match(r'^[a-z]', lines[i+1]):
                formatted_lines.append('')
    
    return '\n'.join(formatted_lines)

class AudioTranscriber:
    """Handles audio transcription using Whisper with pause detection."""
    
    def __init__(self, pause_threshold_seconds=0.8, progress_callback=None):
        self.pause_threshold = pause_threshold_seconds
        self.models = {}  # Cache loaded models
        self.current_model_name = None
        self.progress_callback = progress_callback
        
    def get_model(self, model_name="base"):
        """Get or load a Whisper model."""
        if model_name not in self.models:
            print(f"Loading Whisper model '{model_name}'...")
            # Disable fp16 for CPU compatibility, force CPU usage
            self.models[model_name] = whisper.load_model(model_name, device="cpu")
        return self.models[model_name]
    
    def transcribe(self, audio_path, model_name="base", language="en"):
        """
        Transcribe audio file and detect pauses.
        """
        if not os.path.exists(audio_path):
            return False, f"Audio file not found: {audio_path}", {}
        
        try:
            model = self.get_model(model_name)
            
            # Transcribe with detailed output to access segments
            result = model.transcribe(
                audio_path,
                language=language,
                fp16=False,
                verbose=False
            )
            
            # Extract segments for pause detection
            segments = result.get("segments", [])
            transcript = self._format_with_pauses(segments)
            
            segments_data = {
                "segments": segments,
                "language": result.get("language"),
                "duration": result.get("duration")
            }
            
            return True, transcript, segments_data
            
        except Exception as e:
            error_msg = f"Transcription error: {str(e)}\n{traceback.format_exc()}"
            return False, error_msg, {}
    
    def _format_with_pauses(self, segments):
        """
        Format transcript with line breaks for pauses.
        """
        if not segments:
            return ""
        
        formatted_lines = []
        current_line = ""
        
        for i, segment in enumerate(segments):
            text = segment.get("text", "").strip()
            if not text:
                continue
            
            # Check if there's a pause before this segment
            if i > 0:
                prev_end = segments[i - 1].get("end", 0)
                current_start = segment.get("start", 0)
                pause_duration = current_start - prev_end
                
                # If pause exceeds threshold, start a new line
                if pause_duration > self.pause_threshold:
                    if current_line:
                        formatted_lines.append(current_line.strip())
                    current_line = text
                else:
                    current_line += " " + text
            else:
                current_line = text
        
        # Add the last line
        if current_line:
            formatted_lines.append(current_line.strip())
        
        return "\n".join(formatted_lines)
