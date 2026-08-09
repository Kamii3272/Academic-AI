import chromadb


class VectorEngine:

    def __init__(self, collection_name="academic_articles"):
        """
        Инициализирует ChromaDB и ВСЕГДА очищает старую коллекцию перед новым поиском.
        """
        self.client = chromadb.Client()

        # Удаляем старую коллекцию с предыдущего поиска, если она существует
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass

        # Создаем свежую чистую коллекцию
        self.collection = self.client.create_collection(name=collection_name)

    def add_articles(self, articles: list[dict]):
        """
        Добавляет выгруженные статьи в векторную базу.
        """
        if not articles:
            return

        documents = []
        metadatas = []
        ids = []

        for idx, art in enumerate(articles):
            text_content = (
                f"{art.get('title', '')}. {art.get('abstract', '')}"
            )

            # Пропускаем пустые тексты
            if not text_content.strip():
                continue

            documents.append(text_content)
            metadatas.append(
                {
                    "title": art.get("title", "Без названия"),
                    "year": str(art.get("year", "N/A")),
                    "doi": art.get("doi", ""),
                }
            )
            ids.append(f"art_{idx}")

        if documents:
            self.collection.add(
                documents=documents, metadatas=metadatas, ids=ids
            )

    def find_similar(self, query: str, n_results: int = 5) -> list[dict]:
        """
        Ищет наиболее семантически близкие статьи в ChromaDB.
        """
        count = self.collection.count()
        if count == 0:
            return []

        # Корректируем количество выводимых результатов
        actual_n = min(n_results, count)

        results = self.collection.query(query_texts=[query], n_results=actual_n)

        similar_articles = []
        if results and "metadatas" in results and results["metadatas"]:
            for i, meta in enumerate(results["metadatas"][0]):
                doc_text = (
                    results["documents"][0][i]
                    if "documents" in results
                    else ""
                )
                similar_articles.append(
                    {
                        "title": meta.get("title"),
                        "year": meta.get("year"),
                        "doi": meta.get("doi"),
                        "abstract": doc_text,
                    }
                )

        return similar_articles