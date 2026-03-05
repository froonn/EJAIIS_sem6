# --- VIEW ---

import re

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel,
    QTabWidget, QTableWidget, QHeaderView,
    QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor

class CorpusView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Корпусный менеджер (MVC + SQLite)")
        self.resize(1100, 850)
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
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите слово или лемму...")
        self.btn_search = QPushButton("Найти")
        search_box.addWidget(self.search_input)
        search_box.addWidget(self.btn_search)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Слово", "Лемма", "Часть речи", "Контекст (Центрирование)"])
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        s_layout.addLayout(search_box)
        s_layout.addWidget(self.results_table)

        # Вкладка 3: Управление
        self.tab_manage = QWidget()
        m_layout = QVBoxLayout(self.tab_manage)

        # Группа добавления
        add_group = QGroupBox("Добавить новую запись")
        add_form = QFormLayout()
        self.add_context_input = QTextEdit()
        self.add_context_input.setPlaceholderText("Введите текст для обработки...")
        self.add_context_input.setMaximumHeight(80)
        self.btn_add_manual = QPushButton("Добавить в корпус")
        add_form.addRow("Текст предложения:", self.add_context_input)
        add_form.addRow(self.btn_add_manual)
        add_group.setLayout(add_form)
        m_layout.addWidget(add_group)

        # Группа удаления
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
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        st_layout.addWidget(self.stats_display)

        self.tabs.addTab(self.tab_corpus, "Корпус")
        self.tabs.addTab(self.tab_search, "Поиск")
        self.tabs.addTab(self.tab_manage, "Управление")
        self.tabs.addTab(self.tab_stats, "Аналитика")
        layout.addWidget(self.tabs)

    def create_highlighted_context(self, context, search_word):
        """Создает виджет с центрированным контекстом и постоянной синей подсветкой"""
        display = QTextEdit()
        display.setReadOnly(True)
        display.setMaximumHeight(60)
        display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        match = re.search(rf'\b{re.escape(search_word)}\b', context, re.IGNORECASE)

        if match:
            start, end = match.span()
            display.setText(context)
            cursor = display.textCursor()

            fmt = QTextCharFormat()
            fmt.setBackground(QColor("blue"))
            fmt.setForeground(QColor("white"))

            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, end - start)
            cursor.setCharFormat(fmt)

            display.setTextCursor(cursor)
            display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            display.setText(context)
            display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return display