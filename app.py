from flask import Flask, request, jsonify, send_file, send_from_directory, render_template_string
import os
import time
from TTS.api import TTS
import traceback

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

try:
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
except Exception as e:
    print(f"Failed to initialize TTS: {str(e)}")
    raise

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Cloning</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            width: 100%;
            max-width: 500px;
            text-align: center;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
            color: #fff;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        input[type="file"], input[type="text"] {
            display: block;
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: none;
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
            font-size: 1em;
            transition: all 0.3s ease;
        }
        input[type="file"]::-webkit-file-upload-button {
            background: #ff6f61;
            border: none;
            padding: 8px 16px;
            border-radius: 25px;
            color: #fff;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        input[type="file"]::-webkit-file-upload-button:hover {
            background: #ff483b;
        }
        input[type="text"]::placeholder {
            color: #ccc;
        }
        input[type="text"]:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.3);
        }
        button {
            background: #00c4cc;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            color: #fff;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 15px;
        }
        button:hover {
            background: #00a3aa;
            transform: scale(1.05);
        }
        .generated-section {
            margin-top: 30px;
            display: none; /* Hidden by default */
            animation: fadeIn 0.5s ease-in;
        }
        h2 {
            font-size: 1.8em;
            margin-bottom: 15px;
            color: #fff;
        }
        audio {
            width: 100%;
            margin-top: 10px;
            filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
        }
        p {
            font-size: 0.9em;
            color: #ddd;
            word-wrap: break-word;
        }
        .loading-bar {
            display: none; /* Hidden by default */
            margin-top: 20px;
            width: 100%;
            height: 10px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            overflow: hidden;
            position: relative;
        }
        .loading-bar::after {
            content: '';
            position: absolute;
            width: 50%;
            height: 100%;
            background: #00c4cc;
            animation: loading 1.5s infinite ease-in-out;
        }
        @keyframes loading {
            0% { transform: translateX(-100%); }
            50% { transform: translateX(200%); }
            100% { transform: translateX(200%); }
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }
            h1 { font-size: 2em; }
            h2 { font-size: 1.5em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Voice Cloning App</h1>
        <input type="file" id="audioInput" accept="audio/*">
        <input type="text" id="textInput" placeholder="Enter text to be spoken" required>
        <button id="upload">Upload & Clone Voice</button>
        <div class="loading-bar" id="loadingBar"></div>
        <div class="generated-section" id="generatedSection">
            <h2>Generated Voice</h2>
            <audio id="clonedAudio" controls></audio>
            <p id="audioPath"></p>
        </div>
    </div>
    
    <script>
        document.getElementById('upload').addEventListener('click', async () => {
            const textInput = document.getElementById('textInput').value;
            const audioInput = document.getElementById('audioInput');
            const generatedSection = document.getElementById('generatedSection');
            const loadingBar = document.getElementById('loadingBar');
            
            if (!textInput) {
                alert("Enter text for speech synthesis!");
                return;
            }
            if (!audioInput.files.length) {
                alert("Please select an audio file!");
                return;
            }
            
            const formData = new FormData();
            formData.append('text', textInput);
            formData.append('file', audioInput.files[0]);
            
            for (let pair of formData.entries()) {
                console.log(pair[0], pair[1]);
            }
            
            // Show loading bar
            loadingBar.style.display = 'block';
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.error || 'Unknown error'); });
                }
                return response.json();
            })
            .then(data => {
                console.log('Parsed JSON:', data);
                if (data.error) {
                    throw new Error(data.error);
                }
                const audioUrl = `/outputs/${data.filename}`;
                const audioElement = document.getElementById('clonedAudio');
                audioElement.src = audioUrl;
                audioElement.load();
                document.getElementById('audioPath').textContent = "Generated Audio: " + audioUrl;
                generatedSection.style.display = 'block'; // Show generated section
                loadingBar.style.display = 'none'; // Hide loading bar
            })
            .catch(error => {
                console.error('Upload Error:', error);
                alert("Error: " + error.message);
                loadingBar.style.display = 'none'; // Hide loading bar on error
            });
        });
    </script>
</body>
</html>
"""

def clone_voice(text, audio_samples):
    unique_filename = f"cloned_voice_{int(time.time() * 1000)}.wav"
    output_file = os.path.join(OUTPUT_FOLDER, unique_filename)
    try:
        print(f"Cloning voice with text: {text}, sample: {audio_samples}")
        tts.tts_to_file(text=text, file_path=output_file, speaker_wav=audio_samples, language="en")
        print(f"Generated: {output_file}")
        return output_file, unique_filename
    except Exception as e:
        print(f"Error in clone_voice: {str(e)}")
        traceback.print_exc()
        return None, None

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        if 'text' not in request.form:
            return jsonify({"error": "No text input provided"}), 400

        file = request.files['file']
        text = request.form['text']

        if file.filename == '':
            return jsonify({"error": "Empty file uploaded"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        print(f"File saved: {file_path}, Text: {text}")

        output_audio, filename = clone_voice(text, file_path)

        if not output_audio or not os.path.exists(output_audio):
            return jsonify({"error": "Failed to generate cloned voice", "details": "TTS processing failed"}), 500

        return jsonify({"filename": filename}), 200
    except Exception as e:
        print(f"Unexpected error in /upload: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/outputs/<filename>')
def serve_output(filename):
    try:
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file {filename}: {str(e)}")
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
