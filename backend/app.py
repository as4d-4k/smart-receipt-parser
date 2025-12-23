from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from werkzeug.utils import secure_filename
from ocr_engine import extract_data

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'uploads'
DB_FILE = 'database.json'  # <--- This is our mini database
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DATABASE HELPER FUNCTIONS ---
def save_to_history(receipt_data):
    """Saves the new receipt data to a JSON file."""
    history = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = [] # If file is broken, start fresh
            
    history.append(receipt_data) # Add the new receipt
    
    with open(DB_FILE, 'w') as f:
        json.dump(history, f, indent=4)

def get_all_history():
    """Reads the JSON file and returns the list."""
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

# --- ROUTES ---

@app.route('/api/scan', methods=['POST'])
def scan_receipt():
    # 1. Check if image exists
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # 2. Save the image
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 3. Process with AI
        try:
            data = extract_data(filepath)
            
            # 4. Check for errors
            if "error" in data:
                 return jsonify({"error": data["error"]}), 500

            # 5. SAVE TO HISTORY (The New Step!)
            # We add a timestamp or ID if we want, but for now just the data
            save_to_history(data)

            return jsonify({
                "message": "Success",
                "data": data
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "File type not allowed"}), 400

@app.route('/api/history', methods=['GET'])
def history():
    """New endpoint to get all past receipts"""
    data = get_all_history()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)