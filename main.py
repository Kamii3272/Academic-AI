import sys
from fetcher import fetch_articles
from generator import generate_topics
from vector_engine import VectorEngine


def run_pipeline():
    print("=" * 60)
    print("🎓 ACADEMIC GAP FINDER v2.0 (Vector & Semantic Search)")
    print("=" * 60)

    # 1. Запрос от пользователя
    user_query = input(
        "\n🔍 Введите сферу исследования (например, 'Japanese phraseology'): "
    ).strip()

    if not user_query:
        print("❌ Ошибка: Тема не может быть пустой!")
        return

    # 2. Модуль сбора (fetcher) — запрашиваем 50 статей
    print(f"\n📡 [1/3] Выгружаем 50 актуальных публикаций из OpenAlex...")
    articles = fetch_articles(user_query, max_results=50)

    if not articles:
        print("⚠️ По вашему запросу не найдено подходящих статей.")
        return

    print(f"✅ Успешно скачано статей: {len(articles)}")

    # 3. Векторный движок (ChromaDB)
    print(
        f"\n🧠 [2/3] Векторизуем статьи и строим карту смыслов в ChromaDB..."
    )
    vector_db = VectorEngine()
    vector_db.add_articles(articles)

    # Делаем семантическую выборку самых релевантных работ
    representative_articles = vector_db.find_similar(user_query, n_results=5)

    # 4. Модуль генерации (generator)
    print(
        f"\n💡 [3/3] Анализируем плотность смыслов и генерируем темы через LLM..."
    )
    result = generate_topics(user_query, representative_articles)

    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n\n👋 Работа программы завершена.")
        sys.exit(0)