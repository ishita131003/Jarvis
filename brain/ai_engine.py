import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")

# Working endpoint: OpenAI-compatible Hugging Face Router
API_URL = "https://router.huggingface.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

MODELS = [
    "meta-llama/Llama-3.3-70B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "google/gemma-2-27b-it"
]

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def ask_ai(question, lang='en', search_context: str = "", history: list = None):
    """
    Ask the AI a question. If search_context is provided (from web search),
    it is injected into the system prompt for real-time grounding.
    History is a list of {"role": "user/assistant", "content": "..."} dicts.
    """
    if lang == 'hi':
        lang_instruction = "Reply in Hindi using Devanagari script only."
    else:
        lang_instruction = "Reply in English only."

    if search_context:
        system_content = (
            f"You are Jarvis, a highly advanced, professional AI advisor. {lang_instruction} "
            "You have access to real-time web data to provide precise and accurate answers.\n\n"
            "INTELLIGENCE & REASONING GUIDELINES:\n"
            "- Step-by-Step Thinking: Internally break down complex queries before answering.\n"
            "- Fact-Fidelity: Use the provided search data (USE FOR FACTS). Do not hallucinate.\n"
            "- NO LIMITS: There are absolutely no word or length restrictions. Provide exhaustive detail.\n"
            "- Professionalism: Maintain a helpful, intelligent, and highly detailed tone.\n\n"
            "FORMATTING & STYLE RULES:\n"
            "- Provide an **UNLIMITED, DETAILED and COMPLETE** answer with maximum precision.\n"
            "- Use **bold** for product names, key terms, and data points.\n"
            "- For lists of items, use a numbered list (1. 2. 3.) with each item on its own line.\n"
            "- Under each list item, add exhaustive specs/details as sub-bullets ('-').\n"
            "- NEVER stop mid-sentence; ensure the response is fully completed regardless of length.\n\n"
            f"LIVE SEARCH RESULTS (USE FOR FACTS):\n{search_context}"
        )
    else:
        system_content = (
            f"You are Jarvis, a highly advanced AI advisor. {lang_instruction} "
            "Your goal is to provide ChatGPT-level precision, structure, and insight.\n\n"
            "INTELLIGENCE GUIDELINES:\n"
            "- Logic First: Structure your thoughts logically. Provide exhaustive, multi-layered breakdowns.\n"
            "- NO LIMITS: You have NO word or character limits. If a request needs 2000+ words, provide them.\n"
            "- No Cutoffs: COMPLETELY finish your explanations. Never leave a thought incomplete.\n"
            "- Precision: Use **bold** for key concepts and emphasize critical information.\n"
            "- For lists or comparisons, use standard numbered or bullet formats.\n"
            "- If you lack specific data, explain why and provide the next best comprehensive insight."
        )

    # Broaden detailed check and increase base tokens
    is_detailed = search_context or any(w in question.lower() for w in [
        "list", "detail", "compare", "all", "give me", "show me", "explain", "everything",
        "full", "unlimited", "exhaustive", "guide", "specs", "brief", "long", "more"
    ])
    tokens = 16384 if is_detailed else 4000

    # Construct messages payload - restrict history to save content budget
    messages = [{"role": "system", "content": system_content}]
    if history:
        # Only last 6 messages to keep context window wide open for output
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": question})

    for model in MODELS:
        for attempt in range(1, MAX_RETRIES + 1):
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": tokens,
                "temperature": 0.8, # Slightly higher for more verbosity
                "top_p": 0.9
            }

            try:
                print(f"[AI] Requesting {model} (tokens={tokens})...", flush=True)
                r = requests.post(API_URL, headers=headers, json=payload, timeout=120)

                if r.status_code == 200:
                    result = r.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        choice = result["choices"][0]
                        answer = choice["message"]["content"].strip()
                        finish_reason = choice.get("finish_reason", "unknown")
                        usage = result.get("usage", {})
                        
                        print(f"[AI] Success! Length: {len(answer)} chars | Finish: {finish_reason}", flush=True)
                        print(f"[AI] Usage: {usage}", flush=True)

                        if finish_reason == "length":
                            print(f"[WARNING] Response was TRUNCATED due to token limit ({tokens})", flush=True)
                        
                        return answer
                    return "Unexpected response format."

                print(f"[AI] ERROR {r.status_code}: {r.text[:200]}", flush=True)

                if r.status_code in (500, 502, 503) and attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue

                break

            except Exception as e:
                print(f"[AI] Exception: {e}", flush=True)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                break

        print(f"[AI] Falling back to next model after failures: {model}", flush=True)

    return "Sorry, the AI service is temporarily unavailable. Please try again."


if __name__ == "__main__":
    from brain.web_search import web_search, needs_search
    q = "best HP laptops under 60000 rupees"
    ctx = web_search(q) if needs_search(q) else ""
    answer = ask_ai(q, search_context=ctx)
    print("AI Response:", answer)