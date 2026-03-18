# 🤖 J.A.R.V.I.S. — Advanced AI Assistant

J.A.R.V.I.S. is a powerful, multimodal AI assistant designed for seamless interaction via voice, text, vision, and document analysis.

---

## 🚀 Key Features

### 🎙️ Multimodal Interaction
- **Voice Recognition**: Real-time voice commands with wake-word support.
- **Bi-lingual TTS**: Crystal clear speech synthesis in both English and Hindi.
- **Vision Support**: Attach images for instant AI analysis and description.
- **PDF Analysis**: Upload PDF documents for intelligent text extraction and contextual querying.

### 🖥️ High-End UI/UX
- **Integrated Compose HUD**: Beautifully redesigned input box with embedded file previews (Images & PDFs) stacked above text entry.
- **Glassmorphic Design**: A premium, futuristic aesthetic with blurred backgrounds, neon glows, and smooth animations.
- **Action Sidebar**: Quick access to Images, Documents, Code, Projects, and Settings.
- **Live Telemetry**: Real-time monitoring of system stats (CPU, RAM, Battery, Brightness) directly in the interface.

### ⚡ Developer & Power Features
- **Hot-Reload (`Ctrl + Shift + R`) **: Instantly refresh the frontend and restart the backend without losing state.
- **Web Search Integration**: JARVIS can browse the live web to provide up-to-date answers using DuckDuckGo.
- **System Control**: Execute commands like opening applications, checking status, and more.

---

## 🛠️ Tech Stack
- **Backend**: Flask, Flask-SocketIO (Real-time communication)
- **AI Core**: OpenRouter API (Access to top-tier LLMs like GPT-4, Claude 3.5), Hugging Face (Fallback)
- **Document Processing**: PyMuPDF (fitz)
- **Voice**: Google Speech Recognition & pyttsx3/gTTS
- **Frontend**: Vanilla JS, Modern CSS (Glassmorphism), HTML5

---

## 🏃 Getting Started

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd Jarvis

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory and add your API keys:
```env
OPENROUTER_API_KEY=your_key_here
```

### 4. Run J.A.R.V.I.S.
```bash
python app.py
```
The application will be available at `http://localhost:5001`.

---

## ⌨️ Shortcuts
- `Ctrl + Shift + R`: Hot-Reload (Restart server and refresh browser)
- `Enter`: Send message
- `Click Mic`: Toggle voice listening

---

