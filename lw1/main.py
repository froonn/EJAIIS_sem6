import prepare
from PyQt6.QtWidgets import QApplication
from view import MainWindow
from controller import TextProcessorController

if __name__ == "__main__":
    app = QApplication([])
    view = MainWindow()
    controller = TextProcessorController(view)
    view.show()
    app.exec()