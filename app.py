import threading
import webbrowser
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from core.listener import listen
from voice.speaker import speak
from brain.ai_engine import ask_ai
from brain.web_search import web_search, needs_search
from core.commands import handle_command
from langdetect import detect as detect_lang

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global chat history to keep context (max 20 messages)
CHAT_HISTORY = []


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def on_connect():
    emit('status', {'state': 'idle', 'message': 'Jarvis Connected. Ready to assist.'})


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

        # Send user's message to frontend
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

    if not user_input:
        return

    emit('user_message', {'text': user_input})

    # Check for exit commands
    if user_input in ["exit", "stop", "goodbye", "band karo", "बंद करो"]:
        emit('bot_message', {'text': 'Goodbye Ishita.'})
        emit('status', {'state': 'goodbye', 'message': 'Shutting down...'})
        speak("Goodbye Ishita.")
        return

    def process_in_thread():
        process_input(user_input)

    thread = threading.Thread(target=process_in_thread, daemon=True)
    thread.start()


def process_input(user_input):
    """Process user input through commands or AI."""
    import traceback
    try:
        socketio.emit('status', {'state': 'thinking', 'message': 'Processing...'})

        # Check for system commands first
        result = handle_command(user_input)
        if result:
            socketio.emit('bot_message', {'text': result})
            socketio.emit('status', {'state': 'speaking', 'message': 'Speaking...'})
            speak(result)
            socketio.emit('status', {'state': 'idle', 'message': 'Ready.'})
            return

        # Detect language
        try:
            lang = detect_lang(user_input)
            lang = 'hi' if lang == 'hi' else 'en'
        except Exception:
            lang = 'en'

        # Check if query needs live web data
        search_context = ""
        if needs_search(user_input):
            socketio.emit('status', {'state': 'thinking', 'message': 'Searching the web...'})
            print(f"[Search] Query needs real-time data: {user_input}", flush=True)
            search_context = web_search(user_input, max_results=4)

        print(f"[DEBUG] Calling ask_ai | input='{user_input}' | lang='{lang}' | has_search={'yes' if search_context else 'no'}", flush=True)

        # Get AI response (with optional search context and chat history)
        socketio.emit('status', {'state': 'thinking', 'message': 'Thinking...'})
        
        # Prepare current history (copy to avoid mutation issues during async)
        current_history = list(CHAT_HISTORY)
        
        response = ask_ai(user_input, lang=lang, search_context=search_context, history=current_history)

        print(f"[DEBUG] Final AI Response Length: {len(response)} characters.", flush=True)
        socketio.emit('bot_message', {'text': response})
        
        # Update global history
        CHAT_HISTORY.append({"role": "user", "content": user_input})
        CHAT_HISTORY.append({"role": "assistant", "content": response})
        
        # Keep history to last 20 messages (10 rounds)
        if len(CHAT_HISTORY) > 20:
            del CHAT_HISTORY[:2]

        socketio.emit('bot_message', {'text': response})
        socketio.emit('status', {'state': 'speaking', 'message': 'Speaking...'})
        speak(response)
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
