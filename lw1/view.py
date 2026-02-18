import sys
from PyQt6.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                             QWidget, QTableWidget, QTableWidgetItem,
                             QLabel, QHeaderView, QMenuBar, QMessageBox, QLineEdit)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor


class MainWindow(QMainWindow):
    open_file_requested = pyqtSignal()
    save_data_requested = pyqtSignal()
    load_data_requested = pyqtSignal()
    filter_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Processor MVC")
        self.resize(1100, 700)
        self._init_ui()
        self._create_menu()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Панель статистики
        self.stats_label = QLabel("Ожидание файла...")
        self.stats_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.stats_label)

        # Поиск
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self.filter_requested.emit)
        search_layout.addWidget(QLabel("Фильтр:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Таблица (5 колонок согласно новому ТЗ)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Словоформа", "Частота СФ", "Лексема", "Частота лексемы", "Комментарий"
        ])

        # Настройка ширины: одинаковая по умолчанию (Stretch)
        header = self.table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        # Но при этом оставляем возможность менять вручную
        header.setCascadingSectionResizes(True)

        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("Открыть PDF")
        self.btn_open.clicked.connect(self.open_file_requested.emit)

        self.btn_load = QPushButton("Загрузить проект")
        self.btn_load.clicked.connect(self.load_data_requested.emit)

        self.btn_save = QPushButton("Сохранить результат")
        self.btn_save.clicked.connect(self.save_data_requested.emit)

        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def set_processing_state(self, is_processing: bool):
        """Индикация процесса обработки красным цветом"""
        if is_processing:
            self.stats_label.setText("ОБРАБОТКА ИДЕТ, ПОЖАЛУЙСТА ПОДОЖДИТЕ...")
            self.stats_label.setStyleSheet("color: red; font-weight: bold;")
            # Принудительно обновляем UI, чтобы надпись появилась до начала тяжелых вычислений
            self.stats_label.repaint()
        else:
            self.stats_label.setStyleSheet("color: black; font-weight: bold;")

    def _create_menu(self):
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("Справка")
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self.show_help)

    def show_help(self):
        QMessageBox.information(self, "Помощь", "Инструкция по использованию программы...")

    def update_table(self, data, comments=None):
        self.table.setRowCount(0)
        comments = comments or {}

        # Подготовка данных для сортировки
        # Нам нужно: Лексема (по алфавиту) -> Внутри лексемы Словоформы (по алфавиту)
        sorted_lexemes = sorted(data['lexemes'].keys())

        row_idx = 0
        for lexeme in sorted_lexemes:
            lex_freq = data['lexemes'][lexeme]
            # Получаем словоформы для этой лексемы и сортируем их
            word_forms = data['connections'].get(lexeme, {})
            sorted_wf = sorted(word_forms.items())  # Сортировка по ключу (словоформе)

            for wf, wf_freq in sorted_wf:
                self.table.insertRow(row_idx)

                # Заполнение колонок
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(wf)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(wf_freq)))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(lexeme)))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(lex_freq)))

                comment_text = comments.get(lexeme, "")
                self.table.setItem(row_idx, 4, QTableWidgetItem(comment_text))
                row_idx += 1