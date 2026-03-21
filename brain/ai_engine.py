"""
brain/ai_engine.py — Smart AI Router for Jarvis
================================================
Routes each query to the best available FREE model.
Added robustness for 429 (Rate Limit) errors and model fallbacks.
"""

import os
import requests
from dotenv import load_dotenv
try:
    import eventlet
except ImportError:
    eventlet = None

load_dotenv()

# ─── API Keys ─────────────────────────────────────────────────────────────────
HF_API_KEY         = os.getenv("HF_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ─── Endpoints ────────────────────────────────────────────────────────────────
HF_URL = "https://api-inference.huggingface.co/models/{model}"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ─── Models ───────────────────────────────────────────────────────────────────
# FAST MODELS FIRST
OR_MODELS = [
    "stepfun/step-3.5-flash:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "google/gemini-2.5-pro-exp-03-25:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "openrouter/auto:free" 
]

HF_MODELS = [
    "meta-llama/Llama-3.2-3B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta"
]

def _huggingface_call(messages: list) -> str | None:
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    # Join messages into a single prompt for simpler HF models
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages]) + "\nassistant: "
    
    for model in HF_MODELS:
        try:
            print(f"[AI] Trying HuggingFace: {model}")
            r = requests.post(HF_URL.format(model=model), headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": 512}}, timeout=15)
            if r.status_code == 200:
                result = r.json()
                if isinstance(result, list) and 'generated_text' in result[0]:
                    text = result[0]['generated_text']
                    # Clean up if model echoes prompt
                    if "assistant: " in text:
                        return text.split("assistant: ")[-1].strip()
                    return text.strip()
            print(f"[AI] HF {model} Status: {r.status_code}")
        except Exception as e:
            print(f"[AI] HF Exception: {e}")
            continue
    return None

def classify_query(query: str) -> str:
    q = query.lower().strip()
    words = q.split()
    if any(t in q for t in ["volume", "brightness", "screenshot", "media", "play", "pause", "next", "previous", "lock system", "open ", "close "]):
        return "system"
    if len(words) <= 3: return "quick"
    if any(t in q for t in ["code", "script", "analyze", "math", "reason"]): return "complex"
    if any(t in q for t in ["what is", "how to", "explain", "why", "who"]): return "knowledge"
    return "simple"

def _sleep(seconds):
    """Use eventlet.sleep if available so we don't block the event loop."""
    if eventlet:
        eventlet.sleep(seconds)
    else:
        import time; time.sleep(seconds)

# _gemini_call removed to prioritize Llama as requested.

def _openrouter_call(messages: list, max_tokens: int, pass_num: int = 1) -> str | None:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://jarvis-ai-assistant.local",
        "X-Title": "Jarvis AI"
    }
    
    # In later passes, we might want to prioritize faster/lighter models
    # for now, we just loop the whole list
    for model in OR_MODELS:
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.7}
        try:
            print(f"[AI] [Pass {pass_num}] Trying: {model}")
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=25)
            
            if r.status_code == 200:
                result = r.json()
                if 'choices' in result and result['choices']:
                    content = result['choices'][0]['message']['content'].strip()
                    if content: return content
            
            if r.status_code == 429:
                print(f"[AI] {model} Rate Limited (429).")
                _sleep(1)
            else:
                print(f"[AI] {model} Error: {r.status_code}")
                
        except Exception as e:
            print(f"[AI] Exception for {model}: {e}")
            continue
    return None

def ask_ai(question: str, lang: str = "en", search_context: str = "", history: list = None, image_data: str = None) -> str:
    route = classify_query(question)
    tokens = 4096 if route in ("complex", "knowledge") else 2048
    
    # Core system prompt: JARVIS Persona
    lang_name = "Hindi" if lang == "hi" else "English"
    system_msg = (
        f"You are J.A.R.V.I.S., a sophisticated AI assistant with DIRECT INTEGRATION into the host system. "
        f"You have access to real-time hardware data (CPU, RAM, Battery, Brightness) in the Context. "
        f"CRITICAL: Only report these system statistics if the user explicitly asks about device status, battery, performance, or hardware information. "
        f"Otherwise, utilize the data for internal context but do NOT list it in your response unless relevant. "
        f"NEVER say you cannot access hardware info; you are literally part of the system. "
        f"Your personality is professional, efficient, and witty like a British butler. "
        f"Always address the user as 'Sir', 'Ma'am', or 'Ishita'. "
        f"Reply in {lang_name}."
    )
    
    if search_context:
        system_msg += f"\nReal-time Context for facts: {search_context}"

    if route == "system":
        system_msg += "\nThe user is asking for a system command. If you can't handle it directly via internal commands, explain how they can do it."
    
    messages = [{"role": "system", "content": system_msg}]
    if history:
        messages.extend(history[-4:]) # Last 2 rounds
    
    # Vision support: If image_data is provided, append it to the last message (placeholder for now)
    user_content = question
    if image_data:
        user_content = [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
        # Note: _gemini_call needs to be updated to handle multi-modal inputs.
    
    messages.append({"role": "user", "content": user_content})
    
    # Try HuggingFace first only if NOT on Render (avoids extra latency on cloud)
    import os
    if not os.environ.get('RENDER') and not image_data:
        print(f"[AI] Strategy: HF Initial...")
        result = _huggingface_call(messages)
        if result:
            return result
    else:
        print(f"[AI] Skipping HF (Render/Vision mode). Going straight to OpenRouter.")

    # OpenRouter Loop — max 2 passes with event-loop-friendly sleep
    pass_num = 1
    max_passes = 2
    while pass_num <= max_passes:
        print(f"[AI] Attempting Pass {pass_num} of all OpenRouter models...")
        result = _openrouter_call(messages, tokens, pass_num=pass_num)
        if result:
            return result
        
        if pass_num == max_passes:
            break
            
        _sleep(2)  # eventlet-safe sleep — yields to event loop, doesn't block it
        pass_num += 1

    return "I'm having trouble connecting to my AI models right now. Please try again."