import requests
import os
import sys

def test_transcribe(api_key, audio_file_path, model="base", url="http://127.0.0.1:5000/transcribe"):
    # url = "https://transcripter-backend.onrender.com/transcribe"
    headers = {
        "X-API-Key": api_key
    }
    files = {
        "file": open(audio_file_path, "rb")
    }
    data = {
        "model": model
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            print("Transcription Successful!")
            print("-" * 30)
            print(response.json()["transcript"])
            print("-" * 30)
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_api.py <API_KEY> <AUDIO_FILE_PATH> [MODEL] [URL]")
        sys.exit(1)
    
    key = sys.argv[1]
    audio_path = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "base"
    url = sys.argv[4] if len(sys.argv) > 4 else "http://127.0.0.1:5000/transcribe"
    
    test_transcribe(key, audio_path, model, url)
