import json
import time
import urllib.parse
import urllib.request


def reconstruct_abstract(inverted_index: dict) -> str:
    """
    Восстанавливает связный текст аннотации из инвертированного индекса OpenAlex.
    """
    if not inverted_index:
        return "Аннотация отсутствует."

    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))

    word_positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in word_positions)


def fetch_articles(query: str, max_results: int = 50) -> list[dict]:
    """
    Ищет статьи в OpenAlex с поддержкой пагинации (выгружает до max_results штук).
    """
    encoded_query = urllib.parse.quote(query)
    articles = []
    page = 1
    per_page = min(max_results, 100)  # Сервер отдаёт до 100 результатов за 1 запрос

    headers = {
        "User-Agent": "AcademicGapFinder/1.0 (mailto:student@example.com)"
    }

    print(f"📡 Скачиваем массив статей по запросу '{query}'...")

    while len(articles) < max_results:
        url = f"https://api.openalex.org/works?search={encoded_query}&per_page={per_page}&page={page}"
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                results = data.get("results", [])

                if not results:
                    break  # Статьи по запросу закончились на сервере

                for item in results:
                    title = item.get("display_name") or "Без названия"
                    year = item.get("publication_year") or "Год не указан"
                    doi = item.get("doi") or "Ссылка отсутствует"

                    inverted_abstract = item.get("abstract_inverted_index")
                    abstract = reconstruct_abstract(inverted_abstract)

                    articles.append(
                        {
                            "title": title,
                            "year": year,
                            "doi": doi,
                            "abstract": abstract,
                        }
                    )

                    if len(articles) >= max_results:
                        break

                page += 1
                time.sleep(0.1)  # Вежливая пауза между страницами

        except Exception as e:
            print(f"❌ Ошибка при выгрузке страницы {page}: {e}")
            break

    return articles


# --- Блок тестирования модуля ---
if __name__ == "__main__":
    print("🔎 Тестируем загрузку БОЛЬШОГО массива статей (50 шт)...\n")
    test_query = "Japanese linguistics"

    # Пробуем выкачать сразу 50 статей!
    results = fetch_articles(test_query, max_results=50)

    print(
        f"\n✅ Успешно загружено и обработано статей: {len(results)} из 50!"
    )
    print("=" * 50)

    print("\nПервые 3 статьи из списка:")
    for i, article in enumerate(results[:3], 1):
        print(f"[{i}] {article['title']} ({article['year']})")

    print(f"\n...и ещё {len(results) - 3} статей успешно сохранены в памяти!")