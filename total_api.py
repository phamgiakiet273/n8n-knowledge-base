from flask import Flask, render_template, request, jsonify
import requests
import os
import base64

app = Flask(__name__)

# Updated webhook configurations
WEBHOOK_UPLOAD = "http://localhost:5678/webhook/document_upload"
WEBHOOK_QUERY = "http://localhost:5678/webhook/query"
WEBHOOK_KNOWLEDGE_BASES = "http://localhost:5678/webhook/get_knowledge_base"
WEBHOOK_FEEDBACK = "http://localhost:5678/webhook/feedback"

# File configurations
ALLOWED_EXTENSIONS = {'pdf'}
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_folder_id(drive_url):
    """Extract folder ID from Google Drive URL"""
    drive_url = drive_url.split('?')[0]
    parts = drive_url.strip('/').split('/')
    if len(parts) > 1 and parts[-2] == 'folders':
        return parts[-1]
    return None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    """Handle both Google Drive and Local File uploads"""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    upload_type = data.get('type')
    knowledge_base = data.get('knowledge_base')
    
    if not knowledge_base:
        return jsonify({"status": "error", "message": "Knowledge base name is required"}), 400

    try:
        payload = {
            "method": upload_type,
            "knowledge_base": knowledge_base
        }

        if upload_type == 'drive':
            # Handle Google Drive upload
            folder_url = data.get('folderUrl')
            folder_id = extract_folder_id(folder_url)
            if not folder_id:
                return jsonify({"status": "error", "message": "Invalid Google Drive URL"}), 400

            payload.update({
                "folderId": folder_id,
                "files": []  # Empty array for drive uploads
            })

        elif upload_type == 'local':
            # Handle local file upload
            files = data.get('files', [])
            if not files:
                return jsonify({"status": "error", "message": "No files provided"}), 400

            # Validate files and add metadata
            validated_files = []
            for file in files:
                filename = file.get('filename', '')
                if not allowed_file(filename):
                    return jsonify({"status": "error", "message": f"Invalid file type: {filename}"}), 400
                
                validated_files.append({
                    "filename": filename,
                    "content": file.get('content'),
                    "upload_method": "local"
                })

            payload["files"] = validated_files

        else:
            return jsonify({"status": "error", "message": "Invalid upload type"}), 400

        # Send to unified webhook endpoint
        response = requests.post(WEBHOOK_UPLOAD, json=payload)
        response.raise_for_status()
        result = response.json()

        # Handle known error cases
        if isinstance(result, list):
            if result[0].get("result", {}).get("exists"):
                return jsonify({"status": "error", "message": "Knowledge base already exists"}), 400

        return jsonify({"status": "success", "data": result})

    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/query', methods=['POST'])
def handle_query():
    """Handle knowledge base queries"""
    try:
        data = {
            "question": request.form.get('question'),
            "knowledge_base": request.form.get('knowledge_base')
        }
        
        response = requests.post(WEBHOOK_QUERY, json=data)
        response.raise_for_status()
        result = response.json()

        # Extract response content
        try:
            if isinstance(result, list):
                content = result[0]["choices"][0]["message"].get("content", "No content available")
            else:
                content = result["choices"][0]["message"].get("content", "No content available")
        except (KeyError, IndexError):
            content = "Invalid response format"

        return jsonify({"status": "success", "response": content})

    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_knowledge_base', methods=['GET'])
def get_knowledge_bases():
    """Retrieve list of available knowledge bases"""
    try:
        response = requests.post(WEBHOOK_KNOWLEDGE_BASES)
        response.raise_for_status()
        data = response.json()

        # Extract knowledge base names
        collections = data[0].get("result", {}).get("collections", [])
        knowledge_bases = [col["name"] for col in collections]

        return jsonify({"status": "success", "knowledge_bases": knowledge_bases})

    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    """Handle user feedback submission"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        # Validate required fields
        required_fields = ['knowledge_base', 'question', 'response', 'feedback']
        for field in required_fields:
            if field not in data:
                return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400

        # Prepare payload for webhook
        payload = {
            "knowledge_base": data['knowledge_base'],
            "question": data['question'],
            "response": data['response'],
            "feedback": data['feedback'],
            "comment": data.get('comment', '')
        }

        # Send to feedback webhook
        response = requests.post(WEBHOOK_FEEDBACK, json=payload)
        response.raise_for_status()

        return jsonify({"status": "success"})

    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)