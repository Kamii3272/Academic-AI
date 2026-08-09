import requests
import streamlit as st

# Модели Gemini для проверки
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def build_analysis_prompt(user_query: str, articles: list[dict]) -> str:
    """Формирует сжатый академический промпт."""
    context = ""
    for i, art in enumerate(articles, 1):
        abstract_text = (
            art.get("abstract") or art.get("text") or "Аннотация отсутствует."
        )
        title = art.get("title", "Без названия")
        year = art.get("year", "N/A")
        short_abstract = (
            abstract_text[:350] + "..."
            if len(abstract_text) > 350
            else abstract_text
        )
        context += f"\n--- Статья {i} ---\nНазвание: {title} ({year})\nАннотация: {short_abstract}\n"

    return f"""
Ты — ведущий академический консультант и эксперт по научной новизне.

ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС: "{user_query}"

СУЩЕСТВУЮЩИЕ ПУБЛИКАЦИИ И ИССЛЕДОВАНИЯ В ЭТОЙ ОБЛАСТИ:
{context}

ТВОЯ ЗАДАЧА:
1. Проанализируй представленные выше статьи.
2. Найди "исследовательские лакуны" (Research Gaps) — темы, ракурсы или междисциплинарные стыки, которые ещё НЕ раскрыты или слабо освещены в этих работах.
3. Сформулируй 3 УНИКАЛЬНЫЕ, узкосфокусированные и академически строгие темы для будущих статей.

ТРЕБОВАНИЯ К ВЫДАЧЕ:
Для каждой из 3 тем укажи:
- 📌 Название темы (четкое, академическое)
- 🎯 Актуальность и новизна (почему этого нет в текущих работах)
- 💡 Краткий план/гипотеза работы (3-4 ключевых тезиса)
"""


def get_gemini_keys() -> list[str]:
    """Считывает все доступные ключи Gemini из Secrets."""
    keys = []
    if "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
        keys.append(str(st.secrets["OPENAI_API_KEY"]).strip())

    for i in range(2, 6):
        key_name = f"OPENAI_API_KEY_{i}"
        if key_name in st.secrets and st.secrets[key_name]:
            keys.append(str(st.secrets[key_name]).strip())

    return keys


def generate_topics(user_query: str, articles: list[dict]) -> str:
    """Пайплайн генерации с логированием ошибок и поддержкой Groq."""
    prompt = build_analysis_prompt(user_query, articles)
    keys = get_gemini_keys()
    errors_log = []

    # 1. Пробуем все ключи и модели Google Gemini
    if keys:
        for idx, api_key in enumerate(keys, 1):
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            }
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "systemInstruction": {
                    "parts": [
                        {
                            "text": "Ты — ведущий академический эксперт и научный руководитель."
                        }
                    ]
                },
                "generationConfig": {"temperature": 0.7},
            }

            for model in GEMINI_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                try:
                    resp = requests.post(
                        url, headers=headers, json=payload, timeout=30
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["candidates"][0]["content"]["parts"][0][
                            "text"
                        ]
                    else:
                        err_text = resp.json().get("error", {}).get("message", resp.text)
                        errors_log.append(
                            f"Gemini (Ключ #{idx}, {model}) -> Код {resp.status_code}: {err_text}"
                        )
                except Exception as e:
                    errors_log.append(
                        f"Gemini (Ключ #{idx}, {model}) -> Исключение: {e}"
                    )
    else:
        errors_log.append("Ключи Gemini (OPENAI_API_KEY) не найдены в Secrets.")

    # 2. Резервный канал: Groq API (Llama 3.3 70B)
    if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
        groq_key = str(st.secrets["GROQ_API_KEY"]).strip()
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — ведущий академический эксперт и научный руководитель.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }
        try:
            resp = requests.post(
                url, headers=headers, json=payload, timeout=30
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                errors_log.append(
                    f"Groq API -> Код {resp.status_code}: {resp.text}"
                )
        except Exception as e:
            errors_log.append(f"Groq API -> Исключение: {e}")

    # Если абсолютно всё упало — выводим детализацию
    formatted_errors = "\n".join([f"• {err}" for err in errors_log])
    return (
        f"❌ **Не удалось получить ответ ни от одного из сервисов.**\n\n"
        f"**Детали ошибок по провайдерам:**\n{formatted_errors}\n\n"
        f"💡 **Решение проблемы раз и навсегда:**\n"
        f"Зарегистрируйте бесплатный ключ на **[groq.com](https://console.groq.com/)** и добавьте `GROQ_API_KEY` в Secrets Streamlit. Groq выдаёт 14 400 бесплатных запросов в день и не блокирует IP-адреса облачных серверов."
    )
