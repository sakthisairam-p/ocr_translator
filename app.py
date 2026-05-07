from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from deep_translator import GoogleTranslator
import os
import uuid
import tempfile
import whisper
import logging


app = Flask(__name__)
CORS(app)

# FIX for Windows Python 3.14 urllib SSL Error: Unset SSLKEYLOGFILE
if 'SSLKEYLOGFILE' in os.environ:
    del os.environ['SSLKEYLOGFILE']

# Initialize Logging to see actual errors instead of generic '...'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the lightweight Whisper model globally (it will download approx 140MB on first run)
print("Loading Whisper model...")
whisper_model = whisper.load_model("base")
print("Whisper model loaded!")

# EXHAUSTIVE GLOBAL 130+ LANGUAGES LIST
LANG_LIST = [
    # --- POPULAR & INDIAN REGIONAL ---
    {'code': 'ta', 'name': 'Tamil (தமிழ்)'},
    {'code': 'en', 'name': 'English'},
    {'code': 'hi', 'name': 'Hindi (हिन्दी)'},
    {'code': 'ml', 'name': 'Malayalam (മലയാളം)'},
    {'code': 'te', 'name': 'Telugu (తెలుగు)'},
    {'code': 'kn', 'name': 'Kannada (ಕನ್ನಡ)'},
    {'code': 'mr', 'name': 'Marathi (മরাठी)'},
    {'code': 'gu', 'name': 'Gujarati (ગુજરાતી)'},
    {'code': 'pa', 'name': 'Punjabi (ਪੰਜਾਬੀ)'},
    {'code': 'bn', 'name': 'Bengali (বাংলা)'},
    {'code': 'ur', 'name': 'Urdu (اردو)'},
    {'code': 'as', 'name': 'Assamese (অসমীয়া)'},
    {'code': 'or', 'name': 'Odia (ଓଡ଼ିଆ)'},
    {'code': 'sa', 'name': 'Sanskrit (संस्कृतम्)'},
    {'code': 'bho', 'name': 'Bhojpuri (भोजपुरी)'},
    {'code': 'mai', 'name': 'Maithili (मैथिली)'},
    {'code': 'doi', 'name': 'Dogri (डोगरी)'},
    {'code': 'ks', 'name': 'Kashmiri (کأشُر)'},
    {'code': 'sd', 'name': 'Sindhi (سنڌي)'},
    {'code': 'mni-Mtei', 'name': 'Meiteilon (Manipuri)'},
    {'code': 'lus', 'name': 'Mizo (Mizo ṭawng)'},
    {'code': 'gom', 'name': 'Konkani (कोंकणी)'},

    # --- GLOBAL POPULAR ---
    {'code': 'ar', 'name': 'Arabic (العربية)'},
    {'code': 'fr', 'name': 'French (Français)'},
    {'code': 'de', 'name': 'German (Deutsch)'},
    {'code': 'es', 'name': 'Spanish (Español)'},
    {'code': 'it', 'name': 'Italian (Italiano)'},
    {'code': 'ja', 'name': 'Japanese (日本語)'},
    {'code': 'ko', 'name': 'Korean (한국어)'},
    {'code': 'ru', 'name': 'Russian (Русский)'},
    {'code': 'pt', 'name': 'Portuguese (Português)'},
    {'code': 'zh-CN', 'name': 'Chinese (Simplified)'},
    {'code': 'zh-TW', 'name': 'Chinese (Traditional)'},
    {'code': 'tr', 'name': 'Turkish (Türkçe)'},
    {'code': 'vi', 'name': 'Vietnamese (Tiếng Việt)'},
    {'code': 'th', 'name': 'Thai (ไทย)'},
    {'code': 'id', 'name': 'Indonesian (Bahasa Indonesia)'},
    {'code': 'nl', 'name': 'Dutch (Nederlands)'},
    {'code': 'pl', 'name': 'Polish (Polski)'},

    # --- FULL ALPHABETICAL LIST ---
    {'code': 'af', 'name': 'Afrikaans'}, {'code': 'sq', 'name': 'Albanian'}, {'code': 'am', 'name': 'Amharic'},
    {'code': 'hy', 'name': 'Armenian'}, {'code': 'ay', 'name': 'Aymara'}, {'code': 'az', 'name': 'Azerbaijani'},
    {'code': 'bm', 'name': 'Bambara'}, {'code': 'eu', 'name': 'Basque'}, {'code': 'be', 'name': 'Belarusian'},
    {'code': 'bs', 'name': 'Bosnian'}, {'code': 'bg', 'name': 'Bulgarian'}, {'code': 'ca', 'name': 'Catalan'},
    {'code': 'ceb', 'name': 'Cebuano'}, {'code': 'ny', 'name': 'Chichewa'}, {'code': 'co', 'name': 'Corsican'},
    {'code': 'hr', 'name': 'Croatian'}, {'code': 'cs', 'name': 'Czech'}, {'code': 'da', 'name': 'Danish'},
    {'code': 'dv', 'name': 'Dhivehi'}, {'code': 'eo', 'name': 'Esperanto'}, {'code': 'et', 'name': 'Estonian'},
    {'code': 'ee', 'name': 'Ewe'}, {'code': 'tl', 'name': 'Filipino'}, {'code': 'fi', 'name': 'Finnish'},
    {'code': 'fy', 'name': 'Frisian'}, {'code': 'gl', 'name': 'Galician'}, {'code': 'ka', 'name': 'Georgian'},
    {'code': 'el', 'name': 'Greek'}, {'code': 'gn', 'name': 'Guarani'}, {'code': 'ht', 'name': 'Haitian Creole'},
    {'code': 'ha', 'name': 'Hausa'}, {'code': 'haw', 'name': 'Hawaiian'}, {'code': 'iw', 'name': 'Hebrew'},
    {'code': 'hmn', 'name': 'Hmong'}, {'code': 'hu', 'name': 'Hungarian'}, {'code': 'is', 'name': 'Icelandic'},
    {'code': 'ig', 'name': 'Igbo'}, {'code': 'ilo', 'name': 'Ilocano'}, {'code': 'ga', 'name': 'Irish'},
    {'code': 'jw', 'name': 'Javanese'}, {'code': 'kk', 'name': 'Kazakh'}, {'code': 'km', 'name': 'Khmer'},
    {'code': 'rw', 'name': 'Kinyarwanda'}, {'code': 'kri', 'name': 'Krio'}, {'code': 'ku', 'name': 'Kurdish'},
    {'code': 'ky', 'name': 'Kyrgyz'}, {'code': 'lo', 'name': 'Lao'}, {'code': 'la', 'name': 'Latin'},
    {'code': 'lv', 'name': 'Latvian'}, {'code': 'lt', 'name': 'Lithuanian'}, {'code': 'ln', 'name': 'Lingala'},
    {'code': 'lg', 'name': 'Luganda'}, {'code': 'lb', 'name': 'Luxembourgish'}, {'code': 'mk', 'name': 'Macedonian'},
    {'code': 'mg', 'name': 'Malagasy'}, {'code': 'ms', 'name': 'Malay'}, {'code': 'mt', 'name': 'Maltese'},
    {'code': 'mi', 'name': 'Maori'}, {'code': 'mn', 'name': 'Mongolian'}, {'code': 'my', 'name': 'Myanmar'},
    {'code': 'ne', 'name': 'Nepali'}, {'code': 'no', 'name': 'Norwegian'}, {'code': 'om', 'name': 'Oromo'},
    {'code': 'ps', 'name': 'Pashto'}, {'code': 'fa', 'name': 'Persian'}, {'code': 'qu', 'name': 'Quechua'},
    {'code': 'ro', 'name': 'Romanian'}, {'code': 'sm', 'name': 'Samoan'}, {'code': 'gd', 'name': 'Scots Gaelic'},
    {'code': 'nso', 'name': 'Sepedi'}, {'code': 'sr', 'name': 'Serbian'}, {'code': 'st', 'name': 'Sesotho'},
    {'code': 'sn', 'name': 'Shona'}, {'code': 'si', 'name': 'Sinhala'}, {'code': 'sk', 'name': 'Slovak'},
    {'code': 'sl', 'name': 'Slovenian'}, {'code': 'so', 'name': 'Somali'}, {'code': 'su', 'name': 'Sundanese'},
    {'code': 'sw', 'name': 'Swahili'}, {'code': 'sv', 'name': 'Swedish'}, {'code': 'tg', 'name': 'Tajik'},
    {'code': 'ti', 'name': 'Tigrinya'}, {'code': 'ts', 'name': 'Tsonga'}, {'code': 'tr', 'name': 'Turkish'},
    {'code': 'tk', 'name': 'Turkmen'}, {'code': 'ak', 'name': 'Twi'}, {'code': 'uk', 'name': 'Ukrainian'},
    {'code': 'uz', 'name': 'Uzbek'}, {'code': 'cy', 'name': 'Welsh'}, {'code': 'xh', 'name': 'Xhosa'},
    {'code': 'yi', 'name': 'Yiddish'}, {'code': 'yo', 'name': 'Yoruba'}, {'code': 'zu', 'name': 'Zulu'}
]

@app.route('/')
def index():
    try:
        return send_file('index.html')
    except:
        return "index.html not found", 404

@app.route('/api/languages')
def get_languages():
    return jsonify(LANG_LIST)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.json
    try:
        translated = GoogleTranslator(source='auto', target=data['target']).translate(data['text'])
        return jsonify({'translated': translated})
    except Exception as e:
        logger.error(f"Translation Error: {e}")
        return jsonify({'translated': "...", 'error': str(e)})

@app.route('/detect', methods=['POST'])
def detect_lang():
    data = request.json
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'code': '', 'name': ''})
    try:
        from langdetect import detect
        lang_code = detect(text)
        
        # Build mapping dict lazily
        LANG_MAP = {item['code']: item['name'] for item in LANG_LIST}
        lang_name = LANG_MAP.get(lang_code, lang_code.upper())
        
        return jsonify({'code': lang_code, 'name': lang_name})
    except Exception as e:
        print("Detect Error:", e)
        return jsonify({'code': '', 'name': 'Unknown'})

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save to a unique temporary file to avoid 'File in use' errors
    temp_dir = tempfile.gettempdir()
    temp_filename = f"audio_{uuid.uuid4()}.webm"
    temp_path = os.path.join(temp_dir, temp_filename)
    audio_file.save(temp_path)

    try:
        # Whisper automatically detects the language and transcribes it!
        result = whisper_model.transcribe(temp_path)
        extracted_text = result["text"].strip()
        detected_language = result["language"] # Usually the 2-letter code like 'ta', 'en', 'hi'
        
        return jsonify({
            'text': extracted_text,
            'language': detected_language
        })
    except Exception as e:
        logger.error(f"Whisper Error: {e}")
        # Check for ffmpeg specifically as it's a common issue on Windows
        error_msg = str(e)
        if "ffmpeg" in error_msg.lower() or "file not found" in error_msg.lower():
            error_msg = "FFmpeg not found. Please install FFmpeg to use voice features."
        return jsonify({'error': error_msg}), 500
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

@app.route('/tts', methods=['POST'])
def tts_audio():
    data = request.json
    text = data.get('text', '')
    lang = data.get('lang', 'en')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
        
    try:
        from gtts import gTTS
        # gTTS sometimes expects simpler lang codes like 'zh' instead of 'zh-CN'
        if lang == 'zh-CN': lang = 'zh-CN'
        if '-' in lang and lang not in ['zh-CN', 'zh-TW']:
            lang = lang.split('-')[0]
            
        tts = gTTS(text=text, lang=lang)
        
        import io
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        return send_file(fp, mimetype="audio/mpeg", as_attachment=False, download_name="speech.mp3")
    except Exception as e:
        print("TTS Error:", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure uploads directory exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    # Run the server
    print("\n" + "="*50)
    print("AI Neural Translator Pro - Server Starting...")
    print("Access at: http://127.0.0.1:5000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', debug=True, port=5000, use_reloader=False)