import threading
import webbrowser
import psutil
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from core.listener import listen
from voice.speaker import speak, stop_speaking
from brain.ai_engine import ask_ai
from brain.web_search import web_search, needs_search
from core.commands import handle_command
from core.system_control import get_system_stats
from langdetect import detect as detect_lang

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global chat history to keep context (max 20 messages)
CHAT_HISTORY = []
IS_MUTED = False

@socketio.on('stop_audio')
def on_stop_audio():
    """Triggered when user clicks the mute/stop button on a message."""
    print("[Socket] Received stop_audio request.")
    stop_speaking()

@socketio.on('toggle_mute')
def on_toggle_mute(data):
    """Toggle global mute state."""
    global IS_MUTED
    IS_MUTED = data.get('muted', False)
    if IS_MUTED:
        stop_speaking()
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

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    emit('status', {'state': 'idle', 'message': 'Jarvis Connected. Ready to assist.'})
    # Start stats emission as a background task
    socketio.start_background_task(emit_system_stats)

@socketio.on('start_listening')
def on_start_listening():
    """Triggered when user clicks the mic button."""
    emit('status', {'state': 'listening', 'message': 'Listening...'})

    def listen_and_respond():
        user_input = listen()
        if not user_input:
            socketio.emit('status', {'state': 'idle', 'message': 'Could not understand. Try again.'})
            return

        user_input_clean = user_input.strip().lower()
        socketio.emit('user_message', {'text': user_input_clean})

        # Check for exit commands
        if user_input_clean in ["exit", "stop", "goodbye", "band karo", "बंद करो"]:
            socketio.emit('bot_message', {'text': 'Goodbye Ishita.'})
            socketio.emit('status', {'state': 'goodbye', 'message': 'Shutting down...'})
            speak("Goodbye Ishita.")
            return

        process_input(user_input_clean)

    thread = threading.Thread(target=listen_and_respond, daemon=True)
    thread.start()

@socketio.on('send_message')
def on_send_message(data):
    """Triggered when user sends a text message."""
    user_input = data.get('text', '').strip().lower()
    image_data = data.get('image', None) # Base64 image data from frontend

    if not user_input and not image_data:
        return

    if user_input:
        emit('user_message', {'text': user_input})

    # Check for exit commands
    if user_input in ["exit", "stop", "goodbye", "band karo", "बंद करो"]:
        emit('bot_message', {'text': 'Goodbye Ishita.'})
        emit('status', {'state': 'goodbye', 'message': 'Shutting down...'})
        speak("Goodbye Ishita.")
        return

    def process_in_thread():
        process_input(user_input, image_data=image_data)

    thread = threading.Thread(target=process_in_thread, daemon=True)
    thread.start()

def process_input(user_input, image_data=None):
    """Process user input through commands or AI."""
    import traceback
    try:
        socketio.emit('status', {'state': 'thinking', 'message': 'Processing...'})

        # Check for system commands first
        if user_input:
            result = handle_command(user_input)
            if result:
                socketio.emit('bot_message', {'text': result})
                socketio.emit('status', {'state': 'speaking', 'message': 'Speaking...'})
                speak(result)
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

        response = ask_ai(user_input or "Describe this image.", lang=lang, search_context=full_context, history=current_history, image_data=image_data)
        
        socketio.emit('bot_message', {'text': response})
        
        if user_input:
            CHAT_HISTORY.append({"role": "user", "content": user_input})
            CHAT_HISTORY.append({"role": "assistant", "content": response})
        
        if len(CHAT_HISTORY) > 20:
            del CHAT_HISTORY[:2]

        socketio.emit('status', {'state': 'speaking', 'message': 'Speaking...'})
        if not IS_MUTED:
            speak(response)
        else:
            print("[Speaker] Muted. Skipping audio.")
        socketio.emit('status', {'state': 'idle', 'message': 'Ready.'})
    except Exception as e:
        print(f"[ERROR] process_input crashed: {e}", flush=True)
        traceback.print_exc()
        socketio.emit('bot_message', {'text': f'Error: {str(e)}'})
        socketio.emit('status', {'state': 'idle', 'message': 'Error occurred.'})

if __name__ == '__main__':
    print("🚀 Starting Jarvis Web Interface...")
    print("🌐 Open http://localhost:5001 in your browser")
    webbrowser.open('http://localhost:5001')
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
