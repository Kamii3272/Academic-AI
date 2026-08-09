import time
import requests
import streamlit as st

# Основные модели Gemini
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
]

# Резервные БЕСПЛАТНЫЕ модели из OpenRouter
OPENROUTER_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "google/gemini-2.0-flash-lite-001:free",
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

        # Жесткая обрезка до 400 символов для минимального расхода токенов
        short_abstract = (
            abstract_text[:400] + "..."
            if len(abstract_text) > 400
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


def get_all_gemini_keys() -> list[str]:
    """Собирает все доступные ключи Gemini из Secrets."""
    keys = []
    # Основной ключ
    if "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
        keys.append(st.secrets["OPENAI_API_KEY"].strip())

    # Дополнительные ключи (если пользователь добавит их в Secrets)
    for i in range(2, 6):
        key_name = f"OPENAI_API_KEY_{i}"
        if key_name in st.secrets and st.secrets[key_name]:
            keys.append(st.secrets[key_name].strip())

    return keys


def try_gemini_api(prompt: str, keys: list[str]) -> str | None:
    """Пробует сгенерировать ответ через все ключи и модели Gemini."""
    for api_key in keys:
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
                    url, headers=headers, json=payload, timeout=45
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                elif resp.status_code == 429:
                    # Если лимит исчерпан — пробуем следующую модель/ключ
                    time.sleep(1)
                    continue
            except Exception:
                continue

    return None


def try_openrouter_api(prompt: str) -> str | None:
    """Резервный вызов через OpenRouter (бесплатные модели Llama/Qwen)."""
    if "OPENROUTER_API_KEY" not in st.secrets:
        return None

    openrouter_key = st.secrets["OPENROUTER_API_KEY"].strip()
    if not openrouter_key:
        return None

    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json",
    }

    for model in OPENROUTER_MODELS:
        payload = {
            "model": model,
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
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            continue

    return None


def generate_topics(user_query: str, articles: list[dict]) -> str:
    """Главный пайплайн генерации с каскадным переключением."""
    prompt = build_analysis_prompt(user_query, articles)
    gemini_keys = get_all_gemini_keys()

    if not gemini_keys:
        return "⚠️ API-ключ не найден в настройках Secrets Streamlit!"

    # 1. Первая линия обороны: Gemini (все ключи и модели)
    result = try_gemini_api(prompt, gemini_keys)
    if result:
        return result

    # 2. Вторая линия обороны: OpenRouter (если подключен)
    result_openrouter = try_openrouter_api(prompt)
    if result_openrouter:
        return result_openrouter

    # 3. Если вообще всё умерло
    return (
        "⏱️ Все бесплатные нейросети временно перегружены параллельными запросами.\n\n"
        "**Подождите 30 секунд и нажмите кнопку снова — лимиты сбросятся!**"
    )
