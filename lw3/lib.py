# lib.py

import spacy
import benepar
from graphviz import Digraph
import pdfplumber
import os
import re
import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional

# --- КОНФИГУРАЦИЯ ---
DB_NAME = "nlp_results.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sentences
                 (
                     id             INTEGER PRIMARY KEY AUTOINCREMENT,
                     content        TEXT UNIQUE,
                     dep_tree_dot   TEXT,
                     const_tree_dot TEXT,
                     created_at     DATETIME
                 )''')
    conn.commit()
    conn.close()


def load_nlp_model():
    """Загрузка и настройка NLP конвейера"""
    nlp = spacy.load("en_core_web_sm")
    nlp.max_length = 3000000
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")

    try:
        if "benepar" not in nlp.pipe_names:
            nlp.add_pipe("benepar", config={"model": "benepar_en3"})
    except Exception:
        benepar.download('benepar_en3')
        nlp.add_pipe("benepar", config={"model": "benepar_en3"})
    return nlp


nlp = load_nlp_model()


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ГРАФОВ ---

def generate_dep_dot(doc) -> str:
    """Генерирует DOT-строку для Dependency Tree"""
    dot = Digraph(comment='Dependency Tree')
    dot.attr(rankdir='LR')
    for token in doc:
        label = f"{token.text}\\n[{token.pos_}]"
        dot.node(str(token.i), label)
        if token.dep_ != 'ROOT':
            dot.edge(str(token.head.i), str(token.i), label=token.dep_)
    return dot.source


def generate_const_dot(doc) -> str:
    """Генерирует DOT-строку для Constituency Tree"""
    dot = Digraph(comment='Constituency Tree')
    node_id = [0]

    def add_nodes(node, parent_id=None):
        current_id = str(node_id[0])
        node_id[0] += 1

        if hasattr(node, "_") and hasattr(node._, "labels") and len(node._.labels) > 0:
            label = node._.labels[0]
        else:
            label = node.text

        dot.node(current_id, label)
        if parent_id is not None:
            dot.edge(parent_id, current_id)

        if hasattr(node, "_") and hasattr(node._, "children"):
            for child in node._.children:
                add_nodes(child, current_id)

    for sent in doc.sents:
        add_nodes(sent)
    return dot.source


# --- ОСНОВНЫЕ ФУНКЦИИ ---

# 1. Функция анализа и сохранения одного предложения
def process_and_save_sentence(text: str) -> None:
    """Строит графы и сохраняет в БД"""
    # 1. Улучшенная очистка: убираем всё, что может смутить токенизатор
    clean_text = re.sub(r'\s+', ' ', text).strip()

    # Пропускаем пустые строки или слишком короткие (например, номера страниц)
    if not clean_text or len(clean_text) < 2:
        return

    try:
        # 2. Обработка конкретного предложения
        doc = nlp(clean_text)
        dep_dot = generate_dep_dot(doc)

        const_dot = ""
        # Benepar часто падает на сложных символах, изолируем его
        try:
            const_dot = generate_const_dot(doc)
        except Exception as e:
            const_dot = f"Error in constituency parsing: {e}"

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO sentences
                         (content, dep_tree_dot, const_tree_dot, created_at)
                     VALUES (?, ?, ?, ?)''',
                  (clean_text, dep_dot, const_dot, datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Критическая ошибка на предложении: {clean_text[:50]}... \nОшибка: {e}")

# 2. Функция обработки PDF
def process_pdf(file_path: str) -> None:
    """Извлекает предложения из PDF и обрабатывает их по одному"""
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден.")
        return

    print("Извлечение текста из PDF...")
    all_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # Предварительная замена переносов строк на пробелы
                all_text += text.replace('\n', ' ') + " "

    print("Разбиение на предложения и анализ...")

    # Используем только sentencizer для первичного разбиения, чтобы не грузить benepar
    # Это предотвращает AssertionError при токенизации всего PDF сразу
    temp_nlp = spacy.blank("en")
    temp_nlp.add_pipe("sentencizer")
    doc = temp_nlp(all_text)

    for sent in doc.sents:
        # Передаем по одному чистому предложению в основную модель
        process_and_save_sentence(sent.text)

    print(f"Обработка завершена. Всего записей: {count_records()}")


# 3. Функция поиска по части предложения
def search_sentences(query: str) -> List[Tuple[int, str]]:
    """Возвращает список (id, текст) подходящих предложений"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    search_pattern = f"%{query}%"
    c.execute("SELECT id, content FROM sentences WHERE content LIKE ?", (search_pattern,))
    results = c.fetchall()
    conn.close()
    return results


# 4. Функция получения данных по ID
def get_data_by_id(pk: int) -> Optional[Tuple[str, str, str]]:
    """Возвращает (текст, dep_graph_dot, const_graph_dot) по Primary Key"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT content, dep_tree_dot, const_tree_dot FROM sentences WHERE id = ?", (pk,))
    result = c.fetchone()
    conn.close()
    return result


# 5. Функция подсчета записей
def count_records() -> int:
    """Возвращает общее количество записей в БД"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sentences")
    count = c.fetchone()[0]
    conn.close()
    return count


# --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---
if __name__ == "__main__":
    init_db()

    # # Пример 1: Обработка строки
    # process_and_save_sentence("The cat sits on the mat.")
    #
    # # Пример 2: Поиск
    # results = search_sentences("cat")
    # print(f"Найдено: {results}")
    #
    # if results:
    #     pk = results[0][0]
    #     # Пример 3: Получение по PK
    #     data = get_data_by_id(pk)
    #     print(f"Данные по ID {pk}: {data[0]}")
    #     # data[1] и data[2] содержат DOT-строки для визуализации
    #
    # print(f"Всего записей: {count_records()}")

    process_pdf('/home/froonn/Downloads/TheLittlePrince.pdf')