import threading
import webbrowser
import psutil
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

from core.listener import listen
from voice.speaker import speak, stop_speaking, wait_until_finished
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

# Global flag to control voice mode loop
voice_mode_active = {}

def voice_interaction_loop(sid):
    """Continuous loop for voice-only interaction."""
    print(f"[VoiceMode] Loop started for {sid}")
    while voice_mode_active.get(sid, False):
        try:
            # 1. Notify frontend we are listening
            socketio.emit('voice_status', {'mode': 'listening', 'status': 'Listening...'}, room=sid)
            
            # 2. Capture voice input
            text = listen()
            
            if not text:
                continue
            
            print(f"[VoiceMode] User said: {text}")
            
            if any(cmd in text.lower() for cmd in ["exit", "stop", "quit", "bye"]):
                socketio.emit('voice_status', {'mode': 'idle', 'status': 'Ending call...'}, room=sid)
                speak("Goodbye Sir. Ending call.")
                break

            # Detect language for better response
            # Simple check for Devanagari 
            is_hindi_input = any('\u0900' <= char <= '\u097F' for char in text)
            lang_code = 'hi' if is_hindi_input else 'en'

            # 3. Notify frontend we are processing
            socketio.emit('voice_status', {'mode': 'thinking', 'status': 'Thinking...'}, room=sid)
            
            # 4. Get AI response (infinite loop internally, but we can emit updates if possible)
            # Actually ask_ai blocks, so we can't easily emit from here unless we change ask_ai
            response_text = ask_ai(text, lang=lang_code, search_context="", history=[])

            # 5. Notify frontend we are speaking and speak it
            socketio.emit('voice_status', {'mode': 'speaking', 'status': 'Jarvis is speaking...'}, room=sid)
            speak(response_text)
            
            # 6. Barge-in Logic: Listen while speaking
            # We use a short phrase limit to detect interruption quickly
            while voice_mode_active.get(sid, False):
                # Check if speaking is done
                from voice.speaker import is_speaking_now
                if not is_speaking_now:
                    break
                
                # Try a quick "background" listen for interruption
                # We use a shorter phrase_time_limit for barge-in detection
                try:
                    # Quick listen with short phrase limit to detect sound/voice
                    interrupt_text = listen(timeout=0.5, phrase_time_limit=2)
                    if interrupt_text:
                        print(f"[BargeIn] User interrupted with: {interrupt_text}")
                        stop_speaking()
                        # Immediately process the interruption as new input
                        text = interrupt_text
                        # Jump back to the start of processing (step 3)
                        # We simulate a "goto" by updating text and skipping wait
                        socketio.emit('voice_status', {'mode': 'thinking', 'status': 'Thinking...'}, room=sid)
                        response_text = ask_ai(text, lang=lang_code, search_context="", history=[])
                        socketio.emit('voice_status', {'mode': 'speaking', 'status': 'Jarvis is speaking...'}, room=sid)
                        speak(response_text)
                        continue 
                except Exception:
                    # Timeout or no voice detected, just check if still speaking
                    pass
                
                time.sleep(0.1)
            
            # 6. Wait for speech to finish before next listen (if not interrupted)
            wait_until_finished()
            
        except Exception as e:
            print(f"[VoiceMode] Loop Error: {e}")
            break
    
    print(f"[VoiceMode] Loop ended for {sid}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/voice-mode')
def voice_mode():
    return render_template('voice_mode.html')

@socketio.on('start_voice_mode')
def handle_start_voice_mode():
    sid = request.sid
    voice_mode_active[sid] = True
    threading.Thread(target=voice_interaction_loop, args=(sid,), daemon=True).start()

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    voice_mode_active[sid] = False

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

    if user_input or image_data:
        emit('user_message', {'text': user_input, 'image': image_data})

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
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
