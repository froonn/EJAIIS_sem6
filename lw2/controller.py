# --- CONTROLLER ---

import json
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
        self.view.tag_input.returnPressed.connect(self.handle_search)
        self.view.btn_add_manual.clicked.connect(self.handle_manual_add)
        self.view.btn_delete_all.clicked.connect(self.handle_delete_all)
        self.view.btn_del_word.clicked.connect(lambda: self.handle_delete_by_filter("word"))
        self.view.btn_del_lemma.clicked.connect(lambda: self.handle_delete_by_filter("lemma"))
        self.view.btn_del_pos.clicked.connect(lambda: self.handle_delete_by_filter("pos"))
        self.view.btn_export_json.clicked.connect(self.handle_export_json)
        self.view.btn_import_json.clicked.connect(self.handle_import_json)

    def handle_load(self):
        file_filter = "All Supported (*.txt *.pdf *.docx *.doc *.rtf);;Text (*.txt);;PDF (*.pdf);;Word (*.docx *.doc);;RTF (*.rtf)"
        files, _ = QFileDialog.getOpenFileNames(self.view, "Выбор файлов", "", file_filter)

        if not files:
            return

        QTest.qWait(100)

        for f_path in files:
            try:
                text = self.model.extract_text(f_path)
                if text:
                    self.model.add_to_corpus(text, f_path)
            except Exception as e:
                QMessageBox.warning(self.view, "Ошибка", f"Файл {f_path} не обработан: {e}")

        self.update_stats_view()
        QMessageBox.information(self.view, "Готово", "Данные сохранены в базу.")

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

    def handle_export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self.view, "Экспорт в JSON", "corpus_export.json", "JSON (*.json)"
        )
        if not path:
            return
        try:
            data = self.model.export_json()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self.view, "Экспорт", f"Экспортировано {len(data)} записей в\n{path}")
        except Exception as e:
            QMessageBox.critical(self.view, "Ошибка экспорта", str(e))

    def handle_import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self.view, "Импорт из JSON", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                QMessageBox.warning(self.view, "Ошибка", "Файл должен содержать список записей (JSON array).")
                return
            self.model.import_json(data)
            self.update_stats_view()
            QMessageBox.information(self.view, "Импорт", f"Импортировано {len(data)} записей из\n{path}")
        except json.JSONDecodeError as e:
            QMessageBox.critical(self.view, "Ошибка JSON", str(e))
        except Exception as e:
            QMessageBox.critical(self.view, "Ошибка импорта", str(e))

    def handle_search(self):
        query = self.view.search_input.text().strip() or None
        tag_filter = self.view.tag_input.text().strip() or None

        if not query and not tag_filter:
            return

        results = self.model.search(query=query, tag_filter=tag_filter)
        self.view.results_table.setRowCount(0)

        for row, item in enumerate(results):
            self.view.results_table.insertRow(row)
            self.view.results_table.setItem(row, 0, QTableWidgetItem(item.get('word', '')))
            self.view.results_table.setItem(row, 1, QTableWidgetItem(item.get('lemma', '')))
            self.view.results_table.setItem(row, 2, QTableWidgetItem(item.get('tags', '')))
            self.view.results_table.setItem(row, 3, QTableWidgetItem(str(item.get('word_freq', ''))))
            self.view.results_table.setItem(row, 4, QTableWidgetItem(str(item.get('lemma_freq', ''))))

            word_for_highlight = item.get('word', '') if query else ''
            highlighted_widget = self.view.create_highlighted_context(
                item.get('context', ''), word_for_highlight
            )
            self.view.results_table.setCellWidget(row, 5, highlighted_widget)
            self.view.results_table.setItem(row, 6, QTableWidgetItem(item.get('source', '')))
            self.view.results_table.setRowHeight(row, 65)

    def update_stats_view(self):
        stats = self.model.get_stats()
        if not stats:
            self.view.label_total.setText("Всего токенов: 0")
            self.view.label_unique.setText("Уникальных словоформ: 0")
            self.view.tag_freq_table.setRowCount(0)
            return

        self.view.label_total.setText(f"Всего токенов: {stats['total']}")
        self.view.label_unique.setText(f"Уникальных словоформ: {stats['unique']}")

        tag_freq = stats.get('tag_freq', [])
        self.view.tag_freq_table.setRowCount(0)
        for row_idx, (tag, freq) in enumerate(tag_freq):
            self.view.tag_freq_table.insertRow(row_idx)
            self.view.tag_freq_table.setItem(row_idx, 0, QTableWidgetItem(tag))
            self.view.tag_freq_table.setItem(row_idx, 1, QTableWidgetItem(str(freq)))
