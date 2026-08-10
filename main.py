import warnings
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fetcher import fetch_articles
from generator import generate_topics
from vector_engine import VectorEngine

warnings.filterwarnings("ignore")

app = FastAPI(title="Lacuna AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str
    max_articles: int = 30


@app.get("/")
def health_check():
    return {"status": "online", "message": "Lacuna AI Backend is running"}


@app.post("/api/analyze")
async def analyze(req: SearchRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(
            status_code=400, detail="Запрос не может быть пустым"
        )

    articles = fetch_articles(query, max_results=req.max_articles)
    if not articles:
        raise HTTPException(
            status_code=404, detail="Публикации по запросу не найдены"
        )

    try:
        vector_db = VectorEngine()
        vector_db.add_articles(articles)
        top_articles = vector_db.find_similar(query, n_results=5)
    except Exception:
        top_articles = articles[:5]

    raw_markdown = generate_topics(query, top_articles)

    years = [
        int(a["year"]) for a in articles if str(a.get("year", "")).isdigit()
    ]
    year_counts = {}
    for y in sorted(years):
        year_counts[y] = year_counts.get(y, 0) + 1

    timeline_data = [
        {"year": str(y), "count": count} for y, count in year_counts.items()
    ]

    return {
        "query": query,
        "total_articles": len(articles),
        "analysis_markdown": raw_markdown,
        "top_articles": top_articles,
        "all_articles": articles,
        "timeline_data": timeline_data,
    }
if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n\n👋 Работа программы завершена.")
        sys.exit(0)
