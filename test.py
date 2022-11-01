import sys
from sys import argv
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow
from PyQt5.uic import loadUi

from ui.Main_Window import Ui_Dialog

class auto_dialog(Ui_Dialog):
    def __init__(self, dialog):
        super().__init__()
        self.setupUi(dialog)
        self.pushButton.clicked.connect(self.on_click)

    def _print(self):
        print("test")


if __name__ == '__main__':
    app = QApplication(argv)
    dialog = QDialog()
    auto = auto_dialog(dialog)
    dialog.show()
    app.exec()

