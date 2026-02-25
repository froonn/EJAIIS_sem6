# controller.py

import time
import json
from PyQt6.QtWidgets import QFileDialog, QApplication
from PyQt6.QtCore import QCoreApplication, QTimer
from handler import extract_text_from_pdf, process_text


class TextProcessorController:
    """The bridge between text processing logic and the user interface."""

    def __init__(self, view):
        self.view = view
        # Main data storage for the current project
        self.data = {'lexemes': {}, 'connections': {}}
        self.comments = {}

        # Connect UI signals to controller methods
        self.view.open_file_requested.connect(self.handle_open_pdf)
        self.view.save_data_requested.connect(self.save_to_file)
        self.view.load_data_requested.connect(self.load_from_file)
        self.view.filter_requested.connect(self.apply_filters)
        self.view.add_data_requested.connect(self.handle_add_entry)

    def handle_open_pdf(self):
        """Handle PDF selection, trigger analysis, and update the view."""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(None, "Select PDF", "", "PDF Files (*.pdf)")

        if file_path:
            # Update UI state immediately
            self.view.set_processing_state(True)

            # CRITICAL: Force the dialog to close and UI to refresh
            QApplication.processEvents()

            # Use a short delay to let the OS hide the file picker window
            QTimer.singleShot(100, lambda: self._start_processing(file_path))

    def _start_processing(self, file_path):
        """Heavy processing logic moved to a separate step to allow UI refresh."""
        try:
            QApplication.processEvents()
            start_time = time.time()

            text = extract_text_from_pdf(file_path)
            lexemes, connections = process_text(text)

            duration = round(time.time() - start_time, 4)
            word_count = len(text.split())

            self.data = {'lexemes': lexemes, 'connections': connections}
            self.comments = {}

            self.view.update_table(self.data)

            # This will now display the BOLD results info
            self.view.display_results_info(duration, word_count)

        except Exception as e:
            # Error message also in bold
            self.view.stats_label.setText(f"<b>Error: {str(e)}</b>")

        finally:
            # We removed the generic "Ready" update here so the timing info stays visible
            QApplication.processEvents()

    def handle_add_entry(self, entry_data):
        """Manually add a new lexeme or wordform to the database."""
        lex = entry_data['lexeme'].strip().lower()
        wf = entry_data['wordform'].strip().lower()

        if not lex or not wf:
            return

        # Update frequency counts and relationships
        self.data['lexemes'][lex] = self.data['lexemes'].get(lex, 0) + 1
        if lex not in self.data['connections']:
            self.data['connections'][lex] = {}
        self.data['connections'][lex][wf] = self.data['connections'][lex].get(wf, 0) + 1

        self.view.update_table(self.data, self.comments)

    def apply_filters(self, quick_search_query):
        """Apply complex filtering (Quick search + Advanced settings)."""
        search_q = quick_search_query.lower()
        adv = self.view.current_filters

        filtered_lexemes = {}
        filtered_conn = {}

        for lexeme, lex_count in self.data['lexemes'].items():
            # 1. Filter by Lexeme frequency and text
            if adv:
                if not (adv['lex_min'] <= lex_count <= adv['lex_max']):
                    continue
                if adv.get('lexeme') and adv['lexeme'].lower() not in lexeme:
                    continue

            # Filter associated wordforms
            wordforms = self.data['connections'].get(lexeme, {})
            matching_wfs = {}

            for wf, wf_count in wordforms.items():
                # 2. Check Advanced Filter conditions for wordforms
                if adv:
                    if not (adv['wf_min'] <= wf_count <= adv['wf_max']):
                        continue
                    if adv.get('wordform') and adv['wordform'].lower() not in wf:
                        continue

                # 3. Check Quick Search (substring match)
                if search_q and (search_q not in lexeme and search_q not in wf):
                    continue

                matching_wfs[wf] = wf_count

            if matching_wfs:
                filtered_lexemes[lexeme] = lex_count
                filtered_conn[lexeme] = matching_wfs

        # Refresh table with filtered results
        self.view.update_table({
            'lexemes': filtered_lexemes,
            'connections': filtered_conn,
        }, self.comments)

    def save_to_file(self):
        """Save the current project state to a JSON file."""
        self._sync_comments_from_view()
        path, _ = QFileDialog.getSaveFileName(None, "Save Project", "", "JSON Files (*.json)")
        if path:
            if not path.lower().endswith('.json'):
                path += '.json'
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'data': self.data, 'comments': self.comments}, f, ensure_ascii=False, indent=4)

    def load_from_file(self):
        """Load project data from a previously saved JSON file."""
        path, _ = QFileDialog.getOpenFileName(None, "Load Project", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                    self.data = payload.get('data', {})
                    self.comments = payload.get('comments', {})
                    # English and Bold
                    self.view.stats_label.setText("<b>Project Loaded Successfully</b>")
                    self.view.update_table(self.data, self.comments)
            except Exception as e:
                self.view.stats_label.setText(f"<b>Load Error: {str(e)}</b>")

    def _sync_comments_from_view(self):
        """Synchronize comments from the table widget back into the controller."""
        for row in range(self.view.table.rowCount()):
            # Column 3 is Lexeme
            lexeme_item = self.view.table.item(row, 3)
            # Column 0 is Wordform
            wf_item = self.view.table.item(row, 0)
            # Column 5 is Comment
            comment_item = self.view.table.item(row, 5)

            if lexeme_item:
                lex_text = lexeme_item.text()
                self.comments[lex_text] = comment_item.text() if comment_item else ""
