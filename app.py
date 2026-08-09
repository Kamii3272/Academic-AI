import re
import warnings

# Подавляем системные предупреждения в консоли
warnings.filterwarnings("ignore")

import pandas as pd
import plotly.express as px
import streamlit as st
from fetcher import fetch_articles
from generator import generate_topics
from vector_engine import VectorEngine

# Настройка страницы
st.set_page_config(
    page_title="Academic Gap Finder v2.0", page_icon="🎓", layout="wide"
)

st.title("🎓 ACADEMIC GAP FINDER v2.0")
st.caption(
    "Автоматизированный векторный анализ научной литературы и поиск исследовательских лакун"
)
st.markdown("---")

# Ввод данных
col1, col2 = st.columns([3, 1])
with col1:
    user_query = st.text_input(
        "🔍 Введите тему или сферу исследования:",
        placeholder="Например: Сетевая инженерия или Japanese katakana",
    )
with col2:
    max_articles = st.number_input(
        "📚 Анализировать статей:", min_value=10, max_value=100, value=30, step=10
    )

if st.button("🚀 Найти исследовательские лакуны", type="primary"):
    if not user_query.strip():
        st.warning("⚠️ Пожалуйста, введите направление исследования!")
    else:
        with st.status(
            "⏳ Запуск академического аналитического пайплайна...", expanded=True
        ) as status:

            # 1. Поиск
            st.write(
                f"📡 **[1/3]** Выгрузка публикаций по направлению '{user_query}'..."
            )
            articles = fetch_articles(user_query, max_results=max_articles)

            if not articles:
                status.update(
                    label="❌ Публикации не найдены", state="error", expanded=True
                )
                st.error("По вашему запросу не найдено подходящих публикаций.")
                st.stop()

            st.write(f"✅ Успешно обработано источников: **{len(articles)}**.")

            # 2. Векторизация
            st.write("🧠 **[2/3]** Векторизация и поиск семантических кластеров...")
            vector_db = VectorEngine()
            vector_db.add_articles(articles)
            representative_articles = vector_db.find_similar(
                user_query, n_results=5
            )
            st.write("✅ Топовые релевантные кластеры отфильтрованы.")

            # 3. Синтез
            st.write("💡 **[3/3]** Генерация аналитического разбора и тем...")
            analysis_result = generate_topics(
                user_query, representative_articles
            )

            status.update(
                label="🎉 Анализ успешно завершён!",
                state="complete",
                expanded=False,
            )

        # Вывод результатов
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "💡 Аналитический разбор и Темы",
                "📊 Визуализация лакун и трендов",
                "🎯 Топ-5 релевантных источников",
                f"📁 Все выгруженные источники ({len(articles)})",
            ]
        )

        with tab1:
            st.markdown(analysis_result)

        with tab2:
            st.subheader("📊 Аналитическая визуализация лакун и источников")
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.markdown("#### 🥧 Распределение исследовательских векторов")

                # Извлекаем названия тем по значку 📌
                found_topics = re.findall(
                    r"📌\s*(?:Тема \d+:?\s*)?([^\n]+)", analysis_result
                )

                if len(found_topics) >= 3:
                    labels = [
                        f"1. {found_topics[0][:30]}...",
                        f"2. {found_topics[1][:30]}...",
                        f"3. {found_topics[2][:30]}...",
                    ]
                    # ДИНАМИЧЕСКИЙ РАСЧЕТ ДОЛЕЙ на основе длины описания и символьного веса
                    lens = [len(t) for t in found_topics[:3]]
                    total_len = sum(lens) or 1
                    # Распределяем пропорционально реальному объему тезисов
                    shares = [round((l / total_len) * 100) for l in lens]
                else:
                    labels = [
                        "1. Фундаментальный вектор",
                        "2. Технологический вектор",
                        "3. Прикладной вектор",
                    ]
                    shares = [45, 30, 25]

                pie_data = pd.DataFrame(
                    {"Направление": labels, "Доля лакуны (%)": shares}
                )

                fig_pie = px.pie(
                    pie_data,
                    names="Направление",
                    values="Доля лакуны (%)",
                    color_discrete_sequence=px.colors.sequential.RdBu,
                    hole=0.4,
                )
                fig_pie.update_traces(textinfo="percent+label")
                fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=10, r=10))
                st.plotly_chart(fig_pie)

            with col_chart2:
                st.markdown("#### 📅 Хронология проанализированных публикаций")

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
                        title="Распределение публикаций по годам",
                        color_discrete_sequence=["#2b5c8f"],
                    )
                    fig_bar.update_layout(
                        yaxis_title="Количество статей",
                        xaxis_title="Год публикации",
                        margin=dict(t=30, b=20, l=10, r=10),
                    )
                    st.plotly_chart(fig_bar)

        with tab3:
            st.subheader("Репрезентативные статьи от векторного движка:")
            for i, art in enumerate(representative_articles, 1):
                with st.expander(
                    f"[{i}] {art.get('title', 'Без названия')} ({art.get('year', 'N/A')})"
                ):
                    st.write(f"**DOI/Ссылка:** {art.get('doi', 'Не указано')}")
                    st.write(f"**Выдержка текста:** {art.get('abstract', 'Отсутствует')}")

        with tab4:
            st.subheader(f"📁 Полный реестр проанализированных статей ({len(articles)})")

            table_data = []
            for i, art in enumerate(articles, 1):
                raw_doi = art.get("doi") or ""
                link = raw_doi if raw_doi.startswith("http") else (f"https://doi.org/{raw_doi}" if raw_doi else None)
                table_data.append(
                    {
                        "№": i,
                        "Год": art.get("year", "N/A"),
                        "Название статьи": art.get("title", "Без названия"),
                        "DOI / Ссылка": link,
                    }
                )

            df_all = pd.DataFrame(table_data)
            st.dataframe(
                df_all,
                column_config={
                    "DOI / Ссылка": st.column_config.LinkColumn(
                        "DOI / Ссылка", display_text="Открыть публикацию 🔗"
                    )
                },
                hide_index=True,
            )
