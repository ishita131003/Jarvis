import sys
import os

# Add current directory to path so we can import brain
sys.path.append(os.getcwd())

from brain.ai_engine import ask_ai

def test_force_response():
    print("--- JARVIS AI PERSISTENCE TEST ---")
    query = 'Hello Jarvis, give me a short fact about space.'
    print(f"Sending query: '{query}'")
    
    response = ask_ai(query)
    
    with open("d:/rbu/BERAM/Jarvis/ai_result_log.txt", "w", encoding="utf-8") as f:
        f.write(f"Query: {query}\n")
        f.write(f"Response: {response}\n")
    
    print("\n[TEST COMPLETED] Result written to ai_result_log.txt")

if __name__ == "__main__":
    test_force_response()
