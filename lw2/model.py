# --- MODEL ---

import sqlite3
import re

from collections import Counter

try:
    import docx
    from PyPDF2 import PdfReader
    from striprtf.striprtf import rtf_to_text
except ImportError:
    docx = None

try:
    import pymorphy2

    MORPH = pymorphy2.MorphAnalyzer()
except ImportError:
    MORPH = None

class CorpusModel:
    def __init__(self, db_path="corpus.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS tokens
                           (
                               id      INTEGER PRIMARY KEY AUTOINCREMENT,
                               word    TEXT,
                               lemma   TEXT,
                               pos     TEXT,
                               tags    TEXT,
                               context TEXT
                           )
                           ''')
            # Индексы для ускорения поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON tokens(word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_lemma ON tokens(lemma)')
            conn.commit()

    def extract_text(self, file_path):
        """Извлечение текста из файлов различных форматов"""
        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

        elif ext == '.docx' and docx:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])

        elif ext == '.pdf':
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"

        elif ext == '.rtf':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = rtf_to_text(f.read())

        elif ext == '.doc':
            with open(file_path, 'rb') as f:
                content = f.read()
                text = "".join([chr(b) if 32 <= b <= 126 or 1040 <= b <= 1103 else " " for b in content])

        return text

    def add_to_corpus(self, text):
        """Лингвистическая разметка текста и сохранение в БД"""
        if not MORPH:
            return

        sentences = re.split(r'(?<=[.!?])\s+', text)
        to_insert = []

        for sent in sentences:
            sent = sent.strip()
            if not sent: continue

            words = re.findall(r'\b[а-яА-ЯёЁa-zA-Z-]+\b', sent)
            for word in words:
                p = MORPH.parse(word)[0]
                to_insert.append((
                    word,
                    p.normal_form,
                    str(p.tag.POS),
                    str(p.tag),
                    sent
                ))

        if to_insert:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    'INSERT INTO tokens (word, lemma, pos, tags, context) VALUES (?, ?, ?, ?, ?)',
                    to_insert
                )
                conn.commit()

    def search(self, query):
        """Поиск в БД по слову или лемме"""
        query = query.lower()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'SELECT word, lemma, pos, context FROM tokens WHERE LOWER(word) = ? OR LOWER(lemma) = ?',
                (query, query)
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_all(self):
        """Полная очистка БД"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM tokens')
            conn.commit()

    def delete_by_word(self, word):
        """Удаление по точному совпадению слова"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM tokens WHERE LOWER(word) = ?', (word.lower(),))
            conn.commit()

    def delete_by_lemma(self, lemma):
        """Удаление по лемме"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM tokens WHERE LOWER(lemma) = ?', (lemma.lower(),))
            conn.commit()

    def delete_by_pos(self, pos):
        """Удаление по части речи"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM tokens WHERE pos = ?', (pos.upper(),))
            conn.commit()

    def get_stats(self):
        """Получение статистики из БД"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM tokens')
            total = cursor.fetchone()[0]

            if total == 0:
                return None

            cursor.execute('SELECT COUNT(DISTINCT lemma) FROM tokens')
            unique = cursor.fetchone()[0]

            cursor.execute('SELECT pos, COUNT(*) FROM tokens GROUP BY pos')
            pos_counts = Counter(dict(cursor.fetchall()))

            return {
                'total': total,
                'unique': unique,
                'pos': pos_counts
            }