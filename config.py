import os
import streamlit as st

DEFAULT_MAX_RESULTS = 50
USER_AGENT = "AcademicGapFinder/1.0 (mailto:student@example.com)"

# Стабильная рабочая модель Google Gemini
DEFAULT_LLM_MODEL = "gemini-2.0-flash"

# Безопасное считывание ключа из Streamlit Secrets или переменных окружения
OPENAI_API_KEY = ""

try:
    if "OPENAI_API_KEY" in st.secrets:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    else:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
