import eventlet
eventlet.monkey_patch()

import sys
import site
import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# Defensive: Ensure user-site-packages are in path for Windows
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

import threading
import webbrowser
import psutil
import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

from brain.ai_engine import ask_ai
from brain.web_search import web_search, needs_search
from core.commands import handle_command
from core.system_control import get_system_stats
from langdetect import detect as detect_lang
import base64
import io
import fitz  # PyMuPDF

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global chat history to keep context (max 20 messages)
CHAT_HISTORY = []
IS_MUTED = False

@socketio.on('stop_audio')
def on_stop_audio():
    """Triggered when user clicks the mute/stop button on a message."""
    print("[Socket] Received stop_audio request.")

@socketio.on('toggle_mute')
def on_toggle_mute(data):
    """Toggle global mute state."""
    global IS_MUTED
    IS_MUTED = data.get('muted', False)
    print(f"[Socket] Mute set to: {IS_MUTED}")

def emit_system_stats():
    """Background task to emit system stats every 2 seconds."""
    while True:
        try:
            stats = get_system_stats()
            socketio.emit('system_stats', stats)
        except Exception as e:
            print(f"[Stats Error] {e}")
        socketio.sleep(2)

def extract_text_from_pdf(base64_data):
    """Extract text from a base64 encoded PDF using PyMuPDF."""
    try:
        pdf_data = base64.b64decode(base64_data)
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        print(f"[PDF Error] {e}")
        return f"Error extracting text: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html', 
                           supabase_url=os.environ.get('SUPABASE_URL', ''),
                           supabase_key=os.environ.get('SUPABASE_ANON_KEY', ''))

@app.route('/voice-mode')
def voice_mode():
    return render_template('voice_mode.html')

@socketio.on('connect')
def on_connect():
    emit('status', {'state': 'idle', 'message': 'Jarvis Connected. Ready to assist.'})
    # Start stats emission as a background task
    socketio.start_background_task(emit_system_stats)

@socketio.on('send_message')
def on_send_message(data):
    """Triggered when user sends a text message."""
    user_input = data.get('text', '').strip().lower()
    file_data = data.get('file', None)
    file_type = data.get('file_type', 'image')
    file_name = data.get('file_name', '')

    if not user_input and not file_data:
        return

    if user_input or file_data:
        emit('user_message', {'text': user_input, 'file': file_data, 'file_type': file_type, 'file_name': file_name})

    # Check for exit commands
    if user_input in ["exit", "stop", "goodbye", "band karo", "बंद करो"]:
        emit('bot_message', {'text': 'Goodbye Ishita.'})
        emit('status', {'state': 'goodbye', 'message': 'Shutting down...'})
        return

    socketio.start_background_task(process_input, user_input, file_data, file_type)

def process_input(user_input, file_data=None, file_type='image'):
    """Process user input through commands or AI."""
    import traceback
    try:
        socketio.emit('status', {'state': 'thinking', 'message': 'Processing...'})

        # Check for system commands first
        if user_input:
            result = handle_command(user_input)
            if result:
                socketio.emit('bot_message', {'text': result})
                socketio.emit('status', {'state': 'idle', 'message': 'Ready.'})
                return

        # Detect language
        try:
            lang = detect_lang(user_input) if user_input else 'en'
            lang = 'hi' if lang == 'hi' else 'en'
        except Exception:
            lang = 'en'

        # Check if query needs live web data
        search_context = ""
        if user_input and needs_search(user_input):
            socketio.emit('status', {'state': 'thinking', 'message': 'Searching the web...'})
            search_context = web_search(user_input, max_results=4)

        # Get real-time system stats for context
        stats = get_system_stats()
        stats_context = f"Current System Stats: CPU: {stats['cpu']}%, RAM: {stats['ram']}%, Battery: {stats['battery']}%, Brightness: {stats['brightness']}%"

        # Get AI response
        socketio.emit('status', {'state': 'thinking', 'message': 'Thinking...'})
        current_history = list(CHAT_HISTORY)
        
        # Combine search and stats context
        full_context = search_context
        if stats_context:
            full_context = (full_context + "\n" + stats_context).strip()
            
        # PDF Text Extraction
        pdf_text = ""
        if file_data and file_type == 'pdf':
            socketio.emit('status', {'state': 'thinking', 'message': 'Analyzing PDF...'})
            pdf_text = extract_text_from_pdf(file_data)
            if pdf_text:
                full_context = (full_context + "\n\nAttached PDF Content:\n" + pdf_text).strip()

        # Image Data for Vision
        image_data = file_data if file_data and file_type == 'image' else None

        response = ask_ai(user_input or "Analyze the attached file.", lang=lang, search_context=full_context, history=current_history, image_data=image_data)
        
        socketio.emit('bot_message', {'text': response})
        
        if user_input:
            CHAT_HISTORY.append({"role": "user", "content": user_input})
            CHAT_HISTORY.append({"role": "assistant", "content": response})
        
        if len(CHAT_HISTORY) > 20:
            del CHAT_HISTORY[:2]

        # The frontend (JavaScript) handles TTS
        socketio.emit('status', {'state': 'idle', 'message': 'Ready.'})
    except Exception as e:
        print(f"[ERROR] process_input crashed: {e}", flush=True)
        traceback.print_exc()
        socketio.emit('bot_message', {'text': f'Error: {str(e)}'})
        socketio.emit('status', {'state': 'idle', 'message': 'Error occurred.'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 Starting Jarvis Web Interface on port {port}...")
    if os.environ.get('RENDER') is None: # Only open browser locally
        webbrowser.open(f'http://localhost:{port}')
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
