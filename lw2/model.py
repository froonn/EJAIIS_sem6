# --- MODEL ---

import sqlite3
import os
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
            cursor.execute('PRAGMA foreign_keys = ON')

            # Справочник частей речи
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS pos_types
                           (
                               id   INTEGER PRIMARY KEY AUTOINCREMENT,
                               code TEXT NOT NULL UNIQUE,
                               name TEXT
                           )
                           ''')

            # Наполнение справочника pymorphy2 POS-тегами
            pos_data = [
                ('NOUN', 'имя существительное'),
                ('ADJF', 'имя прилагательное(полное)'),
                ('ADJS', 'имя прилагательное(краткое)'),
                ('COMP', 'компаратив'),
                ('VERB', 'глагол(личная форма)'),
                ('INFN', 'глагол(инфинитив)'),
                ('PRTF', 'причастие(полное)'),
                ('PRTS', 'причастие(краткое)'),
                ('GRND', 'деепричастие'),
                ('NUMR', 'числительное'),
                ('ADVB', 'наречие'),
                ('NPRO', 'местоимение-существительное'),
                ('PRED', 'предикатив'),
                ('PREP', 'предлог'),
                ('CONJ', 'союз'),
                ('PRCL', 'частица'),
                ('INTJ', 'междометие'),
                ('UNKN', 'неизвестно'),
            ]
            cursor.executemany(
                'INSERT OR IGNORE INTO pos_types (code, name) VALUES (?, ?)',
                pos_data
            )

            # Источники текстов
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS sources
                           (
                               id        INTEGER PRIMARY KEY AUTOINCREMENT,
                               file_path TEXT,
                               file_name TEXT NOT NULL
                           )
                           ''')

            # Предложения
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS sentences
                           (
                               id        INTEGER PRIMARY KEY AUTOINCREMENT,
                               source_id INTEGER NOT NULL,
                               text      TEXT    NOT NULL,

                               FOREIGN KEY (source_id) REFERENCES sources (id) ON DELETE CASCADE
                           )
                           ''')

            # Лексемы (уникальные леммы)
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS lexemes
                           (
                               id    INTEGER PRIMARY KEY AUTOINCREMENT,
                               lemma TEXT NOT NULL UNIQUE
                           )
                           ''')

            # Словоформы лексемы
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS wordforms
                           (
                               id        INTEGER PRIMARY KEY AUTOINCREMENT,
                               lexeme_id INTEGER NOT NULL,
                               word      TEXT    NOT NULL,
                               pos_id    INTEGER,
                               tags      TEXT,

                               UNIQUE (lexeme_id, word),
                               FOREIGN KEY (pos_id) REFERENCES pos_types (id),
                               FOREIGN KEY (lexeme_id) REFERENCES lexemes (id) ON DELETE CASCADE
                           )
                           ''')

            # Токены в предложениях
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS tokens
                           (
                               id          INTEGER PRIMARY KEY AUTOINCREMENT,
                               sentence_id INTEGER NOT NULL,
                               wordform_id INTEGER NOT NULL,
                               position    INTEGER,

                               FOREIGN KEY (sentence_id) REFERENCES sentences (id) ON DELETE CASCADE,
                               FOREIGN KEY (wordform_id) REFERENCES wordforms (id)
                           )
                           ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_sentence  ON tokens(sentence_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_wordform  ON tokens(wordform_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_wordform_word   ON wordforms(word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_wordform_lexeme ON wordforms(lexeme_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_lexeme_lemma    ON lexemes(lemma)')

            conn.commit()

    def extract_text(self, file_path=None):
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
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        elif ext == '.rtf':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = rtf_to_text(f.read())

        elif ext == '.doc':
            with open(file_path, 'rb') as f:
                content = f.read()
                text = "".join([chr(b) if 32 <= b <= 126 or 1040 <= b <= 1103 else " " for b in content])

        return text

    def _get_or_create_lexeme(self, cursor, lemma):
        """Получить или создать лексему, вернуть её id"""
        cursor.execute('SELECT id FROM lexemes WHERE lemma = ?', (lemma,))
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute(
            'INSERT INTO lexemes (lemma) VALUES (?)',
            (lemma,))
        return cursor.lastrowid

    def _get_or_create_wordform(self, cursor, lexeme_id, word, pos_code, tags):
        """Получить или создать словоформу, вернуть её id"""
        cursor.execute(
            'SELECT id FROM wordforms WHERE lexeme_id = ? AND word = ?',
            (lexeme_id, word)
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute('SELECT id FROM pos_types WHERE code = ?', (pos_code,))
        pos_row = cursor.fetchone()
        pos_id = pos_row[0] if pos_row else None

        cursor.execute(
            'INSERT INTO wordforms (lexeme_id, word, pos_id, tags) VALUES (?, ?, ?, ?)',
            (lexeme_id, word, pos_id, tags)
        )
        return cursor.lastrowid

    def add_to_corpus(self, text, source=None):
        """Лингвистическая разметка текста и сохранение в БД"""
        if not MORPH:
            return

        file_name = os.path.basename(source) if source else "unknown"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            cursor.execute(
                'INSERT INTO sources (file_path, file_name) VALUES (?, ?)',
                (source, file_name)
            )
            source_id = cursor.lastrowid

            sentences = re.split(r'(?<=[.!?])\s+', text)

            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue

                cursor.execute(
                    'INSERT INTO sentences (source_id, text) VALUES (?, ?)',
                    (source_id, sent)
                )
                sentence_id = cursor.lastrowid

                words = re.findall(r'\b[а-яА-ЯёЁa-zA-Z\'-]+\b', sent)
                for pos_in_sent, word in enumerate(words):
                    p = MORPH.parse(word)[0]
                    lemma = p.normal_form
                    pos_code = str(p.tag.POS) if p.tag.POS else 'UNKN'
                    tags = str(p.tag)

                    lexeme_id = self._get_or_create_lexeme(cursor, lemma)
                    wordform_id = self._get_or_create_wordform(cursor, lexeme_id, word, pos_code, tags)

                    cursor.execute(
                        'INSERT INTO tokens (sentence_id, wordform_id, position) VALUES (?, ?, ?)',
                        (sentence_id, wordform_id, pos_in_sent)
                    )

            conn.commit()

    def delete_all(self):
        """Полная очистка БД"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')
            cursor.execute('DELETE FROM tokens')
            cursor.execute('DELETE FROM wordforms')
            cursor.execute('DELETE FROM lexemes')
            cursor.execute('DELETE FROM sentences')
            cursor.execute('DELETE FROM sources')
            conn.commit()

    def delete_by_word(self, word):
        """Удаление токенов по точному совпадению словоформы"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')
            cursor.execute('''
                           DELETE
                           FROM tokens
                           WHERE wordform_id IN (SELECT id
                                                 FROM wordforms
                                                 WHERE LOWER(word) = ?)
                           ''', (word.lower(),))
            conn.commit()

    def delete_by_lemma(self, lemma):
        """Удаление токенов по лемме"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')
            cursor.execute('''
                           DELETE
                           FROM tokens
                           WHERE wordform_id IN (SELECT wf.id
                                                 FROM wordforms wf
                                                          JOIN lexemes lx ON wf.lexeme_id = lx.id
                                                 WHERE LOWER(lx.lemma) = ?)
                           ''', (lemma.lower(),))
            conn.commit()

    def delete_by_pos(self, pos):
        """Удаление токенов по части речи"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')
            cursor.execute('''
                           DELETE
                           FROM tokens
                           WHERE wordform_id IN (SELECT wf.id
                                                 FROM wordforms wf
                                                          JOIN lexemes lx ON wf.lexeme_id = lx.id
                                                          JOIN pos_types pt ON wf.pos_id = pt.id
                                                 WHERE pt.code = ?)
                           ''', (pos.upper(),))
            conn.commit()

    def search(self, query=None, tag_filter=None):
        """Поиск по словоформе, лемме или тегам"""

        query = query.lower() if query else None
        tag_filter = tag_filter.upper() if tag_filter else None

        sql = '''
              SELECT wf.word,
                     lx.lemma,
                     wf.tags                               AS tags,
                     s.text                                AS context,
                     src.file_name                         AS source,
                     COUNT(t.id) OVER (PARTITION BY wf.id) AS word_freq,
                     COUNT(t.id) OVER (PARTITION BY lx.id) AS lemma_freq
              FROM tokens t
                       JOIN wordforms wf ON t.wordform_id = wf.id
                       JOIN lexemes lx ON wf.lexeme_id = lx.id
                       LEFT JOIN pos_types pt ON wf.pos_id = pt.id
                       JOIN sentences s ON t.sentence_id = s.id
                       JOIN sources src ON s.source_id = src.id
              '''

        conditions = []
        params = []

        if query:
            conditions.append("(LOWER(wf.word) = ? OR LOWER(lx.lemma) = ?)")
            params.extend([query, query])

        if tag_filter:
            conditions.append("wf.tags LIKE ?")
            params.append(f"%{tag_filter}%")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)

            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self):
        """Получение статистики из БД"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM tokens')
            total = cursor.fetchone()[0]

            if total == 0:
                return None

            cursor.execute('SELECT COUNT(*) FROM wordforms')
            unique = cursor.fetchone()[0]

            cursor.execute('''
                           SELECT TRIM(tag_part.value) AS tag,
                                  COUNT(*)             AS freq
                           FROM tokens t
                                    JOIN wordforms wf ON t.wordform_id = wf.id,
                                json_each('["' || REPLACE(REPLACE(wf.tags, ',', '","'), ' ', '","') || '"]') AS tag_part
                           WHERE TRIM(tag_part.value) != ''
                           GROUP BY TRIM(tag_part.value)
                           ORDER BY freq DESC
                           ''')
            tag_freq = cursor.fetchall()

            return {
                'total': total,
                'unique': unique,
                'tag_freq': tag_freq,
            }

    def export_json(self):
        """Экспорт всех данных корпуса в виде списка записей"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                           SELECT src.file_path AS source_path,
                                  src.file_name AS source_name,
                                  s.text        AS sentence,
                                  wf.word       AS word,
                                  lx.lemma      AS lemma,
                                  pt.code       AS pos,
                                  wf.tags       AS tags,
                                  t.position    AS position
                           FROM tokens t
                                    JOIN wordforms wf ON t.wordform_id = wf.id
                                    JOIN lexemes lx ON wf.lexeme_id = lx.id
                                    LEFT JOIN pos_types pt ON wf.pos_id = pt.id
                                    JOIN sentences s ON t.sentence_id = s.id
                                    JOIN sources src ON s.source_id = src.id
                           ORDER BY src.id, s.id, t.position
                           ''')
            return [dict(row) for row in cursor.fetchall()]

    def import_json(self, records):
        """
        Импорт данных из списка записей JSON.
        Каждая запись: {source_path, source_name, sentence, word, lemma, pos, tags, position}
        Существующие данные не удаляются — записи добавляются поверх.
        """
        if not records:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('PRAGMA foreign_keys = ON')

            # Группируем токены по (source_name, sentence)
            from collections import defaultdict
            groups = defaultdict(list)
            for rec in records:
                key = (rec.get('source_path'), rec.get('source_name', 'unknown'), rec.get('sentence', ''))
                groups[key].append(rec)

            for (source_path, source_name, sentence_text), tokens in groups.items():
                # Источник
                cursor.execute(
                    'INSERT INTO sources (file_path, file_name) VALUES (?, ?)',
                    (source_path, source_name)
                )
                source_id = cursor.lastrowid

                # Предложение
                cursor.execute(
                    'INSERT INTO sentences (source_id, text) VALUES (?, ?)',
                    (source_id, sentence_text)
                )
                sentence_id = cursor.lastrowid

                for rec in sorted(tokens, key=lambda r: r.get('position', 0)):
                    word = rec.get('word', '')
                    lemma = rec.get('lemma', '')
                    pos = rec.get('pos', 'UNKN')
                    tags = rec.get('tags', '')

                    lexeme_id = self._get_or_create_lexeme(cursor, lemma)
                    wordform_id = self._get_or_create_wordform(cursor, lexeme_id, word, pos, tags)

                    cursor.execute(
                        'INSERT INTO tokens (sentence_id, wordform_id, position) VALUES (?, ?, ?)',
                        (sentence_id, wordform_id, rec.get('position', 0))
                    )

            conn.commit()
