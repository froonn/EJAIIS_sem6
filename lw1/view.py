# view.py

import sys
from PyQt6.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                             QWidget, QTableWidget, QTableWidgetItem,
                             QLabel, QHeaderView, QMessageBox, QLineEdit,
                             QDialog, QFormLayout, QFrame, QSpinBox, QComboBox)
from PyQt6.QtCore import pyqtSignal, Qt


class AddEntryDialog(QDialog):
    """Dialog window for manual data entry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Entry")
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)
        self.lexeme_input = QLineEdit()
        self.wordform_input = QLineEdit()

        layout.addRow("Lexeme:", self.lexeme_input)
        layout.addRow("Wordform:", self.wordform_input)

        buttons = QHBoxLayout()
        self.btn_ok = QPushButton("Add")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(self.btn_ok)
        buttons.addWidget(self.btn_cancel)
        layout.addRow(buttons)

    def get_data(self):
        """Return the user-entered data."""
        return {
            "lexeme": self.lexeme_input.text(),
            "wordform": self.wordform_input.text(),
        }


class FilterDialog(QDialog):
    """Window for advanced data filtering settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Filters")
        self.setFixedWidth(450)
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)
        self.f_wordform = QLineEdit()
        self.f_lexeme = QLineEdit()

        # Wordform frequency range setup
        wf_freq_layout = QHBoxLayout()
        self.f_wf_min = QSpinBox()
        self.f_wf_min.setRange(0, 100000)
        self.f_wf_max = QSpinBox()
        self.f_wf_max.setRange(0, 100000)
        self.f_wf_max.setValue(100000)
        wf_freq_layout.addWidget(QLabel("Min:"))
        wf_freq_layout.addWidget(self.f_wf_min)
        wf_freq_layout.addWidget(QLabel("Max:"))
        wf_freq_layout.addWidget(self.f_wf_max)

        # Lexeme frequency range setup
        lex_freq_layout = QHBoxLayout()
        self.f_lex_min = QSpinBox()
        self.f_lex_min.setRange(0, 100000)
        self.f_lex_max = QSpinBox()
        self.f_lex_max.setRange(0, 100000)
        self.f_lex_max.setValue(100000)
        lex_freq_layout.addWidget(QLabel("Min:"))
        lex_freq_layout.addWidget(self.f_lex_min)
        lex_freq_layout.addWidget(QLabel("Max:"))
        lex_freq_layout.addWidget(self.f_lex_max)

        layout.addRow("Wordform contains:", self.f_wordform)
        layout.addRow("Lexeme contains:", self.f_lexeme)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addRow(line)

        layout.addRow("Wordform Freq:", wf_freq_layout)
        layout.addRow("Lexeme Freq:", lex_freq_layout)

        self.btn_apply = QPushButton("Apply Filters")
        self.btn_apply.clicked.connect(self.accept)
        layout.addRow(self.btn_apply)

    def get_filters(self):
        """Return the dictionary of set filters."""
        return {
            "wordform": self.f_wordform.text().strip(),
            "lexeme": self.f_lexeme.text().strip(),
            "wf_min": self.f_wf_min.value(),
            "wf_max": self.f_wf_max.value(),
            "lex_min": self.f_lex_min.value(),
            "lex_max": self.f_lex_max.value()
        }


class MainWindow(QMainWindow):
    """Main application window: table and core controls."""

    # Signals to notify the controller of user actions
    open_file_requested = pyqtSignal()
    save_data_requested = pyqtSignal()
    load_data_requested = pyqtSignal()
    add_data_requested = pyqtSignal(dict)
    filter_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Processor 5000 Pro Max Ultra Super")
        self.resize(1200, 800)
        self.current_filters = {}
        self._init_ui()

    def _init_ui(self):
        """Initialize layout and widgets of the main window."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top Bar: status, help, and filter button
        top_bar = QHBoxLayout()
        self.stats_label = QLabel("<b>Waiting for file...</b>")

        # Action buttons on the right side of the bar
        self.btn_help = QPushButton("Help")
        self.btn_help.clicked.connect(self._show_help)

        self.btn_filter_show = QPushButton("Open Filters")
        self.btn_filter_show.clicked.connect(self._show_filter_dialog)

        top_bar.addWidget(self.stats_label)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_help)
        top_bar.addWidget(self.btn_filter_show)
        main_layout.addLayout(top_bar)

        # Results table configuration
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Wordform", "WF Freq", "Lexeme", "Lex Freq", "Comment"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)

        # Bottom Bar: functional buttons
        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("Open PDF")
        self.btn_open.clicked.connect(self.open_file_requested.emit)
        self.btn_save = QPushButton("Save Results")
        self.btn_save.clicked.connect(self.save_data_requested.emit)
        self.btn_load = QPushButton("Load Project")
        self.btn_load.clicked.connect(self.load_data_requested.emit)
        self.btn_new = QPushButton("Add Entry")
        self.btn_new.clicked.connect(self._handle_add_entry)

        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_new)
        main_layout.addLayout(btn_layout)

    def _show_help(self):
        """Display step-by-step user guide."""
        guide_text = (
            "<b>User Guide: How to use Text Processor Pro</b><br><br>"
            "<b>1. Analyze a Document:</b><br>"
            "Click <b>'Open PDF'</b> to select a file. The system will extract text, "
            "identify lemmas (dictionary forms), and count frequencies automatically.<br><br>"
            "<b>2. Manage Data:</b><br>"
            "• <b>Comments:</b> Type directly into the 'Comment' column to add notes.<br>"
            "• <b>Add Entry:</b> Use 'Add Entry' to manually insert words not found in the PDF.<br><br>"
            "<b>3. Filtering:</b><br>"
            "Click <b>'Open Filters'</b> to narrow down results by frequency (e.g., only show "
            "words appearing more than 10 times) or by wordform.<br><br>"
            "<b>4. Saving Progress:</b><br>"
            "Click <b>'Save Results'</b> to export your work to a .json file. "
            "Use <b>'Load Project'</b> later to continue where you left off."
        )

        msg = QMessageBox(self)
        msg.setWindowTitle("Instructions")
        msg.setText(guide_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def _show_filter_dialog(self):
        """Open filter dialog and notify controller upon application."""
        dialog = FilterDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_filters = dialog.get_filters()
            # Send empty string as we removed the search input widget
            self.filter_requested.emit("")

    def _handle_add_entry(self):
        """Open manual entry dialog and pass data to controller."""
        dialog = AddEntryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.add_data_requested.emit(dialog.get_data())

    def set_processing_state(self, is_processing: bool):
        """Visual notification of file processing state."""

        self.stats_label.setText("<b>PROCESSING...</b>" if is_processing else "Ready")

    def display_results_info(self, duration, word_count):
        """Display info about processing duration and word count in bold."""
        self.stats_label.setText(
            f"<b>Processing Time: {duration}s | Word Count: {word_count}</b>"
        )

    def update_table(self, data, comments=None):
        """Complete redraw of the table based on provided data."""
        self.table.setRowCount(0)
        comments = comments or {}
        lexemes = data.get('lexemes', {})
        connections = data.get('connections', {})

        row = 0

        # Iterate lexemes and their connections to fill table rows
        for lemma in sorted(lexemes.keys()):
            lex_freq = lexemes[lemma]
            wfs = connections.get(lemma, {})
            for wf, wf_freq in sorted(wfs.items()):
                self.table.insertRow(row)

                # 0: Wordform (Static)
                self.table.setItem(row, 0, QTableWidgetItem(wf))

                # 1: WF Freq (Static)
                self.table.setItem(row, 1, QTableWidgetItem(str(wf_freq)))

                # 2: Lexeme (Static)
                self.table.setItem(row, 2, QTableWidgetItem(lemma))

                # 3: Lex Freq (Static)
                self.table.setItem(row, 3, QTableWidgetItem(str(lex_freq)))

                # 4: Comment (Editable)
                self.table.setItem(row, 4, QTableWidgetItem(comments.get(lemma, "")))

                row += 1
