import requests
from config import DEFAULT_LLM_MODEL, OPENAI_API_KEY


def build_analysis_prompt(user_query: str, articles: list[dict]) -> str:
    """
    Формирует строгий академический промпт для LLM.
    """
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
    """
    Отправляет промпт напрямую в Google Gemini API через REST.
    """
    prompt = build_analysis_prompt(user_query, articles)

    if not OPENAI_API_KEY:
        return (
            "⚠️ API-ключ не найден в настройках!\n\n"
            "Пожалуйста, проверьте Secrets в Streamlit."
        )

    # Прямой адрес API Google с передачей ключа в URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_LLM_MODEL}:generateContent?key={OPENAI_API_KEY}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": "Ты — ведущий академический эксперт и научный руководитель."}]
        },
        "generationConfig": {
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        data = response.json()

        if response.status_code == 200:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            error_msg = data.get("error", {}).get("message", response.text)
            return f"❌ Ошибка при обращении к Gemini API: {error_msg}"

    except Exception as e:
        return f"❌ Ошибка сети при обращении к Gemini API: {e}"
