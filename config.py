import os

DEFAULT_MAX_RESULTS = 50
USER_AGENT = "AcademicGapFinder/1.0 (mailto:student@example.com)"
DEFAULT_LLM_MODEL = "gemini-3.6-flash"

# Программа сначала ищет ключ в безопасных настройках сервера (Streamlit Secrets),
# а если запускается локально — берёт твой ключ ниже.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "AQ.Ab8RN6JmKBC9W-D5fuTH46EuIf8Pzzya-aCxcIsfi7EfavUHIw")  # <- вставь свой ключ AIzaSy сюда для локального запуска