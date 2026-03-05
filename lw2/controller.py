# --- CONTROLLER ---

import os

from PyQt6.QtWidgets import (
    QFileDialog, QTableWidgetItem, QMessageBox,
)
from PyQt6.QtTest import QTest

class CorpusController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self._connect_signals()
        self.update_stats_view()

    def _connect_signals(self):
        self.view.btn_load.clicked.connect(self.handle_load)
        self.view.btn_search.clicked.connect(self.handle_search)
        self.view.search_input.returnPressed.connect(self.handle_search)
        self.view.btn_add_manual.clicked.connect(self.handle_manual_add)
        self.view.btn_delete_all.clicked.connect(self.handle_delete_all)
        self.view.btn_del_word.clicked.connect(lambda: self.handle_delete_by_filter("word"))
        self.view.btn_del_lemma.clicked.connect(lambda: self.handle_delete_by_filter("lemma"))
        self.view.btn_del_pos.clicked.connect(lambda: self.handle_delete_by_filter("pos"))

    def handle_load(self):
        file_filter = "All Supported (*.txt *.pdf *.docx *.doc *.rtf);;Text (*.txt);;PDF (*.pdf);;Word (*.docx *.doc);;RTF (*.rtf)"
        files, _ = QFileDialog.getOpenFileNames(self.view, "Выбор файлов", "", file_filter)

        if not files:
            return

        QTest.qWait(100)  # Задержка 0.1 сек

        full_preview = ""
        for f_path in files:
            try:
                text = self.model.extract_text(f_path)
                if text:
                    self.model.add_to_corpus(text)
                    full_preview += f"--- {os.path.basename(f_path)} ---\n{text[:300]}...\n\n"
            except Exception as e:
                QMessageBox.warning(self.view, "Ошибка", f"Файл {f_path} не обработан: {e}")

        self.view.text_preview.setText(full_preview)
        self.update_stats_view()
        QMessageBox.information(self.view, "Готово", "Данные сохранены в базу.")

    def handle_search(self):
        query = self.view.search_input.text().strip()
        if not query:
            return

        results = self.model.search(query)
        self.view.results_table.setRowCount(0)

        for row, item in enumerate(results):
            self.view.results_table.insertRow(row)
            self.view.results_table.setItem(row, 0, QTableWidgetItem(item['word']))
            self.view.results_table.setItem(row, 1, QTableWidgetItem(item['lemma']))
            self.view.results_table.setItem(row, 2, QTableWidgetItem(item['pos']))

            highlighted_widget = self.view.create_highlighted_context(item['context'], item['word'])
            self.view.results_table.setCellWidget(row, 3, highlighted_widget)
            self.view.results_table.setRowHeight(row, 65)

    def handle_manual_add(self):
        context = self.view.add_context_input.toPlainText().strip()
        if not context:
            QMessageBox.warning(self.view, "Внимание", "Введите текст предложения.")
            return

        self.model.add_to_corpus(context)
        self.update_stats_view()
        self.view.add_context_input.clear()
        QMessageBox.information(self.view, "Успех", "Запись добавлена в базу данных.")

    def handle_delete_all(self):
        confirm = QMessageBox.question(self.view, "Подтверждение", "Удалить ВСЕ записи из базы данных?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.model.delete_all()
            self.update_stats_view()
            self.view.results_table.setRowCount(0)
            self.view.text_preview.clear()
            QMessageBox.information(self.view, "Удалено", "База данных полностью очищена.")

    def handle_delete_by_filter(self, filter_type):
        val = self.view.del_input.text().strip()
        if not val:
            QMessageBox.warning(self.view, "Ошибка", "Введите значение для удаления.")
            return

        if filter_type == "word":
            self.model.delete_by_word(val)
        elif filter_type == "lemma":
            self.model.delete_by_lemma(val)
        elif filter_type == "pos":
            self.model.delete_by_pos(val)

        self.update_stats_view()
        self.view.results_table.setRowCount(0)
        QMessageBox.information(self.view, "Успех", "Операция удаления завершена.")
        self.view.del_input.clear()

    def update_stats_view(self):
        stats = self.model.get_stats()
        if not stats:
            self.view.stats_display.setText("База данных пуста.")
            return

        text = f"Общая статистика (БД):\nВсего токенов: {stats['total']}\nУникальных лемм: {stats['unique']}\n\n"
        text += "Части речи:\n"
        for pos, count in stats['pos'].most_common():
            text += f"- {pos}: {count}\n"
        self.view.stats_display.setText(text)