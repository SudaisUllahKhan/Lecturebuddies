# 🎓 LectureBuddies - Educational AI Assistant

A comprehensive educational platform that uses AI to help students understand their lecture materials. Upload your lecture notes, slides, or any educational content and get instant answers to your questions!

## ✨ Features

- **📚 Document Upload**: Support for PDF, DOCX, DOC, TXT, and images (OCR)
- **🤖 AI-Powered Chat**: Ask questions about your lecture materials
- **📋 Auto-Summary**: Generate comprehensive summaries of uploaded content
- **❓ Study Questions**: Get practice questions based on your materials
- **📝 Quiz Generator**: Create MCQs by topic or from files/text
- **🎤 Live Transcription**: Record or upload audio and transcribe with Faster-Whisper
- **🌐 Translation**: Translate text between languages
- **📖 Flash Cards**: Generate study flash cards
- **🎨 Modern Interface**: Beautiful Streamlit UI

## 🚀 Quick Start

### Prerequisites

- Python 3.11 (recommended)
- Groq API key
- (Optional, for OCR) Tesseract OCR installed on Windows at `C:\Program Files\Tesseract-OCR\tesseract.exe` or available in PATH

### Installation

1. Clone or download the project
   ```bash
   git clone <repository-url>
   cd LectureBuddies
   ```

2. Create and activate a virtual environment (recommended)
   ```bash
   python -m venv venv
   venv\\Scripts\\activate  # on Windows
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment variables
   - Copy `env_example.txt` to `.env`
   - Add your Groq API key:
   ```
   GROQ_API_KEY=your_actual_api_key_here
   ```

5. Run the application
   ```bash
   streamlit run main.py
   ```

6. Open your browser
   - The app will open at `http://localhost:8501`

## 📖 How to Use

### 1. Upload Documents
- Use the feature sidebars (Chatbot/Quiz/Flash Cards) to upload documents
- Supported formats: PDF, DOCX, DOC, TXT, PNG/JPG (OCR)

### 2. Chat with LectureBuddies
- Ask questions about your uploaded materials
- Use quick prompts for faster onboarding

### 3. Generate Quizzes & Flash Cards
- Choose difficulty and number of items
- Generate from uploaded files, pasted text, or prompts

### 4. Live Lecture Recording
- Record via microphone or upload audio files for transcription
- Transcripts can be saved or downloaded

### 5. Translation
- Translate text or uploaded documents between languages

## 🛠️ Technical Details

### Architecture
- **Frontend**: Streamlit
- **AI Engine**: Groq `chat.completions` API (e.g., `llama-3.1-8b-instant`)
- **Transcription**: Faster-Whisper
- **Document Processing**: Custom `document_processor.py` (PyPDF2, python-docx, OCR via Tesseract)

### Key Components
- `main.py`: Main Streamlit application (all features)
- `document_processor.py`: Document parsing and OCR
- `requirements.txt`: Python dependencies

### Supported File Formats
- **PDF**: PyPDF2 text extraction
- **DOCX/DOC**: python-docx
- **TXT**: Plain text
- **Images**: OCR via Tesseract

## 🔧 Configuration

### Environment Variables (.env)
```
GROQ_API_KEY=your_api_key_here
```

### OCR (Windows)
- Install Tesseract from: `https://github.com/tesseract-ocr/tesseract`
- Default path used by the app: `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`
- You can also add Tesseract to your PATH instead.

## 🚨 Troubleshooting

1. "Missing API key"
   - Ensure `.env` exists and contains `GROQ_API_KEY`

2. OCR errors or no text from images
   - Verify Tesseract is installed and accessible
   - Confirm path is correct or Tesseract is in PATH

3. Microphone/recording errors
   - Check audio device permissions
   - Ensure sample rate 16kHz is supported

4. Slow responses
   - Large files can take time; try smaller inputs

## 📝 Project Structure

```
LectureBuddies/
├── main.py                 # Main Streamlit application
├── document_processor.py   # Document parsing & OCR
├── requirements.txt        # Python dependencies
├── env_example.txt         # Environment variables template
├── README.md               # This file
└── temp/                   # Temporary files
```

## 🤝 Contributing

This is an FYP (Final Year Project) for educational purposes. Feel free to:
- Report bugs and issues
- Suggest new features
- Improve documentation

## 📄 License

This project is created for educational purposes as part of a Final Year Project.

---

**🎓 Happy Learning with LectureBuddies!**







