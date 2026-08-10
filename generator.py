import os
import requests

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def get_gemini_keys() -> list[str]:
    keys = []
    env_names = [
        "OPENAI_API_KEY",
        "OPENAI_API_KEY_2",
        "OPENAI_API_KEY_3",
        "OPENAI_API_KEY_4",
        "OPENAI_API_KEY_5",
    ]

    # Чтение из переменных окружения (Render)
    for name in env_names:
        val = os.getenv(name)
        if val and val.strip() and val.strip() not in keys:
            keys.append(val.strip())

    # Безопасное чтение из streamlit secrets (если есть)
    try:
        import streamlit as st

        for name in env_names:
            if name in st.secrets and st.secrets[name]:
                val = str(st.secrets[name]).strip()
                if val and val not in keys:
                    keys.append(val)
    except Exception:
        pass

    return keys


def build_prompt(query: str, articles: list[dict]) -> str:
    context = ""
    for i, art in enumerate(articles, 1):
        context += f"\n--- Источник {i}: {art.get('title')} ({art.get('year')}) ---\n"
        context += f"Abstract: {art.get('abstract', 'N/A')[:350]}...\n"

    return f"""
Ты — ведущий академический консультант и эксперт по анализу научной литературы.
ЗАПРОС ИССЛЕДОВАТЕЛЯ: "{query}"

РЕПРЕЗЕНТАТИВНЫЕ ИСТОЧНИКИ ИЗ БАЗЫ:
{context}

Сформулируй 3 УНИКАЛЬНЫЕ темы для будущих статей:

📌 **Тема [номер]: [Академическое название]**
• **Научная новизна / Актуальность:** [2-3 предложения]
• **Расширенная академическая аннотация:** [4-5 предложений]
• **Ключевые слова:** [5-7 терминов через запятую]
• **Подробный исследовательский план:**
1. Введение и постановка проблемы
2. Теоретико-методологическая база
3. Эмпирический анализ
4. Выводы и научная ценность
"""


def generate_topics(query: str, articles: list[dict]) -> str:
    prompt = build_prompt(query, articles)
    keys = get_gemini_keys()

    for key in keys:
        for model in GEMINI_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                resp = requests.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": key,
                    },
                    json={
                        "contents": [
                            {"role": "user", "parts": [{"text": prompt}]}
                        ],
                        "generationConfig": {"temperature": 0.7},
                    },
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                continue

    # Резервный канал (Groq)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key.strip():
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key.strip()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass

    return "❌ Ошибка генерации: не удалось связаться с ИИ-сервисами."
    formatted_errors = "\n".join([f"• {err}" for err in errors_log])
    return (
        f"❌ **Не удалось получить ответ от сервисов генерации.**\n\n"
        f"**Детали:**\n{formatted_errors}"
    )
