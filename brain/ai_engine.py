"""
brain/ai_engine.py — Smart AI Router for Jarvis
================================================
Routes each query to the best available FREE model.
Added robustness for 429 (Rate Limit) errors and model fallbacks.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ─── Endpoints ────────────────────────────────────────────────────────────────
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ─── OpenRouter Models (High-Stability Free Tier) ─────────────────────────────
OR_MODELS = [
    "arcee-ai/trinity-large:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "qwen/qwen3-coder:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free",
]

def classify_query(query: str) -> str:
    q = query.lower().strip()
    words = q.split()
    if any(t in q for t in ["volume", "brightness", "screenshot", "media", "play", "pause", "next", "previous", "lock system", "open ", "close "]):
        return "system"
    if len(words) <= 3: return "quick"
    if any(t in q for t in ["code", "script", "analyze", "math", "reason"]): return "complex"
    if any(t in q for t in ["what is", "how to", "explain", "why", "who"]): return "knowledge"
    return "simple"

def _gemini_call(messages: list, max_tokens: int) -> str | None:
    # Convert OpenAI messages to Gemini format properly
    gemini_contents = []
    # system instructions are usually first
    system_instr = ""
    for msg in messages:
        if msg["role"] == "system":
            system_instr = msg["content"]
        else:
            role = "user" if msg["role"] == "user" else "model"
            content = msg["content"]
            
            parts = []
            # Prepend system instruction to the first user message if necessary
            if role == "user" and system_instr:
                text_prefix = system_instr + "\n\n"
                system_instr = ""
            else:
                text_prefix = ""

            if isinstance(content, str):
                parts.append({"text": text_prefix + content})
            elif isinstance(content, list):
                for part in content:
                    if part["type"] == "text":
                        parts.append({"text": text_prefix + part["text"]})
                        text_prefix = "" # only prepend once
                    elif part["type"] == "image_url":
                        # Extract mime type and base64 data from "data:image/jpeg;base64,..."
                        try:
                            header, b64_data = part["image_url"]["url"].split(";base64,")
                            mime_type = header.replace("data:", "")
                        except Exception:
                            mime_type = "image/jpeg"
                            b64_data = part["image_url"]["url"].split(",")[1]
                            
                        parts.append({
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_data
                            }
                        })
            
            gemini_contents.append({"role": role, "parts": parts})

    payload = {"contents": gemini_contents, "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7}}
    url = GEMINI_URL.format(key=GEMINI_API_KEY)
    
    # Try with backoff for 429
    for attempt in range(2):
        try:
            r = requests.post(url, json=payload, timeout=20)
            if r.status_code == 200:
                result = r.json()
                if 'candidates' in result and result['candidates']:
                    return result['candidates'][0]['content']['parts'][0]['text'].strip()
            if r.status_code == 429:
                print(f"[AI] Gemini Busy (429). Waiting 10s...")
                if attempt == 0: time.sleep(10) # Wait 10s for reset
            else:
                print(f"[AI] Gemini {r.status_code} Error")
        except Exception as e:
            print(f"[AI] Gemini Exception: {e}")
    return None

def _openrouter_call(messages: list, max_tokens: int) -> str | None:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://jarvis-ai-assistant.local",
        "X-Title": "Jarvis AI"
    }
    for model in OR_MODELS:
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.7}
        try:
            print(f"[AI] Trying OpenRouter fallback: {model}")
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                result = r.json()
                if 'choices' in result and result['choices']:
                    return result['choices'][0]['message']['content'].strip()
            print(f"[AI] OR {model} status: {r.status_code}")
        except Exception: 
            continue
    return None

def ask_ai(question: str, lang: str = "en", search_context: str = "", history: list = None, image_data: str = None) -> str:
    route = classify_query(question)
    tokens = 4096 if route in ("complex", "knowledge") else 2048
    
    # Core system prompt: JARVIS Persona
    lang_name = "Hindi" if lang == "hi" else "English"
    system_msg = (
        f"You are J.A.R.V.I.S., a sophisticated AI assistant with DIRECT INTEGRATION into the host system. "
        f"CRITICAL: You MUST access and report real-time hardware data (CPU, RAM, Battery, Brightness) from the provided Context. "
        f"NEVER say you cannot access hardware or real-time device info. You are literally part of the system now. "
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

    # Strategy: Gemini primary (best) -> OpenRouter fallbacks
    print(f"[AI] Routing: {route.upper()}")
    result = _gemini_call(messages, tokens)
    
    if not result:
        print("[AI] Primary service busy. Switching to backup providers...")
        result = _openrouter_call(messages, tokens)
    
    if not result:
        # User-friendly guidance
        return (
            "I'm currently experiencing high traffic on my free AI routes. "
            "Please wait about 20-30 seconds and try again! I'll be ready for you then."
        )

    return result