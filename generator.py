import requests
import streamlit as st

# Список моделей для автоматического переключения при исчерпании лимитов
MODELS_TO_TRY = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]


def build_analysis_prompt(user_query: str, articles: list[dict]) -> str:
    """Формирует академический промпт для LLM."""
    context = ""
    for i, art in enumerate(articles, 1):
        abstract_text = (
            art.get("abstract") or art.get("text") or "Аннотация отсутствует."
        )
        title = art.get("title", "Без названия")
        year = art.get("year", "Год не указан")

        context += f"\n--- Статья {i} ---\nНазвание: {title}\nГод: {year}\nАннотация: {abstract_text}\n"

    prompt = f"""
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
    return prompt


def generate_topics(user_query: str, articles: list[dict]) -> str:
    """Отправляет запрос в Google Gemini API с авто-переключением моделей при 429."""
    prompt = build_analysis_prompt(user_query, articles)

    api_key = ""
    try:
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

    if not api_key:
        return "⚠️ API-ключ не найден в настройках Secrets Streamlit!"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key.strip(),
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

    last_error = ""

    # Автоматически пробуем модели по очереди, если одна превысила лимит (429)
    for model_name in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=60
            )
            data = response.json()

            if response.status_code == 200:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            elif response.status_code == 429:
                last_error = f"Лимит бесплатного тарифа для {model_name} временно исчерпан."
                continue
            else:
                error_msg = data.get("error", {}).get("message", response.text)
                return f"❌ Ошибка при обращении к Gemini API ({response.status_code}): {error_msg}"
        except Exception as e:
            last_error = str(e)
            continue

    return f"⏱️ Превышен бесплатный лимит запросов Google API. Подождите 1 минуту и нажмите кнопку снова.\n\nДетали: {last_error}"
