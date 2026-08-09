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
    Отправляет промпт напрямую в Google Gemini API.
    """
    prompt = build_analysis_prompt(user_query, articles)

    if not OPENAI_API_KEY or OPENAI_API_KEY == "AIzaSy...":
        return (
            "⚠️ API-ключ Google не найден в config.py!\n\n"
            "Пожалуйста, вставьте ваш API-ключ от Google AI Studio в config.py.\n\n"
            "--- СФОРМИРОВАННЫЙ ПРОМПТ ---\n" + prompt[:500] + "..."
        )

    from openai import OpenAI

    # Официальный шлюз Google Gemini для совместимости с OpenAI библиотекой
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=OPENAI_API_KEY,
    )

    try:
        print(f"🤖 Запрашиваем генерацию у Google Gemini [{DEFAULT_LLM_MODEL}]...")
        response = client.chat.completions.create(
            model=DEFAULT_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Ты — ведущий академический эксперт и научный руководитель.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Ошибка при обращении к Gemini API: {e}"