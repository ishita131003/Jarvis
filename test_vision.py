import sys
import os
import base64

# Add current directory to path
sys.path.append(os.getcwd())

from brain.ai_engine import ask_ai

def test_vision():
    print("--- JARVIS VISION ENGINE TEST ---")
    
    # Create a small dummy base64 pixel to simulate an image if a real one isn't handy
    # Red 1x1 pixel
    dummy_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    print("Sending query: 'What is in this image?' with dummy image...")
    # Using a known vision-capable model if possible, but let's just use the router
    try:
        response = ask_ai("What is in this image? Describe its color.", image_data=dummy_image)
        print("\nJARVIS Response:")
        print(response)
        
        # Log to file for verification
        with open("vision_test_log.txt", "w", encoding='utf-8') as f:
            f.write(f"Query: What is in this image?\nResponse: {response}")
            
    except Exception as e:
        print(f"Vision Test Error: {e}")

if __name__ == "__main__":
    test_vision()
