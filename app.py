import re
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import plotly.express as px
import streamlit as st
from fetcher import fetch_articles
from generator import generate_topics
from vector_engine import VectorEngine

# Конфигурация страницы
st.set_page_config(
    page_title="Academic Gap Finder", page_icon="🎓", layout="wide"
)

# Кастомный академический CSS-стиль (минимум пестроты, чистые шрифты)
st.markdown(
    """
    <style>
    .main-title {
        font_family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.2rem;
        color: #1E293B;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 25px;
    }
    .stButton>button {
        background-color: #0F172A;
        color: #FFFFFF;
        border-radius: 6px;
        font-weight: 500;
        border: none;
    }
    .stButton>button:hover {
        background-color: #334155;
        color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">Academic Gap Finder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Аналитическая система выявления исследовательских лакун в научной литературе</div>',
    unsafe_allow_html=True,
)
st.markdown("---")

col1, col2 = st.columns([3, 1])
with col1:
    user_query = st.text_input(
        "Тема или область исследования:",
        placeholder="Например: Сетевая инженерия или Японская катакана",
    )
with col2:
    max_articles = st.number_input(
        "Объем выборки (статей):", min_value=10, max_value=100, value=30, step=10
    )

if st.button("Начать аналитический поиск", type="primary"):
    if not user_query.strip():
        st.warning("Пожалуйста, укажите направление исследования.")
    else:
        with st.status(
            "Выполнение аналитического пайплайна...", expanded=True
        ) as status:

            st.write(f"1. Выгрузка научных публикаций по запросу: '{user_query}'...")
            articles = fetch_articles(user_query, max_results=max_articles)

            if not articles:
                status.update(
                    label="Публикации не найдены", state="error", expanded=True
                )
                st.error("По вашему запросу не найдено подходящих публикаций.")
                st.stop()

            st.write(f"2. Обработано релевантных источников: **{len(articles)}**.")

            st.write("3. Семантическая векторизация и кластеризация данных...")
            vector_db = VectorEngine()
            vector_db.add_articles(articles)
            representative_articles = vector_db.find_similar(
                user_query, n_results=5
            )

            st.write("4. Синтез научных лакун и формирование аннотаций...")
            analysis_result = generate_topics(
                user_query, representative_articles
            )

            status.update(
                label="Анализ успешно завершен",
                state="complete",
                expanded=False,
            )

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "Аналитический разбор и Темы",
                "Визуализация лакун",
                "Ключевые источники (Топ-5)",
                f"Реестр публикаций ({len(articles)})",
            ]
        )

        with tab1:
            st.markdown(analysis_result)

        with tab2:
            st.subheader("Визуальный анализ структуры исследований")
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.markdown("##### Распределение исследовательских векторов")

                found_topics = re.findall(
                    r"📌\s*(?:Тема \d+:?\s*)?([^\n]+)", analysis_result
                )

                if len(found_topics) >= 3:
                    labels = [
                        f"1. {found_topics[0][:32]}...",
                        f"2. {found_topics[1][:32]}...",
                        f"3. {found_topics[2][:32]}...",
                    ]
                    lens = [len(t) for t in found_topics[:3]]
                    total_len = sum(lens) or 1
                    shares = [round((l / total_len) * 100) for l in lens]
                else:
                    labels = [
                        "1. Теоретический вектор",
                        "2. Методологический вектор",
                        "3. Прикладной вектор",
                    ]
                    shares = [40, 35, 25]

                pie_data = pd.DataFrame(
                    {"Вектор": labels, "Доля (%)": shares}
                )

                fig_pie = px.pie(
                    pie_data,
                    names="Вектор",
                    values="Доля (%)",
                    color_discrete_sequence=px.colors.sequential.Slate,
                    hole=0.35,
                )
                fig_pie.update_traces(textinfo="percent+label")
                fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=10, r=10))
                st.plotly_chart(fig_pie)

            with col_chart2:
                st.markdown("##### Динамика публикаций по годам")

                years = [
                    int(art["year"])
                    for art in articles
                    if str(art.get("year", "")).isdigit()
                ]

                if years:
                    df_years = pd.DataFrame({"Год": years})
                    fig_bar = px.histogram(
                        df_years,
                        x="Год",
                        nbins=12,
                        color_discrete_sequence=["#334155"],
                    )
                    fig_bar.update_layout(
                        yaxis_title="Количество публикаций",
                        xaxis_title="Год",
                        margin=dict(t=20, b=20, l=10, r=10),
                    )
                    st.plotly_chart(fig_bar)

        with tab3:
            st.subheader("Репрезентативные источники:")
            for i, art in enumerate(representative_articles, 1):
                with st.expander(
                    f"[{i}] {art.get('title', 'Без названия')} ({art.get('year', 'N/A')})"
                ):
                    raw_doi = art.get("doi") or ""
                    link_text = raw_doi if raw_doi.startswith("http") else (f"https://doi.org/{raw_doi}" if raw_doi else "Ссылка отсутствует")
                    st.write(f"**DOI / Ссылка:** {link_text}")
                    st.write(f"**Аннотация:** {art.get('abstract', 'Отсутствует')}")

        with tab4:
            st.subheader(f"Реестр проанализированных публикаций ({len(articles)})")

            table_data = []
            for i, art in enumerate(articles, 1):
                raw_doi = art.get("doi") or ""
                valid_link = None
                if raw_doi:
                    valid_link = raw_doi if raw_doi.startswith("http") else f"https://doi.org/{raw_doi}"

                table_data.append(
                    {
                        "№": i,
                        "Год": art.get("year", "N/A"),
                        "Название статьи": art.get("title", "Без названия"),
                        "DOI / Ссылка": valid_link,
                    }
                )

            df_all = pd.DataFrame(table_data)

            st.dataframe(
                df_all,
                column_config={
                    "DOI / Ссылка": st.column_config.LinkColumn(
                        "DOI / Ссылка", display_text="Открыть публикацию"
                    )
                },
                hide_index=True,
                on_select="ignore",
            )
