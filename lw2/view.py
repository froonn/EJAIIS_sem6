# --- VIEW ---

import re

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel,
    QTabWidget, QTableWidget, QHeaderView,
    QFormLayout, QGroupBox, QScrollArea
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

        # Вкладка 1: Управление
        self.tab_manage = QWidget()
        m_layout = QVBoxLayout(self.tab_manage)

        load_group = QGroupBox("Загрузка документов")
        load_layout = QVBoxLayout()
        self.btn_load = QPushButton("Загрузить документы (TXT, PDF, DOCX, RTF, DOC)")
        self.btn_load.setFixedHeight(40)
        load_layout.addWidget(self.btn_load)
        load_group.setLayout(load_layout)
        m_layout.addWidget(load_group)

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

        io_group = QGroupBox("Импорт / Экспорт данных (JSON)")
        io_layout = QHBoxLayout()
        self.btn_export_json = QPushButton("Экспортировать в JSON")
        self.btn_import_json = QPushButton("Импортировать из JSON")
        self.btn_export_json.setFixedHeight(35)
        self.btn_import_json.setFixedHeight(35)
        io_layout.addWidget(self.btn_export_json)
        io_layout.addWidget(self.btn_import_json)
        io_group.setLayout(io_layout)
        m_layout.addWidget(io_group)

        m_layout.addStretch()

        # Вкладка 2: Поиск
        self.tab_search = QWidget()
        s_layout = QVBoxLayout(self.tab_search)

        search_form = QFormLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите слово или лемму...")
        search_form.addRow("Слово / лемма:", self.search_input)
        s_layout.addLayout(search_form)

        tag_box = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Например: NOUN, VERB, plur, sing, accs, ...")
        self.btn_search = QPushButton("Найти")
        self.btn_search.setFixedHeight(35)
        tag_box.addWidget(QLabel("Фильтр по тегу:"))
        tag_box.addWidget(self.tag_input)
        tag_box.addWidget(self.btn_search)
        s_layout.addLayout(tag_box)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(
            ["Слово", "Лемма", "Теги", "Частота слова", "Частота леммы", "Контекст", "Источник"]
        )
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setDefaultSectionSize(120)
        header.resizeSection(0, 100)
        header.resizeSection(1, 100)
        header.resizeSection(2, 180)
        header.resizeSection(3, 110)
        header.resizeSection(4, 110)
        header.resizeSection(5, 350)
        header.resizeSection(6, 150)
        header.setStretchLastSection(False)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setWordWrap(True)
        s_layout.addWidget(self.results_table)

        # Вкладка 3: Аналитика
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
        tag_header.resizeSection(0, 250)
        tag_header.resizeSection(1, 120)
        tag_header.setStretchLastSection(True)
        self.tag_freq_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        st_layout.addWidget(self.tag_freq_table)

        # Вкладка 4: Справка
        self.tab_help = QWidget()
        h_layout = QVBoxLayout(self.tab_help)

        help_scroll = QScrollArea()
        help_scroll.setWidgetResizable(True)
        help_content = QWidget()
        help_content_layout = QVBoxLayout(help_content)
        help_content_layout.setSpacing(10)
        help_content_layout.setContentsMargins(20, 20, 20, 20)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setFrameShape(QTextEdit.Shape.NoFrame)
        help_text.setHtml("""
        <h2>Корпусный менеджер — Справка</h2>

        <h3>&#128196; Вкладка «Управление»</h3>
        <p><b>Загрузка документов</b><br>
        Нажмите кнопку <i>«Загрузить документы»</i> для выбора одного или нескольких файлов.<br>
        Поддерживаемые форматы: <b>TXT, PDF, DOCX, DOC, RTF</b>.<br>
        После загрузки текст автоматически разбивается на предложения,
        каждое слово лингвистически размечается (словоформа, лемма, часть речи, теги)
        и сохраняется в базу данных.</p>

        <p><b>Добавление записи вручную</b><br>
        Введите произвольный текст в поле и нажмите <i>«Добавить в корпус»</i>.
        Текст будет обработан так же, как и загруженный файл.</p>

        <p><b>Удаление записей</b>
        <ul>
            <li><i>«Удалить все записи»</i> — полная очистка базы данных.</li>
            <li>Введите значение в поле и выберите тип удаления:
                <b>По слову</b> (точное совпадение словоформы),
                <b>По лемме</b> или <b>По части речи</b> (например: NOUN, VERB).</li>
        </ul></p>

        <p><b>Импорт / Экспорт (JSON)</b>
        <ul>
            <li><i>«Экспортировать в JSON»</i> — сохраняет все токены корпуса в файл JSON
            (каждый токен содержит: слово, лемму, теги, предложение, источник, позицию).</li>
            <li><i>«Импортировать из JSON»</i> — загружает ранее экспортированный файл
            и добавляет записи в текущую базу (существующие данные не удаляются).</li>
        </ul></p>

        <h3>&#128269; Вкладка «Поиск»</h3>
        <p>Позволяет искать токены в корпусе по двум параметрам (можно комбинировать):</p>
        <ul>
            <li><b>Слово / лемма</b> — введите словоформу или лемму для точного поиска
            (регистр не учитывается).</li>
            <li><b>Фильтр по тегу</b> — введите тег или его часть (например:
            <code>NOUN</code>, <code>plur</code>, <code>accs</code>).</li>
        </ul>
        <p>Результаты отображаются в таблице со столбцами:<br>
        <b>Слово, Лемма, Теги, Частота слова, Частота леммы, Контекст, Источник</b>.<br>
        Найденное слово подсвечивается в столбце «Контекст».<br>
        Ширину столбцов можно изменять перетаскиванием границ заголовков.</p>

        <h3>&#128202; Вкладка «Аналитика»</h3>
        <p>Отображает общую статистику по корпусу:</p>
        <ul>
            <li><b>Всего токенов</b> — общее количество слов в корпусе.</li>
            <li><b>Уникальных словоформ</b> — количество различных словоформ.</li>
            <li><b>Частотные характеристики тегов</b> — таблица со всеми тегами
            и количеством их вхождений, отсортированная по убыванию частоты.</li>
        </ul>

        <h3>&#128221; Теги pymorphy2 (краткий справочник)</h3>
        <table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;">
            <tr><th>Тег</th><th>Значение</th></tr>
            <tr><td>NOUN</td><td>имя существительное</td></tr>
            <tr><td>ADJF</td><td>имя прилагательное (полное)</td></tr>
            <tr><td>ADJS</td><td>имя прилагательное (краткое)</td></tr>
            <tr><td>VERB</td><td>глагол (личная форма)</td></tr>
            <tr><td>INFN</td><td>глагол (инфинитив)</td></tr>
            <tr><td>PRTF</td><td>причастие (полное)</td></tr>
            <tr><td>PRTS</td><td>причастие (краткое)</td></tr>
            <tr><td>GRND</td><td>деепричастие</td></tr>
            <tr><td>NUMR</td><td>числительное</td></tr>
            <tr><td>ADVB</td><td>наречие</td></tr>
            <tr><td>NPRO</td><td>местоимение-существительное</td></tr>
            <tr><td>PREP</td><td>предлог</td></tr>
            <tr><td>CONJ</td><td>союз</td></tr>
            <tr><td>PRCL</td><td>частица</td></tr>
            <tr><td>INTJ</td><td>междометие</td></tr>
            <tr><td>nomn</td><td>именительный падеж</td></tr>
            <tr><td>gent</td><td>родительный падеж</td></tr>
            <tr><td>datv</td><td>дательный падеж</td></tr>
            <tr><td>accs</td><td>винительный падеж</td></tr>
            <tr><td>ablt</td><td>творительный падеж</td></tr>
            <tr><td>loct</td><td>предложный падеж</td></tr>
            <tr><td>sing</td><td>единственное число</td></tr>
            <tr><td>plur</td><td>множественное число</td></tr>
            <tr><td>masc</td><td>мужской род</td></tr>
            <tr><td>femn</td><td>женский род</td></tr>
            <tr><td>neut</td><td>средний род</td></tr>
        </table>
        """)

        help_content_layout.addWidget(help_text)
        help_scroll.setWidget(help_content)
        h_layout.addWidget(help_scroll)

        self.tabs.addTab(self.tab_manage, "Управление")
        self.tabs.addTab(self.tab_search, "Поиск")
        self.tabs.addTab(self.tab_stats, "Аналитика")
        self.tabs.addTab(self.tab_help, "Справка")
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
