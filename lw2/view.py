# --- VIEW ---

import re

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel,
    QTabWidget, QTableWidget, QHeaderView,
    QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QColor, QPalette


class CorpusView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Корпусный менеджер")
        self.resize(1200, 850)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.tabs = QTabWidget()

        # Вкладка 1: Корпус (Загрузка)
        self.tab_corpus = QWidget()
        c_layout = QVBoxLayout(self.tab_corpus)
        self.btn_load = QPushButton("Загрузить документы (TXT, PDF, DOCX, RTF, DOC)")
        self.btn_load.setFixedHeight(40)
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        c_layout.addWidget(self.btn_load)
        c_layout.addWidget(QLabel("Предпросмотр последних данных:"))
        c_layout.addWidget(self.text_preview)

        # Вкладка 2: Поиск
        self.tab_search = QWidget()
        s_layout = QVBoxLayout(self.tab_search)

        search_form = QFormLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите слово или лемму...")
        search_form.addRow("Слово / лемма:", self.search_input)
        s_layout.addLayout(search_form)

        self.btn_search = QPushButton("Найти")
        self.btn_search.setFixedHeight(35)
        s_layout.addWidget(self.btn_search)

        tag_box = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Например: NOUN, VERB, plur, sing, accs, ...")
        tag_box.addWidget(QLabel("Фильтр по тегу:"))
        tag_box.addWidget(self.tag_input)
        tag_box.addWidget(self.btn_search)
        s_layout.addLayout(tag_box)

        # Слово, Лемма, Теги, Частота слова, Частота леммы, Контекст, Источник
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(
            ["Слово", "Лемма", "Теги", "Частота слова", "Частота леммы", "Контекст", "Источник"]
        )
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setDefaultSectionSize(120)
        header.resizeSection(0, 100)   # Слово
        header.resizeSection(1, 100)   # Лемма
        header.resizeSection(2, 180)   # Теги
        header.resizeSection(3, 110)   # Частота слова
        header.resizeSection(4, 110)   # Частота леммы
        header.resizeSection(5, 350)   # Контекст
        header.resizeSection(6, 150)   # Источник
        header.setStretchLastSection(False)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setWordWrap(True)

        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        s_layout.addWidget(self.results_table)

        # Вкладка 3: Управление
        self.tab_manage = QWidget()
        m_layout = QVBoxLayout(self.tab_manage)

        add_group = QGroupBox("Добавить новую запись")
        add_form = QFormLayout()
        self.add_context_input = QTextEdit()
        self.add_context_input.setPlaceholderText("Введите текст для обработки...")
        self.btn_add_manual = QPushButton("Добавить в корпус")
        add_form.addRow(self.add_context_input)
        add_form.addRow(self.btn_add_manual)
        add_group.setLayout(add_form)
        m_layout.addWidget(add_group)

        del_group = QGroupBox("Удаление записей")
        del_vbox = QVBoxLayout()

        self.btn_delete_all = QPushButton("Удалить все записи")
        self.btn_delete_all.setStyleSheet("background-color: #ffcccc;")
        del_vbox.addWidget(self.btn_delete_all)

        del_filter_layout = QHBoxLayout()
        self.del_input = QLineEdit()
        self.del_input.setPlaceholderText("Значение для удаления...")
        self.btn_del_word = QPushButton("По слову")
        self.btn_del_lemma = QPushButton("По лемме")
        self.btn_del_pos = QPushButton("По части речи")

        del_filter_layout.addWidget(self.del_input)
        del_filter_layout.addWidget(self.btn_del_word)
        del_filter_layout.addWidget(self.btn_del_lemma)
        del_filter_layout.addWidget(self.btn_del_pos)
        del_vbox.addLayout(del_filter_layout)

        del_group.setLayout(del_vbox)
        m_layout.addWidget(del_group)
        m_layout.addStretch()

        # Вкладка 4: Аналитика
        self.tab_stats = QWidget()
        st_layout = QVBoxLayout(self.tab_stats)

        self.label_total = QLabel("Всего токенов: —")
        self.label_unique = QLabel("Уникальных словоформ: —")
        st_layout.addWidget(self.label_total)
        st_layout.addWidget(self.label_unique)

        st_layout.addWidget(QLabel("<br><b>Частотные характеристики тегов:</b>"))
        self.tag_freq_table = QTableWidget()
        self.tag_freq_table.setColumnCount(2)
        self.tag_freq_table.setHorizontalHeaderLabels(["Тег", "Частота"])
        tag_header = self.tag_freq_table.horizontalHeader()
        tag_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        tag_header.resizeSection(0, 250)   # Тег
        tag_header.resizeSection(1, 120)   # Частота
        tag_header.setStretchLastSection(True)
        self.tag_freq_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        st_layout.addWidget(self.tag_freq_table)

        self.tabs.addTab(self.tab_corpus, "Корпус")
        self.tabs.addTab(self.tab_search, "Поиск")
        self.tabs.addTab(self.tab_manage, "Управление")
        self.tabs.addTab(self.tab_stats, "Аналитика")
        layout.addWidget(self.tabs)

    def create_highlighted_context(self, context, search_word):
        """Создает виджет с центрированным контекстом и постоянной подсветкой"""
        display = QTextEdit()
        display.setReadOnly(True)
        display.setMaximumHeight(60)
        display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        match = re.search(rf'\b{re.escape(search_word)}\b', context, re.IGNORECASE)

        if match:
            start, end = match.span()
            display.setText(context)
            display.setAlignment(Qt.AlignmentFlag.AlignCenter)

            palette = display.palette()
            palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, QColor("#3399FF"))
            palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, QColor("white"))
            palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor("#3399FF"))
            palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor("white"))
            display.setPalette(palette)

            def restore_selection():
                cursor = display.textCursor()
                if cursor.selectionStart() != start or cursor.selectionEnd() != end:
                    cursor.setPosition(start)
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        end - start
                    )
                    display.blockSignals(True)
                    display.setTextCursor(cursor)
                    display.blockSignals(False)

            restore_selection()
            display.selectionChanged.connect(restore_selection)
        else:
            display.setText(context)
            display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return display