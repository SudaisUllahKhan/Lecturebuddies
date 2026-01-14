import streamlit as st
import requests
import PyPDF2
from docx import Document
import io
import os
import json
import base64
import time
from dotenv import load_dotenv
from document_processor import DocumentProcessor
import sounddevice as sd
import numpy as np
import soundfile as sf
import threading
import queue
import tempfile
from PIL import Image
import pytesseract
import re
import speech_recognition as sr
from faster_whisper import WhisperModel
from database import (
    create_user, 
    authenticate_user, 
    get_user_stats, 
    increment_activity,
    save_recording,
    save_quiz,
    update_user_profile,
    get_full_user_data,
    delete_user_account
)


  
   
  
    
   
   
 
    
    
  





# ==========================
import random

# ==========================
# PAGE CONFIGURATION
# ==========================
st.set_page_config(
    page_title="Lecturebuddies - Educational Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_random_quote():
    """Returns a random motivational quote with author"""
    quotes = [
        {"text": "The expert in anything was once a beginner.", "author": "Helen Hayes"},
        {"text": "Success is the sum of small efforts, repeated day in and day out.", "author": "Robert Collier"},
        {"text": "Live as if you were to die tomorrow. Learn as if you were to live forever.", "author": "Mahatma Gandhi"},
        {"text": "It always seems impossible until it's done.", "author": "Nelson Mandela"},
        {"text": "Don't watch the clock; do what it does. Keep going.", "author": "Sam Levenson"},
        {"text": "Education is the passport to the future, for tomorrow belongs to those who prepare for it today.", "author": "Malcolm X"},
        {"text": "The beautiful thing about learning is that no one can take it away from you.", "author": "B.B. King"},
        {"text": "Study hard, for the well is deep, and our brains are shallow.", "author": "Richard Baxter"},
        {"text": "Motivation is what gets you started. Habit is what keeps you going.", "author": "Jim Ryun"},
        {"text": "Your future is created by what you do today, not tomorrow.", "author": "Robert Kiyosaki"},
        {"text": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
        {"text": "Strive for progress, not perfection.", "author": "Bill Phillips"},
        {"text": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
        {"text": "There are no shortcuts to any place worth going.", "author": "Beverly Sills"},
        {"text": "Focus on the goal, not the obstacle.", "author": "Anonymous"}
    ]
    return random.choice(quotes)

# ==========================
# SESSION STATE INITIALIZATION
# ==========================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        # Login/Auth
        "authenticated": False,
        "current_user": None,
        "user_id": None, 
        "user_stats": {}, 
        "current_page": "dashboard",

        # Chatbot & Summarization
        "messages": [],
        "uploaded_files": [],
        "document_contents": {},
        "chat_model": "llama-3.1-8b-instant",
        "chat_temperature": 0.7,

        # Quiz Generator
        "quiz_output": None,
        "num_questions": 5,
        "difficulty": "Medium",
        "quiz_model": "llama-3.1-8b-instant",
        "quiz_temperature": 0.7,

        # Live Lecture Recording
        "rec_thread": None,
        "audio_queue": None,
        "recording": False,
        "transcript": "",
        "partial_transcript": "",
        "chunks_saved": [],

        # Dashboard
        "selected_feature": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ==========================
# LOAD API KEY
# ==========================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# ==========================
# LOGO HELPER
# ==========================
def get_logo_svg(size_px=80, font_size_px=42):
    """Returns the SVG logo string with adjustable size wrapped in a link"""
    svg_icon = f'<svg class="lb-logo-svg" width="{size_px}" height="{size_px}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="position: relative; top: 10px;"><path d="M50 15L20 28L50 41L80 28L50 15Z" fill="#2D005E"/><path d="M70 32V45" stroke="#2D005E" stroke-width="2"/><circle cx="50" cy="48" r="15" fill="#2D005E"/></svg>'
    font_style = f'font-family: \'Georgia\', serif; font-size: {font_size_px}px; font-weight: 900; color: #2D005E; letter-spacing: -1px; margin-left: -10px;'
    
    return f'<a href="https://lecturebuddies.streamlit.app" target="_blank" style="text-decoration: none; display: flex; align-items: center; gap: 0px; cursor: pointer;">{svg_icon}<span class="lb-logo-text" style="{font_style}">Lecturebuddies</span></a>'

# ==========================
# GLOBAL STYLING - LECTUREBUDDIES THEME
# ==========================
st.markdown(
    """
    <style>
    /* Removed Poppins @import */

    /* Prevent scrolling on login page only */
    .login-page body, .login-page html {
        overflow-y: hidden !important;
        height: 100vh !important;
    }

    /* Main App Styling */
    .stApp {
        font-family: 'Georgia', serif;
        background-color: #f5f7fa;
    }

    /* Hide Streamlit default elements */
    MainMenu {visibility: visible;}
    footer {visibility: visible;}
    header {visibility: visible;}
    
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0) !important; 
        height: 0px !important; 
    }

    /* Main Title */
    .main-title {
        text-align: center;
        font-size: clamp(28px, 5vw, 42px);
        font-weight: 800;
        background: linear-gradient(90deg, #4e54c8, #8f94fb, #4e54c8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 8px;
        font-family: 'Georgia', serif;
    }

    /* Tagline */
    .tagline {
        text-align: center;
        font-size: clamp(14px, 2vw, 16px);
        color: #666;
        margin-bottom: 15px;
        font-family: 'Georgia', serif;
    }

    /* Gradient Line */
    hr.gradient {
        border: none;
        height: 3px;
        background: linear-gradient(90deg, #4e54c8, #8f94fb, #4e54c8);
        border-radius: 50px;
        margin: 15px auto;
        max-width: 400px;
    }

    /* App Brand Title (Login Page) */
    .app-brand-title {
        font-size: clamp(28px, 5vw, 42px);
        font-weight: 800;
        color: #4e54c8;
        text-shadow: 2px 2px 4px rgba(78, 84, 200, 0.2);
        font-family: 'Georgia', serif;
        margin-bottom: 8px;
        text-align: center;
    }

    /* ==============================================
       DASHBOARD CONTENT STYLING FIXES
       ============================================== */

    .main .block-container {
        padding: clamp(1rem, 3vw, 3rem) !important;
        max-width: 1400px;
        margin: 0 auto;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 10px !important; 
        padding-bottom: 10px !important;
    }

    /* ==============================================
       SIDEBAR
       ============================================== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%);
        border-right: 1px solid #e0e7ff;
    }

    .sidebar-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #9ca3af;
        padding: 0 20px;
        margin-bottom: 12px;
        font-family: 'Georgia', serif !important;
    }

    /* Sidebar Button Styling */
    [data-testid="stSidebar"] button {
        width: 100% !important;
        text-align: left !important;
        padding: 8px 15px !important;
        margin: 1px 0 !important;
        border-radius: 8px !important;
        background: transparent !important;
        border: none !important;
        color: #4b5563 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        transition: all 0.3s ease !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        white-space: nowrap !important;
        min-height: 32px !important;
        font-family: 'Georgia', serif !important;
    }

    [data-testid="stSidebar"] button:hover {
        background: linear-gradient(135deg, #4e54c8, #8f94fb) !important;
        color: white !important;
        transform: translateX(5px);
    }

    /* Logout Button in Sidebar - Special Styling */
    [data-testid="stSidebar"] button[key="logout_btn"],
    [data-testid="stSidebar"] .stButton > button[key="logout_btn"],
    [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child button,
    [data-testid="stSidebar"] button[aria-label*="Logout"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }

    [data-testid="stSidebar"] button[key="logout_btn"]:hover,
    [data-testid="stSidebar"] .stButton > button[key="logout_btn"]:hover,
    [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child button:hover,
    [data-testid="stSidebar"] button[aria-label*="Logout"]:hover {
        background: linear-gradient(90deg, #8f94fb, #764ba2) !important;
        transform: translateX(5px) translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }

    /* Welcome Styles */
    .welcome-container {
        text-align: center;
        padding: clamp(15px, 3vw, 30px);
        background: linear-gradient(90deg, #8f94fb, #764ba2);
        border-radius: 15px;
        border: 1px solid #d1d9ff;
        margin: 10px 0;
    }

    .welcome-title {
        color: #ffffff !important;
        font-size: clamp(18px, 4vw, 24px);
        font-weight: 700;
        margin-bottom: 10px;
        font-family: 'Georgia', serif;
    }

    .welcome-text {
        color: #ffffff !important;
        font-size: clamp(14px, 2vw, 16px);
        font-family: 'Georgia', serif;
    }

    /* ==============================================
       LOGIN/SIGNUP PAGES
       ============================================== */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
        padding: 40px 20px;
    }

    .login-box-wrapper {
        background: white;
        padding: 45px 40px;
        border-radius: 16px;
        box-shadow: 0 10px 50px rgba(78, 84, 200, 0.12);
        max-width: 420px;
        width: 100%;
    }

    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }

    .login-title {
        font-size: 32px;
        font-weight: 700;
        color: #4e54c8;
        margin-bottom: 8px;
        font-family: 'Georgia', serif;
    }

    .login-subtitle {
        font-size: 15px;
        color: #667eea;
        font-weight: 400;
        font-family: 'Georgia', serif;
    }

    /* Input Field Styling */
    .login-input-wrapper {
        margin-bottom: 20px;
    }

    .login-label {
        display: block;
        font-size: 14px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 8px;
        font-family: 'Georgia', serif;
    }

    /* Override Streamlit input styling */
    .stTextInput > div > div > input,
    .stTextInput > div > input {
        border: 2px solid #e5e7eb !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        font-family: 'Georgia', serif !important;
        transition: all 0.3s ease !important;
        height: auto !important;
        width: 100% !important;
        background: #f9fafb !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextInput > div > input:focus {
        border-color: #667eea !important;
        outline: none !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1) !important;
        background: white !important;
    }

    /* Input Field Labels - Fixed Black, No Bold, No Hover */
    .stTextInput label,
    .stTextInput label p {
        color: #000000 !important;
        font-weight: 400 !important;
        transition: none !important;
    }

    .stTextInput label:hover,
    .stTextInput label:hover p {
        color: #000000 !important;
        font-weight: 400 !important;
    }

    /* Modern Button Styling */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 9px 12px !important;
        border: none !important;
        border-radius: 10px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        font-family: 'Georgia', serif !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        margin-top: 10px !important;
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #8f94fb, #764ba2) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }

    /* Login/Signup Page Button Styling - Higher Specificity */
    .stTabs .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #4e54c8, #8f94fb) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 9px 12px !important;
        border: none !important;
        border-radius: 10px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        font-family: 'Georgia', serif !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        margin-top: 10px !important;
    }

    .stTabs .stButton > button:hover {
        background: linear-gradient(135deg, #8f94fb, #4e54c8) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }

    /* Create Account Button - Specific Gradient */
    button[data-testid="baseButton-secondary"]:has-text("Create Account"),
    div[data-testid="stVerticalBlock"] button:nth-of-type(2) {
        background: linear-gradient(135deg, #4e54c8, #8f94fb) !important;
    }

    button[data-testid="baseButton-secondary"]:has-text("Create Account"):hover,
    div[data-testid="stVerticalBlock"] button:nth-of-type(2):hover {
        background: linear-gradient(135deg, #8f94fb, #4e54c8) !important;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background-color: #f3f4f6;
        border-radius: 12px;
        padding: 6px;
        margin-bottom: 30px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-family: 'Georgia', serif;
        font-weight: 600;
        font-size: 15px;
        padding: 9px 20px;
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        border-radius: 10px !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }

    /* Links Styling */
    .login-links {
        text-align: center;
        margin-top: 25px;
        padding-top: 25px;
        border-top: 1px solid #e5e7eb;
        font-family: 'Georgia', serif;
    }

    .login-link {
        color: #667eea;
        text-decoration: none;
        font-size: 14px;
        font-weight: 500;
        transition: color 0.3s ease;
        font-family: 'Georgia', serif;
    }

    .login-link:hover {
        color: #764ba2;
        text-decoration: underline;
    }

    /* Primary Button Override - Custom Gradient */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(90deg, #8f94fb, #764ba2) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }

    /* ==============================================
       DASHBOARD CONTENT STYLING
       ============================================== */
    .dashboard-header {
        background: linear-gradient(135deg, #f8f9ff, #e8ecff);
        padding: clamp(20px, 4vw, 30px);
        border-radius: 16px;
        border: 1px solid #d1d9ff;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(78, 84, 200, 0.08);
    }

    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(78, 84, 200, 0.12);
        border-color: #d1d9ff;
    }

    /* Chat Styling */
    .user-bubble, .assistant-bubble {
        padding: 12px 18px;
        border-radius: 18px;
        max-width: clamp(70%, 85%, 90%);
        font-family: 'Georgia', serif;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        word-wrap: break-word;
    }

    /* Demo Button Styling */
    .dev-access-container {
        margin-top: 30px;
        padding: 20px;
        background: #fff5f5;
        border: 1px dashed #feb2b2;
        border-radius: 12px;
        text-align: center;
    }

    /* Streamlit Default Element Hides */
    .stDeployButton { display: none; }

    /* User Info Hover & Click Effects */
    .user-info:hover {
        background: linear-gradient(135deg, #e8ecff, #d6d9ff) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(78, 84, 200, 0.15) !important;
    }

    /* ==============================================
       MEDIA QUERIES FOR RESPONSIVENESS
       ============================================== */
    
    /* Extra Small Devices (Portrait Phones) */
    @media only screen and (max-width: 480px) {
        .main .block-container {
            padding: 0.75rem !important;
        }
        .login-box-wrapper {
            padding: 20px 15px !important;
        }
        .stButton > button {
            padding: 8px 10px !important;
        }
    }

    /* Mobile Devices (Phones) */
    @media only screen and (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem !important; 
            padding-bottom: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Navigation */
        .nav-container {
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }
        
        .nav-title {
            font-size: 1.2rem !important;
            text-align: center;
        }

        /* Chat Bubbles */
        .user-bubble, .assistant-bubble {
            max-width: 92% !important;
            padding: 10px 14px !important;
            font-size: 13px !important;
        }
        
        /* Sidebar Elements */
        [data-testid="stSidebar"] {
            min-width: 250px !important;
        }
    }

    /* Tablets and Small Laptops */
    @media only screen and (min-width: 769px) and (max-width: 1023px) {
        .main .block-container {
            padding: 1.5rem !important;
        }
        .user-bubble, .assistant-bubble {
            max-width: 85% !important;
        }
        .login-box-wrapper {
            max-width: 400px;
        }
    }

    /* Small Laptops (13" laptops, 1024-1366px) */
    @media only screen and (min-width: 1024px) and (max-width: 1366px) {
        .main .block-container {
            padding: 1.75rem !important;
            max-width: 1100px;
        }
        
        .user-bubble, .assistant-bubble {
            max-width: 80% !important;
            font-size: 14px !important;
        }
        
        .login-box-wrapper {
            max-width: 420px;
            padding: 40px 35px;
        }
        
        [data-testid="stSidebar"] {
            min-width: 280px !important;
        }
        
        .dashboard-header {
            padding: clamp(18px, 3vw, 25px);
        }
        
        .welcome-container {
            padding: clamp(12px, 2.5vw, 25px);
        }
    }

    /* Medium Laptops (14-15" laptops, 1367-1600px) */
    @media only screen and (min-width: 1367px) and (max-width: 1600px) {
        .main .block-container {
            padding: 2rem !important;
            max-width: 1300px;
        }
        
        .user-bubble, .assistant-bubble {
            max-width: 78% !important;
        }
        
        .login-box-wrapper {
            max-width: 440px;
            padding: 45px 40px;
        }
        
        [data-testid="stSidebar"] {
            min-width: 300px !important;
        }
        
        .dashboard-header {
            padding: clamp(20px, 3.5vw, 28px);
        }
    }

    /* Large Laptops (15-17" Full HD, 1601-1920px) */
    @media only screen and (min-width: 1601px) and (max-width: 1920px) {
        .main .block-container {
            padding: 2.5rem !important;
            max-width: 1400px;
        }
        
        .user-bubble, .assistant-bubble {
            max-width: 75% !important;
        }
        
        .login-box-wrapper {
            max-width: 460px;
            padding: 50px 45px;
        }
        
        [data-testid="stSidebar"] {
            min-width: 320px !important;
        }
        
        .dashboard-header {
            padding: clamp(22px, 4vw, 30px);
        }
        
        .stButton > button {
            font-size: 16px !important;
        }
    }

    /* Extra Large Screens (4K laptops, monitors, 1921px+) */
    @media only screen and (min-width: 1921px) {
        .main .block-container {
            padding: 3rem !important;
            max-width: 1600px;
        }
        
        .user-bubble, .assistant-bubble {
            max-width: 70% !important;
            font-size: 15px !important;
        }
        
        .login-box-wrapper {
            max-width: 480px;
            padding: 55px 50px;
        }
        
        [data-testid="stSidebar"] {
            min-width: 340px !important;
        }
        
        .dashboard-header {
            padding: 30px;
        }
        
        .stButton > button {
            font-size: 16px !important;
            padding: 10px 14px !important;
        }
        
        .main-title {
            font-size: 48px;
        }
    }

    /* Global Tab Hover Effect */
    button[data-baseweb="tab"]:hover {
        background: linear-gradient(90deg, #4e54c8, #8f94c8) !important;
        color: white !important;
        border-radius: 0px !important;
        transition: all 0.3s ease !important;
    }

    /* Custom Font Color Override - Tabs */
    .st-emotion-cache-1jsf23j, 
    .st-emotion-cache-1jsf23j p, 
    .st-emotion-cache-1jsf23j span {
        color: #000000 !important;
        transition: color 0.3s ease !important;
    }

    .st-emotion-cache-1jsf23j:hover,
    .st-emotion-cache-1jsf23j:hover p,
    .st-emotion-cache-1jsf23j:hover span,
    .st-emotion-cache-1jsf23j[aria-selected="true"],
    .st-emotion-cache-1jsf23j[aria-selected="true"] p,
    .st-emotion-cache-1jsf23j[data-selected="true"] {
        color: #FFFFFF !important;
    }

    /* Container Background Override */
    .st-c2 {
        background-color: #764ba2 !important;
    }

    /* Custom Emotion Cache Color Override */
    .st-emotion-cache-11xx4re {
        color: #8f94fb !important;
    }

    .st-emotion-cache-1lsfsc6 {
        background: linear-gradient(90deg, #8f94fb, #764ba2) !important;
    }

    .st-emotion-cache-pxambx {
        background: linear-gradient(90deg, #8f94fb, #764ba2) !important;
    }

    /* Global Placeholder Styling */
    ::placeholder {
        color: #8f94fb !important;
        opacity: 0.8 !important;
    }

    /* Slider Styling */
    .stSlider > div > div > div > div {
        background-color: #8f94fb !important;
    }
    
    .stSlider > div > div > div {
        background-color: rgba(143, 148, 251, 0.2) !important;
    }
    
    .stSlider [role="slider"] {
        background-color: #8f94fb !important;
    }
    
    .stSlider label {
        color: #8f94fb !important;
        font-weight: 600 !important;
    }

    /* Mobile Responsiveness for Login Logo */
    @media (max-width: 480px) {
        .login-logo-wrapper .lb-logo-svg {
            width: 60px !important;
            height: 60px !important;
            min-width: 60px !important;
        }
        .login-logo-wrapper .lb-logo-text {
            font-size: 28px !important;
            margin-left: -5px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================
# SIMPLE PASSWORD RESET
# ==========================
def show_simple_password_reset():
    """Simple password reset using only username"""
    st.markdown("""
        <div class="welcome-container">
            <h1 class="welcome-title">🔐 Reset Password</h1>
            <p class="welcome-text">Enter your username to set a new password</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        reset_username = st.text_input("Username", placeholder="Enter your username", key="reset_user_input")
        
        if reset_username:
            from database import get_user_id_by_username, update_user_profile
            user_id = get_user_id_by_username(reset_username)
            
            if user_id:
                st.success(f"User '{reset_username}' found. Enter your new password below.")
                new_pass = st.text_input("New Password", type="password", key="new_pass_simple")
                confirm_pass = st.text_input("Confirm New Password", type="password", key="confirm_pass_simple")
                
                if st.button("Update Password", use_container_width=True):
                    if new_pass == confirm_pass:
                        if len(new_pass) < 6:
                            st.error("Password must be at least 6 characters long")
                        else:
                            success, message = update_user_profile(user_id, new_password=new_pass)
                            if success:
                                st.success("Password updated successfully!")
                                time.sleep(1.5)
                                st.session_state.show_simple_reset = False
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.error("Passwords do not match")
            else:
                st.error("User not found")
        
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.show_simple_reset = False
            st.rerun()

# ==========================
# LOGIN AND SIGNUP SECTION
# ==========================
def show_login_page():
    """Display login/signup page with WordPress-style centered form"""
    
    # --- CSS INJECTION FOR BOLD FONTS ---
    st.markdown(
        """
        <style>
        /* Make the Labels (e.g. "Username") Bold */
        .stTextInput label p {
            font-weight: 700 !important;
            font-size: 15px !important;
            font-family: 'Georgia', serif !important;
        }
        
        /* Make the Placeholders (e.g. "Enter your username") Bold */
        .stTextInput input::placeholder {
            font-weight: 700 !important;
            color: #8f94fb !important; /* Updated brand color */
            font-family: 'Georgia', serif !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    # ------------------------------------

    # Center column approach for login form
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Display SVG logo and tagline
        logo_html = get_logo_svg(size_px=100, font_size_px=48)
        tagline_html = '<div style="text-align: center; margin-top: 5px; margin-bottom: 30px;"><p style="color: #666; font-size: 16px; font-family: \'Georgia\', serif; margin-top: 5px; line-height: 1.6;">Your intelligent study companion—learn, create, and excel with AI</p></div>'
        st.markdown(f'<div class="login-logo-wrapper" style="display: flex; flex-direction: column; align-items: center; margin-bottom: 20px;">{logo_html}{tagline_html}</div>', unsafe_allow_html=True)
        
       
        
        # Login/Signup Tabs
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

            if st.button("Login", key="login_btn", help="Login to your account"):
                if username and password:
                    # Authenticate using database
                    success, message, user_id = authenticate_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        st.session_state.user_id = user_id
                        # Load user stats
                        st.session_state.user_stats = get_user_stats(user_id)
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter both username and password")
            
            # Simple Forgot Password Link
            st.markdown('<div style="text-align: center; margin-top: 10px;">', unsafe_allow_html=True)
            if st.button("Forgot Password?", key="forgot_pass_simple_btn"):
                st.session_state.show_simple_reset = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            

        with tab2:
            new_username = st.text_input("Choose Username", placeholder="Enter your username", key="signup_username")
            new_email = st.text_input("Email (optional)", placeholder="Enter your email", key="signup_email")
            new_password = st.text_input("Choose Password", type="password", placeholder="Enter your password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="confirm_password")

            if st.button("Create Account", key="signup_btn", help="Create new account"):
                if new_username and new_password and confirm_password:
                    if new_password == confirm_password:
                        if len(new_password) < 6:
                            st.error("Password must be at least 6 characters long")
                        else:
                            # Create user in database
                            success, message, user_id = create_user(new_username, new_password, new_email if new_email else None)
                            if success:
                                st.session_state.authenticated = True
                                st.session_state.current_user = new_username
                                st.session_state.user_id = user_id
                                # Initialize user stats (will be all zeros for new user)
                                st.session_state.user_stats = get_user_stats(user_id)
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.error("Passwords don't match")
                else:
                    st.warning("Please fill in username and password fields")
        
        # Developer Demo Access (Temporary)
        st.markdown('<div class="dev-access-container">', unsafe_allow_html=True)
        st.markdown('<p class="dev-access-title">Developer Tools</p>', unsafe_allow_html=True)
        if st.button("🚀 Demo Access (Dev Only)", key="demo_btn", help="Bypass login for development"):
            # Use Developer account
            # Create if doesn't exist, otherwise authenticate
            success, message, user_id = create_user("Developer", "devpass123", "dev@lecturebuddies.com")
            if not success and "exists" in message:
                success, message, user_id = authenticate_user("Developer", "devpass123")
            
            if success:
                st.session_state.authenticated = True
                st.session_state.current_user = "Developer"
                st.session_state.user_id = user_id
                st.session_state.user_stats = get_user_stats(user_id)
                st.success("Welcome, Developer! Access granted.")
                time.sleep(1)
                st.rerun()
            else:
                # Fallback if DB is completely broken
                st.session_state.authenticated = True
                st.session_state.current_user = "Developer"
                st.session_state.user_id = 1
                st.session_state.user_stats = {
                    "study_sessions": 0, "quizzes_created": 0, "recordings_count": 0,
                    "flashcards_created": 0, "notes_count": 0, "total_study_time": 0
                }
                st.warning("DB Access failed, using offline developer mode.")
                time.sleep(1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# DASHBOARD LAYOUT SECTION
# ==========================
def show_dashboard():
    """Display main dashboard with sidebar and content area"""
    
    # Initialize profile dropdown state
    if "show_profile_dropdown" not in st.session_state:
        st.session_state.show_profile_dropdown = False

    # Add JavaScript to detect sidebar state and show/hide floating toggle button
    st.markdown(
        """
        <script>
        // Function to check sidebar state and toggle floating button
        function checkSidebarState() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            let floatingToggle = document.getElementById('floating-sidebar-toggle');
            
            if (sidebar) {
                const isCollapsed = sidebar.classList.contains('css-17eq0hr') || 
                                  sidebar.style.transform === 'translateX(-100%)' ||
                                  window.getComputedStyle(sidebar).width === '0px';
                
                if (isCollapsed || !sidebar.offsetParent) {
                    # Sidebar is collapsed - show floating button
                    if (!floatingToggle) {
                        floatingToggle = document.createElement('div');
                        floatingToggle.id = 'floating-sidebar-toggle';
                        floatingToggle.className = 'sidebar-collapsed-toggle';
                        floatingToggle.onclick = function() {
                            # Click the collapse button to expand
                            const toggleBtn = document.querySelector('button[data-testid="baseButton-header"]');
                            if (toggleBtn) toggleBtn.click();
                        };
                        document.body.appendChild(floatingToggle);
                    }
                } else {
                    # Sidebar is expanded - hide floating button
                    if (floatingToggle) {
                        floatingToggle.remove();
                    }
                }
            }
        }
        
        // Check sidebar state on load and periodically
        checkSidebarState();
        setInterval(checkSidebarState, 500);
        
        // Also check when sidebar is toggled
        document.addEventListener('click', function(e) {
            if (e.target.closest('button[data-testid="baseButton-header"]')) {
                setTimeout(checkSidebarState, 350);
            }
        });
        </script>
        """,
        unsafe_allow_html=True
    )

    # --- RESPONSIVE TOP NAVIGATION BAR ---
    with st.container():
        # CSS for horizontal alignment and styling
        st.markdown("""
            <style>
                .nav-container {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.5rem 1rem;
                    background-color: transparent;
                    margin-bottom: 1rem;
                }
                /* Navbar Container Styling */
                div[data-testid="stHorizontalBlock"]:has(img[src^="data:image"]) {
                    background: linear-gradient(135deg, #4e54c8, #8f94fb);
                    padding: 1.5rem 2rem;
                    border-radius: 16px;
                    box-shadow: 0 4px 20px rgba(78, 84, 200, 0.2);
                    align-items: center;
                    margin-bottom: 0.5rem;
                }

                /* User Profile Button Styling - Glass Effect */
                [data-testid="stPopover"] > button {
                    background: rgba(255, 255, 255, 0.15) !important;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2) !important;
                    color: white !important;
                    border-radius: 12px !important;
                    padding: 0.5rem 1rem !important;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
                    font-family: 'Georgia', serif !important;
                    font-weight: 600 !important;
                    height: auto !important;
                    transition: all 0.3s ease !important;
                }
                [data-testid="stPopover"] > button:hover {
                    transform: translateY(-2px) !important;
                    background: rgba(255, 255, 255, 0.25) !important;
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
                    border: 1px solid rgba(255, 255, 255, 0.4) !important;
                }
                [data-testid="stPopover"] > button p {
                    font-size: 16px !important;
                    font-weight: 600 !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Flex-like layout using columns  
        col_nav_left, col_nav_spacer, col_nav_right = st.columns([4, 6, 2])
        
        with col_nav_left:
            # Display SVG logo in navigation
            st.markdown(f'<div style="display: flex; align-items: center; width: fit-content;">{get_logo_svg(size_px=80, font_size_px=30)}</div>', unsafe_allow_html=True)
            









            
        with col_nav_right:
            # Profile Menu logic
            # Fetch display name and user info
            user_id = st.session_state.get("user_id")
            current_user = st.session_state.get("current_user", "Account")
            display_name = st.session_state.get("user_display_name")
            
            # Normalize display name
            user_display = display_name or (current_user if isinstance(current_user, str) else current_user.get("username", "Account"))
            
            with st.popover(f"👤 {user_display}", use_container_width=True):
                st.markdown("### 👤 User Account")
                if isinstance(current_user, dict):
                    st.markdown(f"**Email:** {current_user.get('email', 'N/A')}")
                    st.markdown(f"**Role:** {current_user.get('role', 'User')}")
                else:
                    st.markdown(f"**User:** {current_user}")
                
                if st.button("👤 View Profile", key="nav_view_profile_btn", use_container_width=True):
                    st.session_state.selected_feature = "profile"
                    st.rerun()
                
                st.markdown("---")
                if st.button("🚪 Log Out", key="nav_logout_btn", use_container_width=True, type="primary"):
                    st.session_state.authenticated = False
                    st.session_state.current_user = None
                    st.session_state.user_id = None
                    st.session_state.selected_feature = None
                    st.rerun()

    st.markdown('<hr class="gradient" style="margin-top: 0; margin-bottom: 2rem; max-width: 100%;">', unsafe_allow_html=True)
    
    # Create Layout - use st.sidebar for proper sidebar integration
    # Features in Sidebar
    with st.sidebar:
        # st.markdown("## 🎓 Main Menu") removed in favor of expander title
        
        # Determine if expander should be open (open if no feature selected)
        is_menu_expanded = st.session_state.selected_feature is None
        
        with st.expander("Menu", expanded=is_menu_expanded):
            # Navigation menu
            if st.button("Dashboard Home", key="nav_dashboard", use_container_width=True):
                st.session_state.selected_feature = None
                st.rerun()
            
            if st.button("Chatbot & Summarization", key="nav_chatbot", use_container_width=True):
                st.session_state.selected_feature = "chatbot"
                st.rerun()
            
            if st.button("Quiz Generator", key="nav_quiz", use_container_width=True):
                st.session_state.selected_feature = "quiz"
                st.rerun()
            
            if st.button("Live Lecture Recording", key="nav_recording", use_container_width=True):
                st.session_state.selected_feature = "recording"
                st.rerun()
            
            if st.button("Flash Cards", key="nav_flashcards", use_container_width=True):
                st.session_state.selected_feature = "flashcards"
                st.rerun()
            
            if st.button("Translation", key="nav_translation", use_container_width=True):
                st.session_state.selected_feature = "translation"
                st.rerun()
            
            if st.button("Search", key="nav_search", use_container_width=True):
                st.session_state.selected_feature = "search"
                st.rerun()
            
            if st.button("Offline Mode", key="nav_offline", use_container_width=True):
                st.session_state.selected_feature = "offline"
                st.rerun()
            
            # OTHER Section
            st.markdown('<hr style="margin: 15px 0 10px 0; border: none; height: 1px; background: #f0f4ff;">', unsafe_allow_html=True)
            st.markdown('<p class="sidebar-title" style="margin-left: 10px;">OTHER</p>', unsafe_allow_html=True)
            
            if st.button("Profile", key="nav_profile", use_container_width=True):
                st.session_state.selected_feature = "profile"
                st.rerun()

            # Custom styling for logout button
            st.markdown("""
                <style>
                div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-last-child(1) button {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                    color: white !important;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
                }
                div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:nth-last-child(1) button:hover {
                    background: linear-gradient(90deg, #8f94fb, #764ba2) !important;
                    transform: translateX(5px) translateY(-2px) !important;
                    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            if st.button("Logout", key="logout_btn", help="Logout from your account", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.selected_feature = None
                st.rerun()

    # Main Content Area
    if st.session_state.selected_feature is None:
        show_welcome_screen()
    elif st.session_state.selected_feature == "chatbot":
        show_chatbot_feature()
    elif st.session_state.selected_feature == "quiz":
        show_quiz_feature()
    elif st.session_state.selected_feature == "recording":
        show_recording_feature()
    elif st.session_state.selected_feature == "flashcards":
        show_flashcards_feature()
    elif st.session_state.selected_feature == "translation":
        show_translation_feature()
    elif st.session_state.selected_feature == "notes":
        show_notes_feature()
    elif st.session_state.selected_feature == "admin":
        show_admin_feature()
    elif st.session_state.selected_feature == "search":
        show_search_feature()
    elif st.session_state.selected_feature == "offline":
        show_offline_feature()
    elif st.session_state.selected_feature == "profile":
        show_profile_feature()
    else:
        show_coming_soon_feature(st.session_state.selected_feature)

def show_coming_soon_feature(feature_name):
    """Placeholder for features not yet fully implemented"""
    st.markdown(
        f"""
        <div class="coming-soon">
            <div class="coming-soon-icon">🚀</div>
            <h2 class="coming-soon-title">{feature_name.replace('_', ' ').title()} Feature</h2>
            <p class="coming-soon-text">
                We're working hard to bring you the best {feature_name.replace('_', ' ')} experience. 
                This feature will be available in the next update!
            </p>
            <div style="text-align: center; margin-top: 30px;">
                <p style="color: #667eea; font-weight: 600;">Stay tuned for educational excellence!</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================
# WELCOME SCREEN SECTION
# ==========================
def show_welcome_screen():
    """Display welcome screen with learning visuals"""
    # WELCOME MESSAGE CARD (THEMED BG)
    st.markdown(
        """
        <div class="welcome-container">
            <h1 class="welcome-title">Welcome to your Dashboard!</h1>
            <p class="welcome-text">
                Your comprehensive educational platform powered by AI. Choose a feature from the sidebar to get started.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Learning Statistics Cards
    # Get user stats from session state (loaded during login)
    user_stats = st.session_state.get("user_stats", {})
    study_sessions = user_stats.get("study_sessions", 0)
    quizzes_created = user_stats.get("quizzes_created", 0)
    recordings_count = user_stats.get("recordings_count", 0)
    
    # Calculate progress percentage (based on activity)
    total_activities = study_sessions + quizzes_created + recordings_count
    progress_percentage = min(100, total_activities * 5) if total_activities > 0 else 0

    # CSS for responsive grid of stats cards
    st.markdown("""
        <style>
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #f8f9ff 0%, #e8ecff 100%);
            padding: 24px;
            border-radius: 16px;
            border: 1px solid #d1d9ff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: translateY(-3px); }
        .stat-value { color: #4e54c8; font-size: 32px; margin: 10px 0; font-weight: 700; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="stats-grid">
            <div class="stat-card">
                <h3 class="feature-title">Study Sessions</h3>
                <p class="feature-description">Track your learning progress</p>
                <div class="stat-value">{study_sessions}</div>
            </div>
            <div class="stat-card">
                <h3 class="feature-title">Quizzes Created</h3>
                <p class="feature-description">Interactive learning materials</p>
                <div class="stat-value">{quizzes_created}</div>
            </div>
            <div class="stat-card">
                <h3 class="feature-title">Recordings</h3>
                <p class="feature-description">Audio content processed</p>
                <div class="stat-value">{recordings_count}</div>
            </div>
            <div class="stat-card">
                <h3 class="feature-title">Progress</h3>
                <p class="feature-description">Learning efficiency</p>
                <div class="stat-value">{progress_percentage}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Inspirational Quote (Themed BG)
    quote_data = get_random_quote()
    st.markdown(
        f"""
        <div class="feature-card" style="
            text-align: center; 
            margin-top: 30px;
            background: linear-gradient(135deg, #f8f9ff 0%, #e8ecff 100%); /* Light Theme Gradient BG */
            padding: 30px;
            border-radius: 16px;
            border: 1px solid #d1d9ff;
            box-shadow: 0 4px 15px rgba(78, 84, 200, 0.08);
        ">
            <h3 style="
                color: #4e54c8; 
                font-size: 20px; 
                font-weight: 700; 
                margin-bottom: 15px; 
                font-family: 'Georgia', serif;
            ">
                Today's Learning Quote
            </h3>
            <p style="
                color: #374151; 
                font-size: 18px; 
                font-style: italic; 
                font-family: 'Georgia', serif; 
                margin: 0 0 10px 0;
            ">
                "{quote_data['text']}"
            </p>
            <p style="
                color: #6b7280; 
                font-size: 14px; 
                margin-top: 10px; 
                font-family: 'Georgia', serif;
            ">
                — {quote_data['author']}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================
# CHATBOT AND SUMMARIZATION SECTION
# ==========================
def show_chatbot_feature():

    
    
    # ✅ Configurable Tesseract OCR path with fallbacks
    # Priority: ENV var TESSERACT_CMD -> Windows default path -> system PATH
    _tesseract_env = os.getenv("TESSERACT_CMD")
    _windows_default = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    try:
        if _tesseract_env and os.path.exists(_tesseract_env):
            pytesseract.pytesseract.tesseract_cmd = _tesseract_env
        elif os.name == "nt" and os.path.exists(_windows_default):
            pytesseract.pytesseract.tesseract_cmd = _windows_default
        # else: rely on PATH; if not present, OCR calls will raise which we handle
    except Exception:
        # If configuration fails, we let _process_image handle exceptions gracefully
        pass
    
    
    class DocumentProcessor:
        def __init__(self):
            self.supported_formats = {
                ".txt", ".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"
            }
    
        def process_document(self, filepath):
            """
            Detect file type and extract text safely.
            Always returns a string (even if it's an error).
            """
            try:
                file_extension = os.path.splitext(filepath)[1].lower()
    
                if file_extension == ".txt":
                    return self._process_txt(filepath)
                elif file_extension == ".pdf":
                    return self._process_pdf(filepath)
                elif file_extension in [".docx", ".doc"]:
                    return self._process_word(filepath)
                elif file_extension in [".png", ".jpg", ".jpeg"]:
                    return self._process_image(filepath)
                else:
                    return f"[Unsupported file format: {file_extension}]"
    
            except Exception as e:
                return f"[File processing error: {str(e)}]"
    
        # ------------------------
        # File Type Processors
        # ------------------------
    
        def _process_txt(self, filepath):
            """Extract text from .txt files."""
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()
                return self._clean_text(content)
            except UnicodeDecodeError:
                try:
                    with open(filepath, "r", encoding="latin-1") as file:
                        content = file.read()
                    return self._clean_text(content)
                except Exception as e:
                    return f"[Error reading TXT file: {str(e)}]"
    
        def _process_pdf(self, filepath):
            """Extract text from PDF files."""
            try:
                with open(filepath, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    content = ""
                    for page in pdf_reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            content += extracted + "\n"
                return self._clean_text(content) if content else "[No text extracted from PDF]"
            except Exception as e:
                return f"[Error reading PDF: {str(e)}]"
    
        def _process_word(self, filepath):
            """Extract text from Word documents (.docx and .doc)."""
            try:
                doc = Document(filepath)
                content = ""
    
                # Extract paragraphs
                for paragraph in doc.paragraphs:
                    content += paragraph.text + "\n"
    
                # Extract tables
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            content += cell.text + " "
                    content += "\n"
    
                return self._clean_text(content) if content else "[No text extracted from Word file]"
            except Exception as e:
                return f"[Error reading Word document: {str(e)}]"
    
        def _process_image(self, filepath):
            """Extract text from image files using OCR (safe with timeout)."""
            try:
                with Image.open(filepath) as img:
                    img = img.convert("RGB")  # ensure format is consistent
                    # Add timeout to prevent hanging on large images
                    content = pytesseract.image_to_string(img, timeout=30)
                    cleaned = self._clean_text(content)
                    return cleaned if cleaned else "[No text detected in image]"
            except Exception as e:
                # Be explicit when Tesseract is missing to help users
                if "tesseract is not installed" in str(e).lower() or "not found" in str(e).lower():
                    return "[OCR unavailable: Tesseract not found. Install Tesseract or set TESSERACT_CMD]"
                return f"[Error reading image: {str(e)}]"
    
        # ------------------------
        # Helpers
        # ------------------------
    
        def _clean_text(self, text):
            """Clean and normalize extracted text."""
            if not text:
                return ""
    
            # Remove extra whitespace
            text = re.sub(r"\s+", " ", text)
    
            # Remove unwanted characters but keep punctuation
            text = re.sub(r"[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]", "", text)
    
            # Normalize spaces
            text = re.sub(r"\s+", " ", text)
    
            return text.strip()
    
        def get_document_summary(self, content, max_length=500):
            """Generate a brief summary of the document content."""
            if not content:
                return "[No content available to summarize]"
    
            if len(content) <= max_length:
                return content
    
            # Take first few sentences
            sentences = content.split(".")
            summary = ""
            for sentence in sentences:
                if len(summary + sentence) < max_length:
                    summary += sentence.strip() + ". "
                else:
                    break
    
            return summary.strip()
    
    
    
    
    
    
    doc_processor = DocumentProcessor()
    
    
    
    # ---------------------------
    # Page Config
    # ---------------------------
    # st.set_page_config(page_title="LectureBuddies - AI Chatbot", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
    
    # ---------------------------
    # Load API Key from .env
    # ---------------------------
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")  # make sure your .env has GROQ_API_KEY=your_api_key_here
    
    if not api_key:
        st.error("⚠️ API key missing! Please check your .env file.")
        st.stop()
    
    # ---------------------------
    # Session Initialization
    # ---------------------------
    def init_session_state():
        defaults = {
            "messages": [],
            "uploaded_files": [],
            "document_contents": {}
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
    
    init_session_state()
    
    # ---------------------------
    # Inject File Content Helper
    # ---------------------------
    def inject_file_content(user_message: str) -> str:
        """
        Replace file references in user message with extracted text,
        so model never says 'I can't see images'.
        """
        for fname, content in st.session_state.document_contents.items():
            if fname.lower() in user_message.lower():
                extracted = content if content.strip() else "[No text extracted from this file]"
                user_message = user_message.replace(
                    fname,
                    f"(Extracted content: {extracted[:1000]}...)"
                )
        return user_message
    
    # ---------------------------
    # API Interaction
    # ---------------------------
    def get_groq_response(user_input, model="llama-3.1-8b-instant"):
    
        """Send query + context to Groq API and return assistant response."""
        if not api_key or api_key.strip() == "":
            return "⚠️ Missing API key. Please set GROQ_API_KEY in your .env file."
    
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
        # Build document context
        doc_context = ""
        if st.session_state.document_contents:
            doc_context = "\n\n**Available Documents:**\n"
            for fname, content in st.session_state.document_contents.items():
                snippet = content[:1000] if content else "[No extractable text]"
                doc_context += f"\n--- {fname} ---\n{snippet}...\n"
    
        # Build conversation
        messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        system_msg = (
            f"You are Lecturebuddies, an AI chatbot designed for education. "
            f"Answer clearly, summarize effectively, and explain concepts step by step."
            f"{' Available Documents: ' + doc_context if doc_context else ''}\n\n"
            "Guidelines:\n"
            "📚 Education-focused\n"
            "📝 Summarization expert\n"
            "🎯 Clarity first (simple language, then details)\n"
            "✅ Confidence + accuracy\n"
            "Break down topics step-by-step, use examples, and stay professional yet supportive."
        )
        messages.insert(0, {"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": user_input})
    
        payload = {"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1000}
    
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "⚠️ No response received.")
            elif resp.status_code == 401:
                return "❌ Invalid API key. Please check GROQ_API_KEY in your .env file."
            elif resp.status_code == 429:
                return "⏳ Too many requests. Please slow down and retry shortly."
            else:
                return f"⚠️ API Error {resp.status_code}: {resp.text}"
        except requests.exceptions.Timeout:
            return "⏳ Request timed out. Please retry."
        except requests.exceptions.RequestException as e:
            return f"🌐 Network error: {e}"
        except Exception as e:
            return f"⚠️ Unexpected error: {e}"
    
    # ---------------------------
    # Document Processing
    # ---------------------------
    def process_document(uploaded_file):
        """Extract text from uploaded documents (txt, pdf, docx, images with OCR)."""
        try:
            # Save the uploaded file temporarily
            temp_path = os.path.join("temp", uploaded_file.name)
            os.makedirs("temp", exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
    
            # Use your DocumentProcessor
            content = doc_processor.process_document(temp_path)
    
            return content if content.strip() else "[No text extracted]"
        except Exception as e:
            return f"[File processing error: {e}]"
    
    # ---------------------------
    # Enhanced Styling (Matching Quiz Generator Theme)
    # ---------------------------
    st.markdown(
        """
        <style>
        .main-title {
            text-align: center;
            font-size: 40px;
            font-weight: 800;
            background: linear-gradient(90deg, #4e54c8, #8f94fb, #4e54c8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: -5px;
            font-family: 'Georgia', serif;
        }
        .tagline {
            text-align: center;
            font-size: 16px;
            color: #666;
            margin-bottom: 15px;
            font-family: 'Georgia', serif;
        }
        hr.gradient {
            border: none;
            height: 3px;
            background: linear-gradient(90deg, #4e54c8, #8f94fb, #4e54c8);
            border-radius: 50px;
            margin: 15px 0;
        }
        .custom-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 24px;
            font-size: 14px;
            font-weight: 700;
            color: white;
            background: linear-gradient(90deg, #4e54c8, #8f94fb);
            border: none;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            font-family: 'Georgia', serif;
            box-shadow: 0 3px 10px rgba(78, 84, 200, 0.3);
            margin: 5px 0;
        }
        .custom-btn:hover {
            background: linear-gradient(90deg, #8f94fb, #4e54c8);
            transform: scale(1.03) translateY(-1px);
            box-shadow: 0 5px 15px rgba(78, 84, 200, 0.4);
        }
        .clear-btn {
            background: linear-gradient(90deg, #ff6b6b, #ee5a52);
            color: white;
            border: none;
            border-radius: 15px;
            padding: 8px 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
            margin: 5px 0;
        }
        .clear-btn:hover {
            background: linear-gradient(90deg, #ee5a52, #ff6b6b);
            transform: scale(1.03);
        }
        .chat-header {
            color: #4e54c8;
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 10px;
            text-align: center;
            font-family: 'Georgia', serif;
        }
        .user-message {
            text-align: right;
            margin: 6px 0;
        }
        .user-bubble {
            display: inline-block;
            background: linear-gradient(90deg, #4e54c8, #8f94fb);
            color: white;
            padding: 10px 14px;
            border-radius: 18px 18px 4px 18px;
            max-width: 70%;
            font-family: 'Georgia', serif;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(78, 84, 200, 0.3);
        }
        .assistant-message {
            margin: 6px 0;
            color: #202123;
        }
        .assistant-bubble {
            background: white;
            padding: 10px 14px;
            border-radius: 18px 18px 18px 4px;
            max-width: 70%;
            border: 1px solid #e0e0e0;
            font-family: 'Georgia', serif;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .welcome-container {
            text-align: center;
            padding: 20px;
            background: linear-gradient(90deg, #8f94fb, #764ba2 );
            border-radius: 15px;
            border: 1px solid #d1d9ff;
            margin: 10px 0;
        }
        .welcome-title {
            color: #ffffff !important;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 10px;
            font-family: 'Georgia', serif;
        }
        .welcome-text {
            color: #ffffff !important;
            font-size: 16px;
            font-family: 'Georgia', serif;
        }
        /* Professional chat input styling */
        .stChatInput > div > div > input {
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            padding: 12px 16px;
            font-family: 'Georgia', serif;
            font-size: 14px;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        .stChatInput > div > div > input:focus {
            border-color: #4e54c8;
            box-shadow: 0 4px 12px rgba(78, 84, 200, 0.2);
            outline: none;
        }
        /* Fixed page height - prevent scrolling */
        .stApp {
            max-height: 100vh;
            overflow: hidden;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-height: 90vh;
            overflow-y: auto;
        }
        /* Reduce sidebar padding */
        .css-1d391kg {
            padding: 0.5rem;
        }
        /* Style sidebar elements */
        .stSidebar > div > div {
            font-family: 'Georgia', serif;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # ---------------------------
    # Sidebar (Enhanced to Match Theme)
    # ---------------------------
    with st.sidebar:
        st.markdown("## ⚙️ Chat Settings")
        st.markdown("### Customize your experience")
        
        if st.button("🗑️ Clear Chat", key="clear_chat", help="Start a new conversation"):
            st.session_state.messages.clear()
            st.rerun()
    
        st.markdown("---")
        st.markdown("**📎 Upload Files**")
        sidebar_upload = st.file_uploader(
            "Choose files",
            type=['txt', 'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'gif', 'bmp'],
            key="sidebar_uploader",
            label_visibility="collapsed",
            help="Upload documents or images for context (PDF, DOCX, TXT, Images with OCR)"
        )
        if sidebar_upload and sidebar_upload.name not in st.session_state.document_contents:
            file_details = {
                "filename": sidebar_upload.name,
                "filetype": sidebar_upload.type,
                "filesize": sidebar_upload.size
            }
            with st.spinner(f"Processing {sidebar_upload.name}..."):
                st.session_state.document_contents[sidebar_upload.name] = process_document(sidebar_upload)
            st.session_state.uploaded_files.append(file_details)
            st.sidebar.success(f"✅ {sidebar_upload.name} uploaded!")
            st.rerun()
    
        # Sidebar tips (Compact)
        st.markdown("---")
        st.markdown("**💡 Quick Tips:**")
        st.markdown("- Ask about studies or homework")
        st.markdown("- Upload files for context")
        st.markdown("- Be specific for better responses")
    
        # Show uploaded files (Styled)
        if st.session_state.uploaded_files:
            st.markdown("---")
            st.markdown("**📁 Your Files:**")
            for i, f in enumerate(st.session_state.uploaded_files):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"📄 {f['filename']}")
                with col2:
                    if st.button("🗑️", key=f"del_file_{i}", help="Remove file"):
                        fname = f['filename']
                        st.session_state.uploaded_files.pop(i)
                        st.session_state.document_contents.pop(fname, None)
                        st.rerun()
    

    
   
    
    # ---------------------------
    # Quick Actions (Styled to Match)
    # ---------------------------
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="welcome-container">
                <h1 class="welcome-title">Lecturebuddies Chatbot</h1>
                <p class="welcome-text">Start chatting or try a quick action below to dive into your studies.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2, col3 = st.columns(3)
        presets = {
            "📚 Help with Homework": "I need help understanding this homework assignment. Can you explain step-by-step?",
            "🔬 Explain a Concept": "I'm studying this concept but finding it difficult. Can you explain clearly with examples?",
            "💡 Study Tips": "I want to improve my study efficiency. What study strategies should I use?"
        }
        for col, (label, prompt) in zip([col1, col2, col3], presets.items()):
            with col:
                if st.button(label, key=label.replace(" ", "_").lower(), help="Start with this prompt"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.spinner("🤔 Thinking..."):
                        reply = get_groq_response(prompt)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.rerun()
    
    # ---------------------------
    # Chat Display (Direct, No Container)
    # ---------------------------
    if st.session_state.messages:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <div class="user-bubble">
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                    <div class="assistant-bubble">
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # ---------------------------
    # Chat Input (Professional Styling, Shorter Placeholder)
    # ---------------------------
    user_input = st.chat_input(placeholder="💬 Ask about studies or uploaded files...")
    if user_input and user_input.strip():
        # 🔑 Inject file content here
        final_input = inject_file_content(user_input.strip())
    
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        with st.spinner("🤔 Thinking..."):
            reply = get_groq_response(final_input)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
    
    # ---------------------------
    # Footer (Compact)
    # ---------------------------
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888; font-size: 12px; font-family: Georgia, serif; margin-bottom: 0;'>"
        "© 2026 Lecturebuddies | Built with ❤️ for educational excellence | Powered by Groq AI</p>",
        unsafe_allow_html=True
    )

# ==========================
# QUIZ GENERATOR SECTION
# ==========================
def show_quiz_feature():
    """Display quiz generator feature with old design"""
    # Layout: Settings in Sidebar (like Chatbot), Main Content in Container
    # col_feature_sidebar, col_main_content = st.columns([1, 3]) # Removed to use genuine sidebar
    
    # Remove bottom spacing for this view
    st.markdown(
        """
        <style>
        .main .block-container { padding-bottom: 0 !important; margin-bottom: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # LEFT: Feature-specific sidebar (Quiz Settings)
    with st.sidebar:
        st.markdown("### ⚙️ Quiz Settings")
        st.markdown("Customize your quiz generation.")
        
        st.markdown("**📊 Number of Questions**")
        num_questions = st.slider("How many questions?", min_value=1, max_value=20, value=st.session_state.num_questions, key="num_slider", label_visibility="collapsed")
        st.session_state.num_questions = num_questions

        st.markdown("**🎯 Difficulty Level**")
        difficulty = st.selectbox("Select difficulty:", ["Easy", "Medium", "Hard"], index=["Easy", "Medium", "Hard"].index(st.session_state.difficulty), key="diff_select", label_visibility="collapsed")
        st.session_state.difficulty = difficulty

        # Model and temperature controls
        model_options = [
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "llama-3.2-11b-text-preview"
        ]
        st.session_state.quiz_model = st.selectbox("Model", model_options, index=model_options.index(st.session_state.quiz_model) if st.session_state.quiz_model in model_options else 0)
        st.session_state.quiz_temperature = st.slider("Creativity (temperature)", 0.0, 1.0, float(st.session_state.quiz_temperature), 0.1)
    
    # RIGHT: Main Quiz Interface
    with st.container():
        # Header
        st.markdown(
            """
            <div class="welcome-container">
                <h1 class="welcome-title">Quiz Generator</h1>
                <p class="welcome-text">
                    Transform your notes, lectures, or ideas into interactive quizzes with AI magic ✨
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        tab1, tab2, tab3 = st.tabs(["📁 Upload File", "💡 Enter Prompt", "📋 Paste Text"])

        # Tab 1 - File Upload
        with tab1:
            st.markdown("### Upload a document to generate a quiz from its content")
            uploaded_file = st.file_uploader(
                "Choose a file (PDF, DOCX, TXT)",
                type=["pdf", "docx", "txt"],
                help="Supported formats: PDF, Word documents, and plain text files."
            )

            if st.button("✨ Generate Quiz from File", key="file-btn", help=f"Create {num_questions} {difficulty} questions"):
                if uploaded_file:
                    content = extract_content_from_file(uploaded_file)
                    if content and "Error" not in content:
                        quiz_result = get_groq_quiz_response(content, num_questions, difficulty, model=st.session_state.quiz_model, temperature=st.session_state.quiz_temperature)
                        st.session_state.quiz_output = quiz_result
                        # Save quiz to database
                        if st.session_state.get("user_id") and "Error" not in quiz_result:
                            save_quiz(st.session_state.user_id, uploaded_file.name, num_questions, difficulty, quiz_result)
                            # Refresh user stats
                            st.session_state.user_stats = get_user_stats(st.session_state.user_id)
                    else:
                        st.error("Failed to extract content from file. Please try a different file or format.")
                else:
                    st.warning("Please upload a file first!")

        # Tab 2 - Prompt
        with tab2:
            st.markdown("### Describe a topic or provide content for the quiz")
            prompt_text = st.text_area(
                "Enter your topic, subject, or detailed content",
                placeholder="e.g., 'Explain photosynthesis and generate questions on it' or paste lecture notes...",
                height=100,
                help="Be as detailed as possible for better quizzes!"
            )

            if st.button("✨ Generate Quiz from Prompt", key="prompt-btn", help=f"Create {num_questions} {difficulty} questions"):
                if prompt_text.strip():
                    quiz_result = get_groq_quiz_response(prompt_text, num_questions, difficulty, model=st.session_state.quiz_model, temperature=st.session_state.quiz_temperature)
                    st.session_state.quiz_output = quiz_result
                    # Save quiz to database
                    if st.session_state.get("user_id") and not quiz_result.startswith("Error"):
                        save_quiz(st.session_state.user_id, f"Prompt: {prompt_text[:50]}...", num_questions, difficulty, quiz_result)
                        # Save to local for offline access
                        local_data = {
                            "subject": f"Prompt: {prompt_text[:20]}...",
                            "num_questions": num_questions,
                            "difficulty": difficulty,
                            "content": quiz_result
                        }
                        save_to_local(st.session_state.current_user, "quizzes", local_data)
                        
                        # Refresh user stats
                        st.session_state.user_stats = get_user_stats(st.session_state.user_id)
                else:
                    st.warning("Please enter some content or a topic!")

        # Tab 3 - Text Input
        with tab3:
            st.markdown("### Paste scanned or copied text directly")
            scanned_text = st.text_area(
                "Paste your text content here",
                placeholder="e.g., Copy-paste from a scanned PDF, image OCR, or notes...",
                height=100,
                help="Ideal for quick text from any source."
            )

            if st.button("✨ Generate Quiz from Text", key="scan-btn", help=f"Create {num_questions} {difficulty} questions"):
                if scanned_text.strip():
                    quiz_result = get_groq_quiz_response(scanned_text, num_questions, difficulty, model=st.session_state.quiz_model, temperature=st.session_state.quiz_temperature)
                    st.session_state.quiz_output = quiz_result
                    # Save quiz to database
                    if st.session_state.get("user_id") and not quiz_result.startswith("Error"):
                        save_quiz(st.session_state.user_id, "Text Input", num_questions, difficulty, quiz_result)
                        # Save to local for offline access
                        local_data = {
                            "subject": "Text Input Quiz",
                            "num_questions": num_questions,
                            "difficulty": difficulty,
                            "content": quiz_result
                        }
                        save_to_local(st.session_state.current_user, "quizzes", local_data)
                        
                        # Refresh user stats
                        st.session_state.user_stats = get_user_stats(st.session_state.user_id)
                else:
                    st.warning("Please paste some text!")

        # Display Quiz Results
        if st.session_state.quiz_output:
            if "Error" in st.session_state.quiz_output or "⚠️" in st.session_state.quiz_output or "❌" in st.session_state.quiz_output:
                st.error(st.session_state.quiz_output)
                if st.button("Clear", key="clear_error", help="Start over"):
                    st.session_state.quiz_output = None
                    st.rerun()
            else:
                st.markdown(
                    """
                    <div class="quiz-container">
                        <h3 style="color: #4e54c8; font-size: 22px; font-weight: 700; margin-bottom: 10px; text-align: center; font-family: 'Georgia', serif;">
                            Your Generated Quiz
                        </h3>
                        <p style="text-align: center; color: #666; font-style: italic; font-size: 14px;">
                            {num_questions} questions at {difficulty} difficulty level
                        </p>
                    </div>
                    """.format(num_questions=st.session_state.num_questions, difficulty=st.session_state.difficulty),
                    unsafe_allow_html=True
                )

                st.markdown("### " + st.session_state.quiz_output)

                st.download_button(
                    label="Download Quiz as TXT",
                    data=st.session_state.quiz_output,
                    file_name=f"lecturebuddies_quiz_{st.session_state.num_questions}q_{st.session_state.difficulty.lower()}.txt",
                    mime="text/plain",
                    help="Save your quiz for later use!"
                )

                if st.button("Generate New Quiz", key="clear", help="Clear and start over"):
                    st.session_state.quiz_output = None
                    st.rerun()

# ==========================
# LIVE LECTURE RECORDING SECTION
# ==========================
def show_recording_feature():
    """Display simplified speech-to-text transcription via file upload or Real-Time"""
    
    # 1. Main heading
    st.markdown(
        """
        <div class="welcome-container">
            <h1 class="welcome-title">Speech to Text</h1>
            <p class="welcome-text">
                Upload voice recordings or record live audio for real-time transcription
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    SAVE_DIR = "temp_recordings"
    os.makedirs(SAVE_DIR, exist_ok=True)

    # 2. Load Whisper Model (Updated to 'tiny.en' for speed as requested)
    @st.cache_resource
    def load_whisper_model_simple(model_size="tiny.en", device="cpu", compute_type="int8"):
        # Try to use GPU if available, else CPU
        try:
            return WhisperModel(model_size, device="cuda", compute_type="int8_float16")
        except:
            return WhisperModel(model_size, device="cpu", compute_type="int8")

    with st.spinner(f"Loading High-Speed Model..."):
        model = load_whisper_model_simple()

    # 3. Tabs for different modes
    tab1, tab2 = st.tabs(["📁 Upload Audio Files", "🎤 Realtime Transcript"])

    # ==========================
    # TAB 1: Upload Audio Files (Existing Working Code)
    # ==========================
    with tab1:
        st.markdown("### Upload audio files for transcription")
        
        uploaded_files = st.file_uploader(
            "Upload audio file(s)",
            type=["wav", "mp3", "m4a", "flac", "ogg"],
            help="Supported formats: WAV, MP3, M4A, FLAC, OGG",
            accept_multiple_files=True,
            key="upload_files"
        )

        if uploaded_files:
            if st.button("🎯 Transcribe Files", key="transcribe_all"):
                for idx, uploaded_file in enumerate(uploaded_files, start=1):
                    with st.spinner(f"Transcribing {uploaded_file.name} ({idx}/{len(uploaded_files)})..."):
                        # Save to temp
                        temp_path = os.path.join(SAVE_DIR, f"uploaded_{int(time.time())}_{uploaded_file.name}")
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.read())

                        try:
                            segments, info = model.transcribe(temp_path, beam_size=5)
                            transcription_text = "".join([seg.text for seg in segments])

                            st.success(f"✅ Transcription completed: {uploaded_file.name}")

                            # Display and downloads
                            with st.expander(f"📝 {uploaded_file.name} — View Transcription", expanded=True):
                                st.text_area("Result", value=transcription_text, height=200, key=f"tx_{idx}")
                                st.download_button(
                                    "📥 Download Transcription",
                                    transcription_text,
                                    file_name=f"transcript_{uploaded_file.name}.txt"
                                )
                        except Exception as e:
                            st.error(f"❌ Error transcribing {uploaded_file.name}: {str(e)}")
                        finally:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)

    # ==========================
    # TAB 2: Realtime Transcript (UPDATED CODE)
    # ==========================
    with tab2:
        st.markdown("### ⚡ Fast Real-time Transcription")
        
        # Initialize session state for transcript storage
        if "live_transcript" not in st.session_state:
            st.session_state.live_transcript = ""
        if "is_recording" not in st.session_state:
            st.session_state.is_recording = False

        col1, col2 = st.columns([1, 2])

        with col1:
            st.info("💡 **Instructions:**\n1. Click 'Start Recording'.\n2. Speak into your mic.\n3. The text will appear instantly.\n4. Click 'Stop Recording' to end the session.")
            
            # Start/Stop Button
            if not st.session_state.is_recording:
                start_recording = st.button("🔴 Start Live Recording", use_container_width=True)
                if start_recording:
                    st.session_state.is_recording = True
                    st.rerun()
            else:
                stop_recording = st.button("⏹️ Stop Recording", use_container_width=True, type="primary")
                if stop_recording:
                    st.session_state.is_recording = False
                    st.rerun()
            
            start_recording = st.session_state.is_recording
            
            # Download Button (Visible if we have text)
            if st.session_state.live_transcript:
                st.download_button(
                    label="📥 Download Transcript",
                    data=st.session_state.live_transcript,
                    file_name="live_transcript.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
            if st.button("🗑️ Clear Transcript", use_container_width=True):
                st.session_state.live_transcript = ""
                st.rerun()

        with col2:
            st.markdown("#### 📝 Live Output")
            # Create a placeholder to update text in real-time
            transcript_placeholder = st.empty()
            
            # Show existing transcript if not recording
            if not start_recording:
                transcript_placeholder.text_area("Transcript", value=st.session_state.live_transcript, height=400, disabled=True)

            # ==========================
            # THE NEW LOGIC INTEGRATION
            # ==========================
            if start_recording:
                # 1. Setup Speech Recognition
                recognizer = sr.Recognizer()
                recognizer.energy_threshold = 1000  
                recognizer.dynamic_energy_threshold = False
                recognizer.pause_threshold = 0.3    
                recognizer.phrase_threshold = 0.3    
                recognizer.non_speaking_duration = 0.3
                
                mic = sr.Microphone(sample_rate=16000)
                
                # Visual Indicator
                st.toast("🎤 Listening... Speak now!", icon="👂")
                
                # Session ID for saving
                session_start_time = int(time.time())
                session_filename = f"recording_{session_start_time}_transcripts.json"
                
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # We use a loop here. In Streamlit, this runs until the user stops/refreshes.
                    try:
                        while st.session_state.is_recording:
                            # 2. Listen
                            # We use a placeholder info to show "Listening"
                            status_ph = st.empty()
                            status_ph.caption("👂 Listening...")
                            
                            audio_data = recognizer.listen(source, timeout=None, phrase_time_limit=5) # 5s chunks for fluidity
                            
                            status_ph.caption("⚡ Processing...")
                            
                            # 3. Process Audio for Whisper
                            raw_data = audio_data.get_raw_data()
                            audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

                            # 4. Transcribe (Fastest Settings)
                            segments, _ = model.transcribe(audio_np, beam_size=1, language="en", vad_filter=False)
                            new_text = "".join([s.text for s in segments]).strip()

                            if new_text:
                                # Append to session state
                                st.session_state.live_transcript += new_text + " "
                                
                                # Update the UI immediately
                                transcript_placeholder.text_area(
                                    "Transcript (Recording...)", 
                                    value=st.session_state.live_transcript, 
                                    height=400
                                )
                                
                                # Save incrementally to local (or save final on stop, but incremental ensures data safety)
                                # For strict "generated online" rule, we assume this is "generating" phase.
                                # To avoid too many writes, only save every 10th update or just keep in memory until stop?
                                # Better: Save here to ensure persistence if app crashes, but maybe overwrite same file.
                                # Actually, user mostly wants "final" transcript.
                                # Let's save the current full transcript.
                                local_data = {
                                    "title": f"Live Recording {time.strftime('%H:%M', time.localtime(session_start_time))}",
                                    "content": st.session_state.live_transcript,
                                    "saved_at": int(time.time())
                                }
                                save_to_local(st.session_state.current_user, "transcripts", local_data, custom_filename=session_filename)
                                
                            status_ph.empty()
                            
                    except Exception as e:
                        st.error(f"Recording stopped or error: {e}")





# ==========================
# FLASH CARDS FEATURE
# ==========================
def show_flashcards_feature():
    """Display flash cards generator feature"""
    st.markdown(
        """
        <div class="welcome-container">
            <h1 class="welcome-title">Flash Cards Generator</h1>
            <p class="welcome-text">
                Create interactive flash cards from your study materials
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚙️ Settings")
        st.markdown("---")
        
        # Flash card settings
        num_cards = st.slider("Number of Cards", 1, 50, 10)
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        subject = st.text_input("Subject/Topic", placeholder="e.g., Biology, History")
        
        st.markdown("---")
        st.markdown("**📄 Upload Content**")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['txt', 'pdf', 'docx'],
            help="Upload study material to generate flash cards"
        )
    
    with col2:
       
        
        if st.button("🎯 Generate Flash Cards", key="generate_cards", use_container_width=True):
            if content_input or uploaded_file:
                with st.spinner("Generating flash cards..."):
                    # Generate flash cards using AI
                    flashcards = generate_flashcards(content_input or "Sample content", num_cards, difficulty, subject)
                    st.session_state.flashcards = flashcards
                    
                    # Save to local for offline access
                    local_data = {
                        "subject": subject or "General Flashcards",
                        "difficulty": difficulty,
                        "cards": flashcards
                    }
                    save_to_local(st.session_state.current_user, "flashcards", local_data)
                    
                    st.success(f"✅ Generated {len(flashcards)} flash cards!")
            else:
                st.warning("Please provide content to generate flash cards")
        
        # Display generated flash cards
        if st.session_state.get('flashcards'):
            st.markdown("### 🃏 Your Flash Cards")
            display_flashcards(st.session_state.flashcards)

def generate_flashcards(content, num_cards, difficulty, subject):
    """Generate flash cards from content using AI"""
    if not api_key:
        return [{"front": "Error: No API key", "back": "Please set GROQ_API_KEY in your .env file"}]
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    prompt = f"""
    Create {num_cards} flash cards from this content for {subject or 'general study'}.
    Difficulty level: {difficulty}
    
    Content: {content[:2000]}
    
    Format each card as:
    Front: [Question or term]
    Back: [Answer or definition]
    
    Make them educational and useful for studying.
    """
    
    messages = [
        {"role": "system", "content": "You are a helpful study assistant that creates educational flash cards."},
        {"role": "user", "content": prompt}
    ]
    
    payload = {"model": "llama-3.1-8b-instant", "messages": messages, "temperature": 0.7, "max_tokens": 1000}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return parse_flashcards(content)
        else:
            return [{"front": "Error generating cards", "back": f"API Error: {response.status_code}"}]
    except Exception as e:
        return [{"front": "Error", "back": f"Failed to generate cards: {str(e)}"}]

def parse_flashcards(content):
    """Parse AI response into flash card format"""
    cards = []
    lines = content.split('\n')
    current_card = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('Front:'):
            if current_card:
                cards.append(current_card)
            current_card = {"front": line.replace('Front:', '').strip(), "back": ""}
        elif line.startswith('Back:'):
            current_card["back"] = line.replace('Back:', '').strip()
    
    if current_card:
        cards.append(current_card)
    
    return cards if cards else [{"front": "Sample Question", "back": "Sample Answer"}]

def display_flashcards(cards):
    """Display flash cards in an interactive format"""
    if not cards:
        return
    
    # Initialize session state for current card
    if 'current_card_index' not in st.session_state:
        st.session_state.current_card_index = 0
    
    current_index = st.session_state.current_card_index
    current_card = cards[current_index]
    
    # Card display
    st.markdown(
        f"""
        <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin: 20px 0;">
            <h3 style="color: #4e54c8; margin-bottom: 20px;">Card {current_index + 1} of {len(cards)}</h3>
            <div style="background: #f8f9ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4 style="color: #2c3e50; margin-bottom: 15px;">Front:</h4>
                <p style="font-size: 18px; color: #333;">{current_card['front']}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Show answer button
    if st.button("👁️ Show Answer", key="show_answer"):
        st.markdown(
            f"""
            <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4 style="color: #2c3e50; margin-bottom: 15px;">Back:</h4>
                <p style="font-size: 18px; color: #333;">{current_card['back']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous", key="prev_card", disabled=current_index == 0):
            st.session_state.current_card_index = max(0, current_index - 1)
            st.rerun()
    
    with col2:
        st.markdown(f"<div style='text-align: center; color: #666;'>Card {current_index + 1} of {len(cards)}</div>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next ➡️", key="next_card", disabled=current_index == len(cards) - 1):
            st.session_state.current_card_index = min(len(cards) - 1, current_index + 1)
            st.rerun()

# ==========================
# MULTILINGUAL TRANSLATION FEATURE
# ==========================
def show_translation_feature():
    """Display multilingual translation feature"""
    st.markdown(
        """
        <div class="welcome-container">
            <h1 class="welcome-title"> Multilingual Translation</h1>
            <p class="welcome-text">
                Translate text to your selected language (source auto-detected)
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚙️ Translation Settings")
        st.markdown("---")
        
        # Language selection (target only)
        languages = {
            "English": "en",
            "Spanish": "es", 
            "French": "fr",
            "German": "de",
            "Italian": "it",
            "Portuguese": "pt",
            "Chinese": "zh",
            "Japanese": "ja",
            "Korean": "ko",
            "Arabic": "ar",
            "Hindi": "hi",
            "Russian": "ru",
            "Urdu": "ur",
            "Punjabi": "pa",
            "Sindhi": "sd"
        }
        target_lang_label = st.selectbox("To Language", list(languages.keys()))
        
        st.markdown("---")
        st.markdown("**📄 Upload Document**")
        uploaded_file = st.file_uploader(
            "Choose a text file",
            type=['txt', 'docx'],
            help="Upload a document to translate"
        )
    
    with col2:
        st.markdown("### 📝 Text Translation")
        
        # Text input
        text_input = st.text_area(
            "Enter text to translate",
            placeholder="Type or paste your text here...",
            height=200
        )
        
        if st.button("🔄 Translate", key="translate_text", use_container_width=True):
            if text_input or uploaded_file:
                with st.spinner("Translating..."):
                    if uploaded_file:
                        # Process uploaded file
                        content = extract_content_from_file(uploaded_file)
                        translated = translate_text(content, target_lang_label)
                    else:
                        translated = translate_text(text_input, target_lang_label)
                    
                    st.session_state.translation_result = translated
                    st.success("✅ Translation completed!")
            else:
                st.warning("Please provide text to translate")
        
        # Display translation result
        if st.session_state.get('translation_result'):
            st.markdown("### 🌐 Translation Result")
            st.text_area("Translated Text", value=st.session_state.translation_result, height=200, key="translation_display")
            
            # Download button
            st.download_button(
                "📥 Download Translation",
                st.session_state.translation_result,
                file_name=f"translation_to_{languages[target_lang_label]}.txt",
                mime="text/plain"
            )

def translate_text(text, target_language_label):
    """Translate text using AI; auto-detect source language"""
    if not api_key:
        return "Error: No API key available"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    prompt = (
        f"Detect the source language and translate the following text to {target_language_label}. "
        f"Only return the translated text, no explanations or prefixes.\n\n{text}"
    )
    
    messages = [
        {"role": "system", "content": "You are a professional translator. Translate accurately and naturally."},
        {"role": "user", "content": prompt}
    ]
    
    payload = {"model": "llama-3.1-8b-instant", "messages": messages, "temperature": 0.3, "max_tokens": 1000}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "Translation failed")
        else:
            return f"Translation error: {response.status_code}"
    except Exception as e:
        return f"Translation failed: {str(e)}"

# ==========================
# NOTES MANAGER FEATURE
# ==========================
def show_notes_feature():
    """Display notes manager with import/export and organization"""
    st.markdown(
        """
        <div class="welcome-container">
            <h1 class="welcome-title">📋 Notes Manager</h1>
            <p class="welcome-text">
                Organize, import, and export your study notes with rich text formatting
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Initialize notes in session state
    if 'notes' not in st.session_state:
        st.session_state.notes = []
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📁 Note Organization")
        st.markdown("---")
        
        # Categories
        categories = ["General", "Mathematics", "Science", "History", "Language", "Other"]
        selected_category = st.selectbox("Category", categories)
        
        # Tags
        tags_input = st.text_input("Tags (comma-separated)", placeholder="e.g., important, exam, review")
        
        st.markdown("---")
        st.markdown("**📤 Import/Export**")
        
        # Import notes
        uploaded_notes = st.file_uploader(
            "Import Notes",
            type=['txt', 'json'],
            help="Import notes from file"
        )
        
        if uploaded_notes:
            if st.button("📥 Import Notes", key="import_notes"):
                try:
                    if uploaded_notes.type == "application/json":
                        notes_data = json.loads(uploaded_notes.read())
                        st.session_state.notes.extend(notes_data)
                    else:
                        content = uploaded_notes.read().decode('utf-8')
                        new_note = {
                            "title": uploaded_notes.name,
                            "content": content,
                            "category": selected_category,
                            "tags": tags_input.split(',') if tags_input else [],
                            "created": time.time()
                        }
                        st.session_state.notes.append(new_note)
                    st.success("✅ Notes imported successfully!")
                except Exception as e:
                    st.error(f"❌ Import failed: {str(e)}")
        
        # Export notes
        if st.session_state.notes:
            if st.button("📤 Export All Notes", key="export_notes"):
                notes_json = json.dumps(st.session_state.notes, indent=2)
                st.download_button(
                    "💾 Download Notes (JSON)",
                    notes_json,
                    file_name=f"lecturebuddies_notes_{int(time.time())}.json",
                    mime="application/json"
                )
    
    with col2:
        st.markdown("### ✏️ Create New Note")
        
        # Note creation form
        note_title = st.text_input("Note Title", placeholder="Enter note title")
        
        # Rich text editor (simplified)
        note_content = st.text_area(
            "Note Content",
            placeholder="Write your note here...\n\nYou can use basic formatting:\n**Bold text**\n*Italic text*\n# Heading\n- Bullet point",
            height=300
        )
        
        if st.button("💾 Save Note", key="save_note", use_container_width=True):
            if note_title and note_content:
                new_note = {
                    "title": note_title,
                    "content": note_content,
                    "category": selected_category,
                    "tags": [tag.strip() for tag in tags_input.split(',')] if tags_input else [],
                    "created": time.time(),
                    "modified": time.time()
                }
                st.session_state.notes.append(new_note)
                
                # Save to local for offline access
                save_to_local(st.session_state.current_user, "notes", new_note)
                
                st.success("✅ Note saved successfully!")
                st.rerun()
            else:
                st.warning("Please enter both title and content")
        
        # Display existing notes
        if st.session_state.notes:
            st.markdown("### 📚 Your Notes")
            for i, note in enumerate(st.session_state.notes):
                with st.expander(f"📝 {note['title']} ({note['category']})"):
                    st.markdown(f"**Created:** {time.ctime(note['created'])}")
                    st.markdown(f"**Tags:** {', '.join(note['tags']) if note['tags'] else 'None'}")
                    st.markdown("**Content:**")
                    st.markdown(note['content'])
                    
                    col_del, col_edit = st.columns(2)
                    with col_del:
                        if st.button("🗑️ Delete", key=f"del_note_{i}"):
                            st.session_state.notes.pop(i)
                            st.rerun()
                    with col_edit:
                        if st.button("✏️ Edit", key=f"edit_note_{i}"):
                            st.session_state.editing_note = i
                            st.rerun()

# ==========================
# ADMIN DASHBOARD FEATURE
# ==========================
def show_admin_feature():
    """Display admin dashboard for system management"""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #4e54c8; font-size: 32px; font-weight: 700; margin-bottom: 10px; font-family: 'Georgia', serif;">
                👨‍💼 Admin Dashboard
            </h1>
            <p style="color: #666; font-size: 16px; font-family: 'Georgia', serif;">
                System management and analytics for administrators
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Check if user is admin
    if st.session_state.current_user != "admin":
        st.warning("🔒 Admin access required. Please login as admin.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 System Stats")
        st.metric("Total Users", "1,234")
        st.metric("Active Sessions", "45")
        st.metric("Storage Used", "2.3 GB")
    
    with col2:
        st.markdown("### 🎯 Feature Usage")
        st.metric("Chatbot Queries", "5,678")
        st.metric("Quiz Generated", "234")
        st.metric("Recordings Made", "89")
    
    with col3:
        st.markdown("### ⚙️ System Health")
        st.metric("API Status", "✅ Online")
        st.metric("Database", "✅ Connected")
        st.metric("Storage", "✅ Available")
    
    st.markdown("---")
    
    # System management
    st.markdown("### 🔧 System Management")
    
    tab1, tab2, tab3 = st.tabs(["Users", "Settings", "Logs"])
    
    with tab1:
        st.markdown("#### 👥 User Management")
        st.dataframe({
            "Username": ["admin", "student1", "student2"],
            "Role": ["Admin", "Student", "Student"],
            "Last Login": ["2024-01-15", "2024-01-14", "2024-01-13"],
            "Status": ["Active", "Active", "Inactive"]
        })
    
    with tab2:
        st.markdown("#### ⚙️ System Settings")
        st.checkbox("Enable Registration", value=True)
        st.checkbox("Maintenance Mode", value=False)
        st.slider("Max File Size (MB)", 1, 100, 10)
    
    with tab3:
        st.markdown("#### 📋 System Logs")
        st.text_area("Recent Logs", value="2024-01-15 10:30:15 - User login: admin\n2024-01-15 10:25:32 - Quiz generated: student1\n2024-01-15 10:20:45 - Recording started: student2", height=200)

# ==========================
# CATEGORIZED SEARCH FEATURE
# ==========================
def show_search_feature():
    """Display categorized search functionality"""
    st.markdown(
        """
        <div class="welcome-container">
            <h1 class="welcome-title">🔍 Categorized Search</h1>
            <p class="welcome-text">
                Search across all your content with advanced filtering and categorization
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🔍 Search Filters")
        st.markdown("---")
        
        # Search categories
        search_categories = st.multiselect(
            "Search in:",
            ["Chat History", "Notes", "Quizzes", "Recordings", "Flash Cards"],
            default=["Chat History", "Notes"]
        )
        
        # Date range
        date_range = st.date_input("Date Range", value=[])
        
        # Content type
        content_type = st.selectbox("Content Type", ["All", "Text", "Audio", "Images", "Documents"])
        
        # Tags filter
        tags_filter = st.text_input("Tags", placeholder="e.g., important, exam")
    
    with col2:
        st.markdown("### Search Query")
        
        search_query = st.text_input(
            "Enter your search query",
            placeholder="Search for specific topics, keywords, or phrases...",
            key="search_input"
        )
        
        if st.button(" Search", key="perform_search", use_container_width=True):
            if search_query:
                with st.spinner("Searching..."):
                    results = perform_search(search_query, search_categories, date_range, content_type, tags_filter)
                    st.session_state.search_results = results
                    st.success(f"✅ Found {len(results)} results!")
            else:
                st.warning("Please enter a search query")
        
        # Display search results
        if st.session_state.get('search_results'):
            st.markdown("###  Search Results")
            display_search_results(st.session_state.search_results)

def perform_search(query, categories, date_range, content_type, tags_filter):
    """Perform categorized search"""
    # This is a simplified search implementation
    # In a real application, you would search through actual data
    results = []
    
    # Simulate search results
    sample_results = [
        {
            "title": "Chemistry Notes - Organic Compounds",
            "content": "Organic compounds are carbon-based molecules...",
            "category": "Notes",
            "date": "2024-01-15",
            "tags": ["chemistry", "organic", "important"],
            "relevance": 0.95
        },
        {
            "title": "Math Quiz - Calculus",
            "content": "Quiz questions about derivatives and integrals...",
            "category": "Quizzes", 
            "date": "2024-01-14",
            "tags": ["math", "calculus", "quiz"],
            "relevance": 0.87
        },
        {
            "title": "Biology Lecture Recording",
            "content": "Transcription of biology lecture about cell division...",
            "category": "Recordings",
            "date": "2024-01-13",
            "tags": ["biology", "lecture", "cell"],
            "relevance": 0.82
        }
    ]
    
    # Filter results based on search criteria
    for result in sample_results:
        if result['category'] in categories:
            if query.lower() in result['title'].lower() or query.lower() in result['content'].lower():
                results.append(result)
    
    return sorted(results, key=lambda x: x['relevance'], reverse=True)

def display_search_results(results):
    """Display search results in a formatted way"""
    for i, result in enumerate(results):
        with st.expander(f"📄 {result['title']} (Relevance: {result['relevance']:.2f})"):
            st.markdown(f"**Category:** {result['category']}")
            st.markdown(f"**Date:** {result['date']}")
            st.markdown(f"**Tags:** {', '.join(result['tags'])}")
            st.markdown(f"**Content:** {result['content'][:200]}...")
            
            if st.button("📖 View Full", key=f"view_result_{i}"):
                st.markdown(f"**Full Content:**\n\n{result['content']}")

# ==========================
# OFFLINE MODE FEATURE
# ==========================
def show_offline_feature():
    """Display offline mode functionality with access to saved content"""
    # 1. Header & Status
    st.markdown(
        """
        <div class="welcome-container">
            <h1 class="welcome-title">Offline Mode</h1>
            <p class="welcome-text">
                Access your previously generated content without internet
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Check connection
    try:
        requests.get("https://www.google.com", timeout=2)
        is_online = True
        status_color = "#28a745"
        status_text = "Connected"
    except:
        is_online = False
        status_color = "#dc3545"
        status_text = "Disconnected"
        
    st.markdown(
        f"""
        <div style="background: white; padding: 15px; border-radius: 12px; border-left: 5px solid {status_color}; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <strong style="color: {status_color}; font-size: 18px;">● {status_text}</strong>
                <div style="color: #666; font-size: 14px; margin-top: 5px;">
                    {'You have full access to all features.' if is_online else 'Restricted to saved content only.'}
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: #f0f2f6; padding: 5px 10px; border-radius: 15px; font-size: 12px; color: #555;">
                    Data Source: Local Storage
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not is_online:
        st.info("⚠️ You are currently offline. AI features (Chat, Quiz Generation) are unavailable. displaying locally saved copies.")
        
    # 2. Offline Content Viewer
    if not st.session_state.current_user:
        st.warning("Please log in to view saved content.")
        return

    st.markdown("### 📂 Saved Library")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Saved Quizzes", "🎴 Flash Cards", "📔 Notes", "🎙️ Transcripts"])
    
    # --- Saved Quizzes ---
    with tab1:
        quizzes = load_from_local(st.session_state.current_user, "quizzes")
        if not quizzes:
            st.info("No saved quizzes found. Generate quizzes while online to see them here.")
        else:
            for q in quizzes:
                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(q.get('saved_at', 0)))
                with st.expander(f"📝 Quiz: {q.get('subject', 'General')} - {date_str}"):
                    st.markdown(f"**Difficulty:** {q.get('difficulty')} | **Questions:** {q.get('num_questions')}")
                    if st.button("👁️ View Quiz", key=f"view_quiz_{q.get('saved_at')}"):
                        st.markdown("---")
                        st.text(q.get('content', 'No content'))
    
    # --- Saved Flash Cards ---
    with tab2:
        flashcards_sets = load_from_local(st.session_state.current_user, "flashcards")
        if not flashcards_sets:
            st.info("No saved flash cards found.")
        else:
            for fc_set in flashcards_sets:
                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(fc_set.get('saved_at', 0)))
                with st.expander(f"🎴 Deck: {fc_set.get('subject', 'General')} - {date_str}"):
                    cards = fc_set.get('cards', [])
                    st.markdown(f"**{len(cards)} Cards**")
                    if st.button("👁️ View Deck", key=f"view_fc_{fc_set.get('saved_at')}"):
                        for card in cards:
                            st.markdown(f"**Q:** {card['front']}")
                            st.markdown(f"**A:** {card['back']}")
                            st.markdown("---")

    # --- Saved Notes ---
    with tab3:
        notes = load_from_local(st.session_state.current_user, "notes")
        if not notes:
            st.info("No saved notes found.")
        else:
            for note in notes:
                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(note.get('saved_at', 0)))
                with st.expander(f"📔 {note.get('title', 'Untitled')} - {date_str}"):
                    st.markdown(f"**Category:** {note.get('category')}")
                    st.markdown("---")
                    st.markdown(note.get('content', ''))

    # --- Saved Transcripts ---
    with tab4:
        transcripts = load_from_local(st.session_state.current_user, "transcripts")
        if not transcripts:
            st.info("No saved transcripts found.")
        else:
            for trans in transcripts:
                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(trans.get('saved_at', 0)))
                with st.expander(f"🎙️ Recording: {trans.get('title', 'Untitled')} - {date_str}"):
                    st.text_area("Transcript", trans.get('content', ''), height=300, key=f"read_trans_{trans.get('saved_at')}")

def show_profile_feature():
    """Display user profile feature with modern, minimal UI"""
    st.markdown(
        """
        <div class="welcome-container">
            <h1 class="welcome-title">👤 User Profile</h1>
            <p class="welcome-text">Manage your personal identity, view insights, and control your account.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.user_id:
        st.warning("Please log in to view your profile.")
        return

    # Fetch latest user data (for display name, etc.)
    user_data = get_full_user_data(st.session_state.user_id)
    profile = user_data.get("profile", {})
    stats = user_data.get("stats", {})
    
    # Sync display name to session state for navigation
    if profile.get("display_name"):
        st.session_state.user_display_name = profile["display_name"]
    
    # Custom CSS for Profile Cards
    st.markdown("""
        <style>
        
        .profile-label {
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 5px;
            font-weight: 600;
        }
        .profile-value {
            font-size: 16px;
            color: #111827;
            font-weight: 500;
            margin-bottom: 15px;
        }
        .insight-card {
            background: #f9fafb;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #f3f4f6;
            text-align: center;
        }
        .danger-zone {
            border: 1px solid #fee2e2;
            background: #fffafb;
            padding: 20px;
            border-radius: 12px;
        }
        </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👤 Identity", "📈 Insights", "🔐 Settings"])

    with tab1:
        st.markdown('<div class="profile-section">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Simple circular avatar placeholder
            initials = profile.get("username", "U")[:2].upper()
            st.markdown(f"""
                <div style="
                    width: 100px; height: 100px; 
                    background: linear-gradient(135deg, #4e54c8, #8f94fb); 
                    border-radius: 50%; 
                    display: flex; align-items: center; justify-content: center; 
                    color: white; font-size: 32px; font-weight: 700;
                    margin: 0 auto 20px auto;
                ">
                    {initials}
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            current_display_name = profile.get("display_name") or profile.get("username")
            st.markdown(f'<div class="profile-label">Username</div><div class="profile-value">{profile.get("username")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="profile-label">Email Address</div><div class="profile-value">{profile.get("email") or "Not provided"}</div>', unsafe_allow_html=True)
            
            new_display_name = st.text_input("Display Name", value=current_display_name, help="How you want to be called in the app")
            
            if st.button("Update Profile", type="primary"):
                success, msg = update_user_profile(st.session_state.user_id, display_name=new_display_name)
                if success:
                    st.success("Profile updated! Refreshing...")
                    st.session_state.user_display_name = new_display_name
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="profile-section">', unsafe_allow_html=True)
        st.subheader("Light Usage Insights")
        st.markdown("These insights reflect your journey with Lecturebuddies. Keep up the great work!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="insight-card">', unsafe_allow_html=True)
            st.metric("Study Sessions", stats.get("study_sessions", 0))
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="insight-card">', unsafe_allow_html=True)
            st.metric("Quizzes Created", stats.get("quizzes_created", 0))
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col3:
            st.markdown('<div class="insight-card">', unsafe_allow_html=True)
            st.metric("Recordings", stats.get("recordings_count", 0))
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Calculate most used feature
        feature_counts = {
            "Chatbot": stats.get("study_sessions", 0),
            "Quizzes": stats.get("quizzes_created", 0),
            "Recordings": stats.get("recordings_count", 0),
            "Flashcards": stats.get("flashcards_created", 0),
            "Notes": stats.get("notes_count", 0)
        }
        most_used = max(feature_counts, key=feature_counts.get)
        
        st.info(f"✨ **Motivational Tip:** You mostly use **{most_used}**. Try exploring other features to diversify your study routine!")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="profile-section">', unsafe_allow_html=True)
        st.subheader("Account Management")
        
        with st.expander("🔐 Change Password"):
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            if st.button("Change Password"):
                if new_pwd == confirm_pwd and len(new_pwd) >= 6:
                    success, msg = update_user_profile(st.session_state.user_id, new_password=new_pwd)
                    if success: st.success("Password changed successfully!")
                    else: st.error(msg)
                else:
                    st.error("Passwords must match and be at least 6 characters.")
        
        st.markdown("---")
        
        col_export, col_logout = st.columns(2)
        with col_export:
            st.markdown("**Data Portability**")
            st.markdown("Download a copy of all your data.")
            if st.button("Export Data (JSON)"):
                full_data = get_full_user_data(st.session_state.user_id)
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(full_data, indent=2),
                    file_name=f"lecturebuddies_data_{profile.get('username')}.json",
                    mime="application/json"
                )
                
        with col_logout:
            st.markdown("**Session Control**")
            st.markdown("Sign out of your account.")
            if st.button("🚪 Logout Now", key="profile_logout_btn"):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.user_id = None
                st.session_state.selected_feature = None
                st.rerun()

        st.markdown("---")
        st.markdown('<div class="danger-zone">', unsafe_allow_html=True)
        st.markdown('<h4 style="color: #c53030; margin-top: 0;">⚠️ Danger Zone</h4>', unsafe_allow_html=True)
        st.markdown("Deleting your account is permanent and cannot be undone.")
        
        if "confirm_delete" not in st.session_state:
            st.session_state.confirm_delete = False
            
        if not st.session_state.confirm_delete:
            if st.button("Delete My Account", type="secondary"):
                st.session_state.confirm_delete = True
                st.rerun()
        else:
            st.warning("Are you absolutely sure? This will delete all your quizzes, notes, and recordings.")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("🔥 Yes, Delete Permanently", type="primary"):
                    success, msg = delete_user_account(st.session_state.user_id)
                    if success:
                        st.session_state.authenticated = False
                        st.session_state.current_user = None
                        st.session_state.user_id = None
                        st.session_state.selected_feature = None
                        st.session_state.confirm_delete = False
                        st.success("Account deleted. Goodbye!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(msg)
            with col_d2:
                if st.button("Cancel"):
                    st.session_state.confirm_delete = False
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# HELPER FUNCTIONS
# ==========================
def inject_file_content(user_message: str) -> str:
    """Replace file references in user message with extracted text"""
    for fname, content in st.session_state.document_contents.items():
        if fname.lower() in user_message.lower():
            extracted = content if content.strip() else "[No text extracted from this file]"
            user_message = user_message.replace(
                fname,
                f"(Extracted content: {extracted[:1000]}...)"
            )
    return user_message

def get_groq_response(user_input, model="llama-3.1-8b-instant", temperature=0.7):
    """Send query + context to Groq API and return assistant response"""
    if not api_key or api_key.strip() == "":
        return "Missing API key. Please set GROQ_API_KEY in your .env file."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Build document context
    doc_context = ""
    if st.session_state.document_contents:
        doc_context = "\n\n**Available Documents:**\n"
        for fname, content in st.session_state.document_contents.items():
            snippet = content[:1000] if content else "[No extractable text]"
            doc_context += f"\n--- {fname} ---\n{snippet}...\n"

    # Build conversation
    messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    system_msg = (
        f"You are Lecturebuddies, an AI chatbot designed for education. "
        f"Answer clearly, summarize effectively, and explain concepts step by step."
        f"{' Available Documents: ' + doc_context if doc_context else ''}\n\n"
        "Guidelines:\n"
        "Education-focused\n"
        "Summarization expert\n"
        "Clarity first (simple language, then details)\n"
        "Confidence + accuracy\n"
        "Break down topics step-by-step, use examples, and stay professional yet supportive."
    )
    messages.insert(0, {"role": "system", "content": system_msg})
    messages.append({"role": "user", "content": user_input})

    payload = {"model": model, "messages": messages, "temperature": float(temperature), "max_tokens": 1000}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "No response received.")
        elif resp.status_code == 401:
            return "Invalid API key. Please check GROQ_API_KEY in your .env file."
        elif resp.status_code == 429:
            return "Too many requests. Please slow down and retry shortly."
        else:
            return f"API Error {resp.status_code}: {resp.text}"
    except requests.exceptions.Timeout:
        return "Request timed out. Please retry."
    except requests.exceptions.RequestException as e:
        return f"Network error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

def process_document(uploaded_file, doc_processor):
    """Extract text from uploaded documents"""
    try:
        temp_path = os.path.join("temp", uploaded_file.name)
        os.makedirs("temp", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())

        content = doc_processor.process_document(temp_path)
        return content if content.strip() else "[No text extracted]"
    except Exception as e:
        return f"[File processing error: {e}]"

def get_groq_quiz_response(content, num_questions=5, difficulty="Medium", model="llama-3.1-8b-instant", temperature=0.7):
    """Send content to Groq API and get quiz questions back"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    difficulty_map = {"Easy": "simple and straightforward", "Medium": "balanced and informative", "Hard": "challenging and detailed"}
    diff_desc = difficulty_map.get(difficulty, "balanced")

    system_msg = (
        "You are Lecturebuddies Quiz Generator. "
        "Your task is to generate high-quality multiple-choice quizzes (MCQs) from educational material. "
        f"Generate exactly {num_questions} MCQs. Each question should have 4 options (A, B, C, D), one correct answer, "
        "and clearly mark the correct answer (e.g., Correct: A). "
        f"Make questions {diff_desc} in difficulty. "
        "Format the output neatly with numbered questions, bold question text, and labeled options. "
        "End with a summary of correct answers."
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": f"Generate a quiz from this content:\n\n{content}"}
    ]

    payload = {"model": model, "messages": messages, "temperature": float(temperature), "max_tokens": 1200}

    try:
        with st.spinner(f"Generating {num_questions} {difficulty} quiz questions..."):
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "No response received.")
        elif resp.status_code == 401:
            return "Invalid API key. Please check GROQ_API_KEY in your .env file."
        elif resp.status_code == 429:
            return "Too many requests. Please retry shortly."
        else:
            return f"API Error {resp.status_code}: {resp.text}"
    except requests.exceptions.Timeout:
        return "Request timed out. Please retry."
    except Exception as e:
        return f"Error: {str(e)}"

def extract_content_from_file(uploaded_file):
    """Extract text content from uploaded file (PDF, DOCX, TXT)"""
    file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else uploaded_file.name.split('.')[-1].lower()

    try:
        if file_type == "application/pdf" or file_type.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            content = ""
            for page in pdf_reader.pages:
                text = page.extract_text() or ""
                content += text + "\n"
            return content.strip()
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_type.endswith('.docx'):
            doc = Document(io.BytesIO(uploaded_file.read()))
            content = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            return content.strip()
        else:  # TXT or other text-based
            return uploaded_file.read().decode("utf-8", errors="ignore").strip()
    except Exception as e:
        return f"Error extracting content: {str(e)}"

def save_to_local(username, category, data, custom_filename=None):
    """Save content to local JSON for offline access."""
    if not username:
        return
    
    base_dir = "user_data"
    user_dir = os.path.join(base_dir, username)
    category_dir = os.path.join(user_dir, category)
    os.makedirs(category_dir, exist_ok=True)
    
    if custom_filename:
        filename = custom_filename
        if not filename.endswith(".json"):
            filename += ".json"
    else:
        # Create a unique filename based on timestamp
        title_part = ""
        if isinstance(data, dict):
            if "title" in data:
                title_part = f"_{data['title'][:20].replace(' ', '_')}"
            elif "subject" in data:
                title_part = f"_{data['subject'][:20].replace(' ', '_')}"
        
        # Clean filename
        title_part = "".join([c for c in title_part if c.isalnum() or c in ('_', '-')])
        
        filename = f"{int(time.time())}{title_part}_{category}.json"
        
    file_path = os.path.join(category_dir, filename)
    
    # Add timestamp
    if isinstance(data, dict) and 'saved_at' not in data:
        data['saved_at'] = int(time.time())
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving to local: {e}")

def load_from_local(username, category):
    """Load all content from local JSON for a category."""
    if not username:
        return []
        
    base_dir = "user_data"
    category_dir = os.path.join(base_dir, username, category)
    
    if not os.path.exists(category_dir):
        return []
        
    items = []
    try:
        for filename in os.listdir(category_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(category_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        if isinstance(data, dict) and 'saved_at' not in data:
                            try:
                                ts = int(filename.split('_')[0])
                                data['saved_at'] = ts
                            except:
                                data['saved_at'] = 0
                        items.append(data)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Error loading from local: {e}")
        
    return sorted(items, key=lambda x: x.get('saved_at', 0), reverse=True)

# Recording helper functions
def record_worker(audio_q: queue.Queue, stop_event: threading.Event):
    """Recording thread worker"""
    while not stop_event.is_set():
        time.sleep(0.1)

def sd_callback(indata, frames, time_info, status):
    """Callback for sounddevice.InputStream"""
    if status:
        pass
    mono = np.mean(indata, axis=1).astype(np.float32)
    # guard: audio_queue may be None if recording not properly started
    if st.session_state.get("audio_queue") is not None:
        try:
            st.session_state.audio_queue.put(mono)
        except Exception:
            pass

def transcription_consumer(model: WhisperModel, chunk_seconds=5):
    """Transcription consumer thread"""
    sample_per_chunk = chunk_seconds * 16000
    buffer = np.zeros((0,), dtype=np.float32)
    chunk_index = 0

    while st.session_state.recording or (st.session_state.audio_queue is not None and not st.session_state.audio_queue.empty()):
        try:
            while st.session_state.audio_queue is not None and not st.session_state.audio_queue.empty():
                data = st.session_state.audio_queue.get_nowait()
                buffer = np.concatenate((buffer, data))

            if buffer.shape[0] >= sample_per_chunk:
                to_process = buffer[:sample_per_chunk]
                buffer = buffer[sample_per_chunk:]

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                    sf.write(tmp_path, to_process, 16000, subtype="PCM_16")

                segments, info = model.transcribe(tmp_path, beam_size=5)
                partial_text = ""
                for seg in segments:
                    partial_text += seg.text

                prev = st.session_state.transcript
                st.session_state.transcript = (prev + " " + partial_text).strip()
                st.session_state.partial_transcript = partial_text

                saved_chunk = os.path.join("temp_recordings", f"chunk_{int(time.time())}_{chunk_index}.wav")
                os.replace(tmp_path, saved_chunk)
                st.session_state.chunks_saved.append(saved_chunk)
                chunk_index += 1
            else:
                time.sleep(0.2)
        except Exception:
            time.sleep(0.1)
    return

# Realtime recording helper functions
def realtime_record_worker(audio_q: queue.Queue, stop_event: threading.Event):
    """Recording thread worker for realtime"""
    while not stop_event.is_set():
        time.sleep(0.1)

def realtime_sd_callback(indata, frames, time_info, status):
    """Callback for sounddevice.InputStream in realtime mode"""
    if status:
        pass
    mono = np.mean(indata, axis=1).astype(np.float32)
    if st.session_state.get("realtime_queue") is not None:
        try:
            st.session_state.realtime_queue.put(mono)
        except Exception:
            pass

def realtime_transcription_consumer(model: WhisperModel, chunk_seconds=5):
    """Transcription consumer thread for realtime"""
    sample_per_chunk = chunk_seconds * 16000
    buffer = np.zeros((0,), dtype=np.float32)
    chunk_index = 0

    while st.session_state.realtime_recording or (st.session_state.realtime_queue is not None and not st.session_state.realtime_queue.empty()):
        try:
            # Get audio data from queue
            while st.session_state.realtime_queue is not None and not st.session_state.realtime_queue.empty():
                data = st.session_state.realtime_queue.get_nowait()
                buffer = np.concatenate((buffer, data))

            # Process when we have enough data
            if buffer.shape[0] >= sample_per_chunk:
                to_process = buffer[:sample_per_chunk]
                buffer = buffer[sample_per_chunk:]

                # Save audio chunk to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                    sf.write(tmp_path, to_process, 16000, subtype="PCM_16")

                # Transcribe the chunk
                try:
                    segments, info = model.transcribe(tmp_path, beam_size=5)
                    partial_text = ""
                    for seg in segments:
                        partial_text += seg.text

                    # Update session state
                    if partial_text.strip():
                        prev = st.session_state.realtime_transcript
                        st.session_state.realtime_transcript = (prev + " " + partial_text).strip()
                        st.session_state.realtime_partial = partial_text
                        
                        # Save chunk for debugging
                        saved_chunk = os.path.join("temp_recordings", f"realtime_chunk_{int(time.time())}_{chunk_index}.wav")
                        os.replace(tmp_path, saved_chunk)
                        st.session_state.realtime_chunks.append(saved_chunk)
                        chunk_index += 1
                        
                        print(f"Transcribed chunk {chunk_index}: {partial_text}")  # Debug print
                    else:
                        print(f"No text in chunk {chunk_index}")  # Debug print
                        os.remove(tmp_path)
                        
                except Exception as e:
                    print(f"Transcription error: {e}")  # Debug print
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
            else:
                time.sleep(0.2)
        except Exception as e:
            print(f"Consumer error: {e}")  # Debug print
            time.sleep(0.1)
    return

# ==========================
# MAIN APPLICATION LOGIC
# ==========================
def main():
    """Main application entry point"""
    # Simple Forgot Password routing
    if st.session_state.get("show_simple_reset", False):
        show_simple_password_reset()
        return

    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
