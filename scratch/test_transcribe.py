import requests
import os

# Create a dummy webm file (just some bytes to see if whisper tries to run ffmpeg)
with open('dummy.webm', 'wb') as f:
    f.write(b'\x1a\x45\xdf\xa3\x93\x42\x82\x88\x6d\x61\x74\x72\x6f\x73\x6b\x61') # WebM header

try:
    with open('dummy.webm', 'rb') as f:
        r = requests.post('http://127.0.0.1:5000/transcribe', files={'audio': f})
        print(r.json())
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists('dummy.webm'):
        os.remove('dummy.webm')
