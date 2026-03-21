# 🤖 J.A.R.V.I.S. — Advanced AI Assistant

J.A.R.V.I.S. is a powerful, multimodal AI assistant designed for seamless interaction via voice, text, vision, and document analysis. It features a premium, immersive user interface and uncapped intelligence.

---

## 🚀 Key Features

### 🎙️ Multimodal Interaction
- **Voice Recognition & Continuous Listening**: Real-time voice commands that listen continuously until a pause is detected.
- **Voice Chat (Call) Mode**: Hands-free, immersive voice conversation interface.
- **Bi-lingual TTS**: Crystal clear speech synthesis in both English and Hindi.
- **Vision Support**: Attach images for instant AI analysis and multimodal routing.
- **PDF Analysis**: Upload PDF documents for intelligent text extraction and contextual querying.

### 🤖 Uncapped AI Capabilities
- **Exhaustive Responses**: Removed token limits and truncations to allow for comprehensive, highly detailed AI answers.
- **Enhanced Accuracy**: Intelligent routing and optimized web search integration.
- **Web Search**: JARVIS can browse the live web to provide up-to-date answers using DuckDuckGo.

### 🖥️ High-End UI/UX
- **Maximized Chat Interface**: Optimized screen layout for an immersive and focused conversational experience.
- **Integrated Compose HUD**: Beautiful input box with embedded file previews (Images & PDFs).
- **Glassmorphic Design**: A premium aesthetic with blurred backgrounds, neon glows, and smooth animations.
- **Action Sidebar**: Quick access to New Chat, My Stuff, and Settings.
- **Live Telemetry**: Real-time monitoring of system stats (CPU, RAM, Battery, Brightness).

### 🔐 Security & Identity
- **Supabase Authentication**: Secure login via Google OAuth.
- **Deferred Login**: Frictionless onboarding. Authentication is only prompted upon your first interaction (sending a message, using voice/files) and can be accessed via Settings.

### ⚡ Developer & Power Features
- **Hot-Reload (`Ctrl + Shift + R`)**: Instantly refresh the frontend and restart the backend without losing state.
- **Monetization Ready**: Configured with proper `ads.txt` and consistent favicons across all platforms.

---

## 🛠️ Tech Stack
- **Backend**: Flask, Flask-SocketIO (Real-time communication)
- **AI Core**: OpenRouter API (Access to top-tier LLMs like GPT-4o, Claude 3.5 Sonnet), Hugging Face
- **Authentication**: Supabase (Google OAuth)
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
Create a `.env` file in the root directory and add your API credentials:
```env
OPENROUTER_API_KEY=your_openrouter_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
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
- `Click Mic / Orb`: Toggle voice listening

---
