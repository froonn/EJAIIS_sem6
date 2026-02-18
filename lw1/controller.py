import time
import json
from PyQt6.QtWidgets import QFileDialog, QApplication
# Импорт функций модели
from handler import extract_text_from_pdf, process_text


class TextProcessorController:
    def __init__(self, view):
        self.view = view
        self.data = {'lexemes': {}, 'connections': {}}
        self.comments = {}

        self.view.open_file_requested.connect(self.handle_open_pdf)
        self.view.save_data_requested.connect(self.save_to_file)
        self.view.load_data_requested.connect(self.load_from_file)
        self.view.filter_requested.connect(self.apply_filter)

    def handle_open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Выберите PDF", "", "PDF Files (*.pdf)")
        if file_path:
            # 1. Сначала уведомляем UI о начале обработки
            self.view.set_processing_state(True)
            # 2. Форсируем закрытие диалогового окна и отрисовку красного текста
            QApplication.processEvents()

            start_time = time.time()

            # Логика обработки
            text = extract_text_from_pdf(file_path)
            lexemes, connections = process_text(text)

            duration = round(time.time() - start_time, 4)
            word_count = len(text.split())

            self.data = {'lexemes': lexemes, 'connections': connections}
            self.comments = {}

            # 3. Возвращаем обычный цвет и выводим статистику
            self.view.set_processing_state(False)
            self.view.stats_label.setText(f"Время обработки: {duration}с | Слов: {word_count}")
            self.view.update_table(self.data)

    def apply_filter(self, query):
        if not query:
            self.view.update_table(self.data, self.comments)
            return

        # Фильтруем данные (поиск по лексеме или словоформе)
        filtered_lexemes = {}
        filtered_conn = {}

        query = query.lower()
        for lexeme, count in self.data['lexemes'].items():
            # Если запрос в лексеме или в любой из её словоформ
            wf_match = any(query in wf.lower() for wf in self.data['connections'].get(lexeme, {}))
            if query in lexeme.lower() or wf_match:
                filtered_lexemes[lexeme] = count
                filtered_conn[lexeme] = self.data['connections'].get(lexeme, {})

        self.view.update_table({'lexemes': filtered_lexemes, 'connections': filtered_conn}, self.comments)

    def save_to_file(self):
        # Сбор комментариев (с учетом того, что лексема может дублироваться в строках)
        for row in range(self.view.table.rowCount()):
            lexeme_item = self.view.table.item(row, 2)
            comment_item = self.view.table.item(row, 4)
            if lexeme_item:
                self.comments[lexeme_item.text()] = comment_item.text() if comment_item else ""

        path, _ = QFileDialog.getSaveFileName(None, "Сохранить проект", "", "JSON Files (*.json)")
        if path:
            if not path.lower().endswith('.json'):
                path += '.json'
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'data': self.data, 'comments': self.comments}, f, ensure_ascii=False, indent=4)

    def load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(None, "Загрузить проект", "", "JSON Files (*.json)")
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
                self.data = payload.get('data', {})
                self.comments = payload.get('comments', {})
                self.view.stats_label.setText("Проект загружен")
                self.view.update_table(self.data, self.comments)