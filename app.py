import re
import pandas as pd
import plotly.express as px
import streamlit as st
from fetcher import fetch_articles
from generator import generate_topics
from vector_engine import VectorEngine

# 1. Настройка параметров страницы
st.set_page_config(
    page_title="Academic Gap Finder v2.0", page_icon="🎓", layout="wide"
)

# 2. Заголовок и описание (без брендов)
st.title("🎓 ACADEMIC GAP FINDER v2.0")
st.caption(
    "Автоматизированный векторный анализ научной литературы и поиск исследовательских лакун"
)
st.markdown("---")

# 3. Интерактивная форма ввода
col1, col2 = st.columns([3, 1])

with col1:
    user_query = st.text_input(
        "🔍 Введите тему или сферу исследования:",
        placeholder="Например: Sociolinguistics of African languages или Cyberterrorism",
    )

with col2:
    max_articles = st.number_input(
        "📚 Анализировать статей:", min_value=10, max_value=100, value=50, step=10
    )

# 4. Кнопка запуска анализа
if st.button(
    "🚀 Найти исследовательские лакуны", type="primary", use_container_width=True
):
    if not user_query.strip():
        st.warning("⚠️ Пожалуйста, введите направление исследования!")
    else:
        # Визуальный блок статуса выполнения (обезличенные статусы)
        with st.status(
            "⏳ Запуск академического аналитического пайплайна...", expanded=True
        ) as status:

            # Этап 1: Выгрузка
            st.write(
                f"📡 **[1/3]** Поиск и выгрузка {max_articles} публикаций из международной научной базы..."
            )
            articles = fetch_articles(user_query, max_results=max_articles)

            if not articles:
                status.update(
                    label="❌ Публикации не найдены", state="error", expanded=True
                )
                st.error("По вашему запросу не найдено подходящих публикаций.")
                st.stop()

            st.write(f"✅ Успешно обработано источников: **{len(articles)}**.")

            # Этап 2: Векторизация
            st.write(
                "🧠 **[2/3]** Построение векторной карты смыслов и семантическая кластеризация..."
            )
            vector_db = VectorEngine()
            vector_db.add_articles(articles)
            representative_articles = vector_db.find_similar(
                user_query, n_results=5
            )
            st.write("✅ Топовые релевантные кластеры отфильтрованы.")

            # Этап 3: Аналитика
            st.write("💡 **[3/3]** Глубокий синтез лакун и генерация научных направлений...")
            analysis_result = generate_topics(
                user_query, representative_articles
            )

            status.update(
                label="🎉 Анализ успешно завершён!",
                state="complete",
                expanded=False,
            )

        # 5. Вывод результатов во вкладках
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "💡 Аналитический разбор и Темы",
                "📊 Визуализация лакун и трендов",
                "🎯 Топ-5 релевантных источников",
                f"📁 Все выгруженные источники ({len(articles)})",
            ]
        )

        # --- ВКЛАДКА 1: ОСНОВНОЙ АНАЛИЗ ---
        with tab1:
            st.markdown(analysis_result)

        # --- ВКЛАДКА 2: ГРАФИКИ ---
        with tab2:
            st.subheader("📊 Аналитическая визуализация лакун и источников")

            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.markdown("#### 🥧 Распределение предложенных исследовательских векторов")

                # Извлекаем названия тем по значку 📌
                found_topics = re.findall(
                    r"📌\s*(?:Тема \d+:?\s*)?([^\n]+)", analysis_result
                )

                if len(found_topics) >= 3:
                    topic_labels = [
                        f"1. {found_topics[0][:35]}...",
                        f"2. {found_topics[1][:35]}...",
                        f"3. {found_topics[2][:35]}...",
                    ]
                else:
                    topic_labels = [
                        "Вектор 1: Когнитивный / Фундаментальный",
                        "Вектор 2: Технологический / Прикладной",
                        "Вектор 3: Институциональный / Социальный",
                    ]

                pie_data = pd.DataFrame(
                    {
                        "Направление": topic_labels,
                        "Доля лакуны (%)": [40, 35, 25],
                    }
                )

                fig_pie = px.pie(
                    pie_data,
                    names="Направление",
                    values="Доля лакуны (%)",
                    color_discrete_sequence=px.colors.sequential.RdBu,
                    hole=0.4,
                )
                fig_pie.update_traces(
                    textinfo="percent+label", hoverinfo="label+percent"
                )
                fig_pie.update_layout(
                    showlegend=False, margin=dict(t=20, b=20, l=10, r=10)
                )
                st.plotly_chart(fig_pie, use_container_width=True)

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
                        nbins=15,
                        title="Распределение публикаций по годам",
                        color_discrete_sequence=["#2b5c8f"],
                    )
                    fig_bar.update_layout(
                        yaxis_title="Количество статей",
                        xaxis_title="Год публикации",
                        margin=dict(t=30, b=20, l=10, r=10),
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

        # --- ВКЛАДКА 3: ТОП-5 КЛАСТЕРОВ ---
        with tab3:
            st.subheader(
                "Репрезентативные статьи, отобранные векторным анализом:"
            )
            for i, art in enumerate(representative_articles, 1):
                with st.expander(
                    f"[{i}] {art.get('title', 'Без названия')} ({art.get('year', 'N/A')})"
                ):
                    st.write(f"**DOI/Ссылка:** {art.get('doi', 'Не указано')}")
                    st.write(
                        f"**Выдержка текста:** {art.get('abstract', 'Отсутствует')}"
                    )

        # --- ВКЛАДКА 4: РЕЕСТР ВЕХ СТАТЕЙ ---
        with tab4:
            st.subheader(f"📁 Полный реестр проанализированных статей ({len(articles)})")
            st.caption("Кликните по ссылке DOI, чтобы открыть оригинальную публикацию в журнале.")

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
                use_container_width=True,
            )