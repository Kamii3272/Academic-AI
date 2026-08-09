import urllib.parse
import requests
from config import DEFAULT_MAX_RESULTS, USER_AGENT

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

    if " " in user_query and not user_query.startswith('"'):
        return f'"{user_query}"'

    return user_query


def fetch_articles(
    query: str, max_results: int = DEFAULT_MAX_RESULTS
) -> list[dict]:
    """Выгружает релевантные публикации из OpenAlex API со стопроцентным генератором ссылок."""
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

        is_network_eng = (
            "network engineering" in optimized_query.lower()
            or "сетевая инженерия" in query.lower()
        )

        for item in results:
            title = item.get("display_name") or "Без названия"
            year = item.get("publication_year") or "Год не указан"

            # 1. Проверяем DOI
            raw_doi = item.get("doi") or ""
            best_link = ""
            if raw_doi:
                best_link = (
                    raw_doi
                    if raw_doi.startswith("http")
                    else f"https://doi.org/{raw_doi}"
                )

            # 2. Если DOI нет — ищем прямую страницу издателя / PDF
            if not best_link:
                primary_loc = item.get("primary_location") or {}
                if isinstance(primary_loc, dict):
                    best_link = (
                        primary_loc.get("landing_page_url")
                        or primary_loc.get("pdf_url")
                        or ""
                    )

            # 3. Если и этого нет — берем ссылку на OpenAlex карточку
            if not best_link:
                best_link = item.get("id") or ""

            # 4. Фолбэк: Прямой поиск в Google Scholar по названию
            if not best_link:
                encoded_title = urllib.parse.quote(f'"{title}"')
                best_link = (
                    f"https://scholar.google.com/scholar?q={encoded_title}"
                )

            title_lower = title.lower()
            if (
                is_network_eng
                and "neural network" in title_lower
                and "engineering" not in title_lower
            ):
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

            if title and len(title) > 3:
                articles.append(
                    {
                        "title": title,
                        "year": str(year),
                        "doi": best_link,  # Теперь здесь ВСЕГДА валидный URL
                        "abstract": abstract,
                    }
                )

        return articles

    except Exception:
        return []
