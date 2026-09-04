# -*- coding: utf-8 -*-
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from core.pf_connector import PowerFactoryConnector
from gui.main_window import MainWindow

def apply_dark_theme(app: QApplication):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(26, 32, 44))
    palette.setColor(QPalette.WindowText, QColor(247, 250, 252))
    palette.setColor(QPalette.Base, QColor(45, 55, 72))
    palette.setColor(QPalette.AlternateBase, QColor(26, 32, 44))
    palette.setColor(QPalette.ToolTipBase, QColor(247, 250, 252))
    palette.setColor(QPalette.ToolTipText, QColor(247, 250, 252))
    palette.setColor(QPalette.Text, QColor(247, 250, 252))
    palette.setColor(QPalette.Button, QColor(45, 55, 72))
    palette.setColor(QPalette.ButtonText, QColor(247, 250, 252))
    palette.setColor(QPalette.Highlight, QColor(49, 130, 206))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

def main():
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    connector = PowerFactoryConnector()
    window = MainWindow(connector)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
