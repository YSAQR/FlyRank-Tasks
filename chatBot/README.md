# 🤖 AI-Powered Smart ChatBot

An interactive, smart AI Chatbot built using **Python**, **Streamlit**, and **Google Gemini API**, featuring persistent conversational memory (chat history) and context-aware responses.

---

## ✨ Features
- 💬 **Interactive UI**: Clean, modern interface built with Streamlit.
- 🧠 **Conversational Memory**: Retains chat history across user messages using Streamlit's `session_state`.
- ⚡ **Powered by Gemini**: Integrates Google's latest Generative AI models.
- 🔒 **Secure Configuration**: Uses `python-dotenv` for API key management without leaking secrets.

---

## 📁 Project Structure
```text
chatBot/
├── .env                # Local secrets (API Key) - Ignored by Git
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules
├── requirements.txt    # Project dependencies
├── app.py              # Main Streamlit application
└── README.md           # Documentation
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YSAQR/Ai-Smart-ChatBot.git
cd Ai-Smart-ChatBot
```

### 2. Set up virtual environment & dependencies
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory (or copy `.env.example`):
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. Run the Application
```bash
streamlit run app.py
```

---

## 🛠️ Built With
- [Python 3.10+](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Google Generative AI SDK](https://ai.google.dev/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
