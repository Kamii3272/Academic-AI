import urllib.parse
import requests
from config import DEFAULT_MAX_RESULTS, USER_AGENT

# Точный фразовый поиск в кавычках ("..."), чтобы база не искала слова отдельно
QUERY_TRANSLATIONS = {
    "сетевая инженерия": '"network engineering"',
    "компьютерные сети": '"computer networks"',
    "кибербезопасность": '"cybersecurity"',
    "искусственный интеллект": '"artificial intelligence"',
    "машинное обучение": '"machine learning"',
}


def prepare_search_query(user_query: str) -> str:
    """Трансформирует запрос в точную фразу для OpenAlex."""
    cleaned = user_query.strip().lower()

    if cleaned in QUERY_TRANSLATIONS:
        return QUERY_TRANSLATIONS[cleaned]

    # Если запрос состоит из нескольких слов и еще не обернут в кавычки
    if " " in user_query and not user_query.startswith('"'):
        return f'"{user_query}"'

    return user_query


def fetch_articles(
    query: str, max_results: int = DEFAULT_MAX_RESULTS
) -> list[dict]:
    """Выгружает строго релевантные публикации из OpenAlex API."""
    optimized_query = prepare_search_query(query)
    encoded_query = urllib.parse.quote(optimized_query)

    url = f"https://api.openalex.org/works?search={encoded_query}&per-page={max_results}&sort=relevance_score:desc"
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []

        data = response.json()
        results = data.get("results", [])
        articles = []

        # Проверка: ищем ли мы именно сетевую инженерию / компьютерные сети
        is_network_eng = "network engineering" in optimized_query.lower() or "сетевая инженерия" in query.lower()

        for item in results:
            title = item.get("display_name") or "Без названия"
            year = item.get("publication_year") or "Год не указан"
            doi = item.get("doi") or ""

            title_lower = title.lower()

            # ФИЛЬТР ЛОЖНЫХ СОВПАДЕНИЙ:
            # Если ищем сетевую инженерию, отбрасываем статьи про нейросети (Neural Networks),
            # если в их названии нет слов "engineering" или "protocol"
            if is_network_eng and "neural network" in title_lower and "engineering" not in title_lower:
                continue

            # Восстанавливаем аннотацию
            abstract_dict = item.get("abstract_inverted_index")
            abstract = ""
            if abstract_dict:
                word_positions = []
                for word, positions in abstract_dict.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join([word for _, word in word_positions])

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
