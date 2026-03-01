import os
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


def ask_ai(question, lang='en'):
    if lang == 'hi':
        lang_instruction = "Reply in Hindi using Devanagari script only."
    else:
        lang_instruction = "Reply in English only."

    payload = {
        "model": "meta-llama/Llama-3.2-3B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": f"You are Jarvis, a voice assistant. {lang_instruction} Reply in exactly 1 sentence. No lists, no bullet points. Be direct."
            },
            {"role": "user", "content": question}
        ],
        "max_tokens": 80
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 503:
            return "Model is loading, please try again in a moment."

        if response.status_code != 200:
            print(f"API ERROR {response.status_code}:", response.text)
            return "Model is loading or API error."

        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()

        return "Unexpected response format."

    except Exception as e:
        print("ERROR:", e)
        return "There was an error connecting to AI service."


if __name__ == "__main__":
    answer = ask_ai("What is the internet?")
    print("AI Response:", answer)