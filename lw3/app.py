# app.py

import streamlit as st
import lib
from graphviz import Source
import os

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="NLP Syntax Analyzer",
    page_icon="🌳",
    layout="wide"
)

# Инициализируем базу данных при первом запуске
if 'db_initialized' not in st.session_state:
    lib.init_db()
    st.session_state['db_initialized'] = True

st.title("🌳 NLP Syntax & Structure Analyzer")
st.markdown("""
Этот инструмент позволяет анализировать синтаксическую структуру предложений (Dependency & Constituency) 
и сохранять результаты в локальную базу данных SQLite.
""")

# --- БОКОВАЯ ПАНЕЛЬ (Загрузка PDF) ---
st.sidebar.header("📥 Загрузка данных")
uploaded_file = st.sidebar.file_uploader("Выберите PDF файл для анализа", type="pdf")

if uploaded_file:
    if st.sidebar.button("Начать обработку PDF"):
        # Сохраняем временный файл, чтобы lib.py мог его прочитать
        with open("temp_upload.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Извлекаем текст и анализируем предложения..."):
            lib.process_pdf("temp_upload.pdf")
            os.remove("temp_upload.pdf")
        st.sidebar.success("Обработка завершена!")
        st.rerun()

st.sidebar.divider()
st.sidebar.write(f"📊 Всего записей в базе: **{lib.count_records()}**")

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
tab_search, tab_direct = st.tabs(["🔍 Поиск и Визуализация", "✍️ Ручной ввод"])

with tab_search:
    query = st.text_input("Поиск по предложениям в базе данных:", placeholder="Введите часть предложения...")

    if query:
        search_results = lib.search_sentences(query)

        if search_results:
            # Формируем список для выбора (текст предложения с привязкой к ID)
            options = {f"ID {res[0]}: {res[1][:100]}...": res[0] for res in search_results}
            selected_option = st.selectbox("Выберите предложение для просмотра:", options.keys())

            pk = options[selected_option]
            data = lib.get_data_by_id(pk)

            if data:
                sentence_text, dep_dot, const_dot = data

                st.info(f"**Предложение:** {sentence_text}")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Dependency Tree")
                    if dep_dot:
                        st.graphviz_chart(dep_dot)
                    else:
                        st.write("Граф зависимостей отсутствует.")

                with col2:
                    st.subheader("Constituency Tree")
                    if "Error" in const_dot:
                        st.error(const_dot)
                    elif const_dot:
                        st.graphviz_chart(const_dot)
                    else:
                        st.write("Граф составляющих отсутствует.")
        else:
            st.warning("Ничего не найдено.")
    else:
        st.info("Введите запрос выше, чтобы найти предложения в базе данных.")

with tab_direct:
    with st.form("manual_input"):
        raw_text = st.text_area("Введите предложение для мгновенного анализа:")
        submit = st.form_submit_button("Проанализировать и сохранить")

        if submit and raw_text:
            with st.spinner("Анализ..."):
                lib.process_and_save_sentence(raw_text)
                st.success("Предложение обработано и добавлено в базу.")
                # После добавления можно сразу найти его в поиске