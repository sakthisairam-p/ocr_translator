import os
import uuid
import logging
import tempfile
import torch
import whisper
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from deep_translator import GoogleTranslator
from langdetect import detect
from gtts import gTTS

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder=os.path.abspath(os.path.dirname(__file__)))
CORS(app)

# FIX for Windows Python 3.14+ urllib SSL Error
if 'SSLKEYLOGFILE' in os.environ:
    del os.environ['SSLKEYLOGFILE']

# --- AI MODELS ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE}")

whisper_model = None
def load_whisper():
    global whisper_model
    try:
        logger.info("Loading Whisper 'base' model...")
        whisper_model = whisper.load_model("base", device=DEVICE)
        logger.info("Whisper model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Whisper: {e}")

load_whisper()

# --- LANGUAGES ---
LANG_LIST = [
    {'code': 'en', 'name': 'English'},
    {'code': 'ta', 'name': 'Tamil (தமிழ்)'},
    {'code': 'hi', 'name': 'Hindi (हिन्दी)'},
    {'code': 'ml', 'name': 'Malayalam (മലയാളം)'},
    {'code': 'te', 'name': 'Telugu (తెలుగు)'},
    {'code': 'kn', 'name': 'Kannada (ಕನ್ನಡ)'},
    {'code': 'mr', 'name': 'Marathi (मराठी)'},
    {'code': 'gu', 'name': 'Gujarati (ગુજરાતી)'},
    {'code': 'bn', 'name': 'Bengali (বাংলা)'},
    {'code': 'ur', 'name': 'Urdu (اردو)'},
    {'code': 'pa', 'name': 'Punjabi (ਪੰਜਾਬੀ)'},
    {'code': 'fr', 'name': 'French (Français)'},
    {'code': 'de', 'name': 'German (Deutsch)'},
    {'code': 'es', 'name': 'Spanish (Español)'},
    {'code': 'it', 'name': 'Italian (Italiano)'},
    {'code': 'ja', 'name': 'Japanese (日本語)'},
    {'code': 'ko', 'name': 'Korean (한국어)'},
    {'code': 'zh-CN', 'name': 'Chinese (Simplified)'},
    {'code': 'ru', 'name': 'Russian (Русский)'},
    {'code': 'ar', 'name': 'Arabic (العربية)'},
    {'code': 'pt', 'name': 'Portuguese (Português)'},
    {'code': 'tr', 'name': 'Turkish (Türkçe)'}
]

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/languages')
def get_languages():
    return jsonify(LANG_LIST)

@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        data = request.json
        text = data.get('text', '').strip()
        target = data.get('target', 'en')
        source = data.get('source', 'auto')

        if not text:
            return jsonify({"error": "Empty text"}), 400

        translated = GoogleTranslator(source=source, target=target).translate(text)
        return jsonify({"translated": translated})
    except Exception as e:
        logger.error(f"Translation Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/detect', methods=['POST'])
def detect_lang():
    try:
        data = request.json
        text = data.get('text', '').strip()
        if not text: return jsonify({"code": "", "name": ""})
        
        code = detect(text)
        name = next((l['name'] for l in LANG_LIST if l['code'] == code), code.upper())
        return jsonify({"code": code, "name": name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if whisper_model is None:
        return jsonify({"error": "Whisper model not loaded"}), 503

    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400
        
        audio_file = request.files['audio']
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name

        result = whisper_model.transcribe(tmp_path, fp16=(DEVICE == "cuda"))
        os.remove(tmp_path)

        return jsonify({"text": result['text'].strip(), "language": result.get("language")})
    except Exception as e:
        logger.error(f"Transcription Error: {e}")
        return jsonify({"error": "Audio processing failed. Is FFmpeg installed?"}), 500

@app.route('/tts', methods=['POST'])
def text_to_speech():
    try:
        data = request.json
        text = data.get('text', '')
        lang = data.get('lang', 'en')

        if not text:
            return jsonify({"error": "No text"}), 400

        # Clean lang code for gTTS
        if '-' in lang and lang not in ['zh-CN', 'zh-TW']:
            lang = lang.split('-')[0]

        tts = gTTS(text=text, lang=lang)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tts.save(tmp.name)
            tmp_path = tmp.name

        return send_file(tmp_path, mimetype="audio/mpeg")
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Neural Translator Pro active at http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)