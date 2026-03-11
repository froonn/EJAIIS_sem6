import sys

from controller import CorpusController
from model import CorpusModel
from view import CorpusView

from PyQt6.QtWidgets import (
    QApplication,
)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = CorpusModel()
    view = CorpusView()
    controller = CorpusController(model, view)

    view.show()
    sys.exit(app.exec())
