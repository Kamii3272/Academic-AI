import urllib.parse
import requests
from config import DEFAULT_MAX_RESULTS, USER_AGENT

# Словарь для точного авто-перевода частых русскоязычных IT/научных запросов
QUERY_TRANSLATIONS = {
    "сетевая инженерия": "network engineering computer networks",
    "компьютерные сети": "computer networks networking protocols",
    "кибербезопасность": "cybersecurity network security",
    "искусственный интеллект": "artificial intelligence machine learning",
    "машинное обучение": "machine learning deep learning",
}


def prepare_search_query(user_query: str) -> str:
    """Автоматически улучшает поисковый запрос для международной базы OpenAlex."""
    cleaned = user_query.strip().lower()

    # Проверяем точные совпадения в словаре
    if cleaned in QUERY_TRANSLATIONS:
        return QUERY_TRANSLATIONS[cleaned]

    # Если запрос на кириллице, добавляем к нему английский контекст
    has_cyrillic = any("\u0400" <= char <= "\u04ff" for char in user_query)
    if has_cyrillic:
        # Для поисковика трансформируем "сетевая инженерия" -> "сетевая инженерия network engineering"
        return f"{user_query} {cleaned}"

    return user_query


def fetch_articles(
    query: str, max_results: int = DEFAULT_MAX_RESULTS
) -> list[dict]:
    """Выгружает релевантные научные публикации из OpenAlex API."""
    optimized_query = prepare_search_query(query)
    encoded_query = urllib.parse.quote(optimized_query)

    # Ищем публикации с сортировкой по релевантности
    url = f"https://api.openalex.org/works?search={encoded_query}&per-page={max_results}&sort=relevance_score:desc"
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []

        data = response.json()
        results = data.get("results", [])
        articles = []

        for item in results:
            title = item.get("display_name") or "Без названия"
            year = item.get("publication_year") or "Год не указан"
            doi = item.get("doi") or ""

            # Восстанавливаем аннотацию из инвертированного индекса OpenAlex
            abstract_dict = item.get("abstract_inverted_index")
            abstract = ""
            if abstract_dict:
                word_positions = []
                for word, positions in abstract_dict.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join([word for _, word in word_positions])

            # Собираем только статьи с понятными названиями
            if title and len(title) > 5:
                articles.append(
                    {
                        "title": title,
                        "year": str(year),
                        "doi": doi,
                        "abstract": abstract,
                    }
                )

        return articles

    except Exception:
        return []
