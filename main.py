# -*- coding: utf-8 -*-
import os
import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QIcon

from core.pf_connector import PowerFactoryConnector
from gui.main_window import MainWindow

def apply_dark_theme(app: QApplication):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(26, 32, 44))
    palette.setColor(QPalette.WindowText, QColor(247, 250, 252))
    palette.setColor(QPalette.Base, QColor(45, 55, 72))
    palette.setColor(QPalette.AlternateBase, QColor(26, 32, 44))
    palette.setColor(QPalette.ToolTipBase, QColor(30, 41, 59))
    palette.setColor(QPalette.ToolTipText, QColor(248, 250, 252))
    palette.setColor(QPalette.Text, QColor(247, 250, 252))
    palette.setColor(QPalette.Button, QColor(45, 55, 72))
    palette.setColor(QPalette.ButtonText, QColor(247, 250, 252))
    palette.setColor(QPalette.Highlight, QColor(49, 130, 206))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

def main():
    # Ensure Windows taskbar displays the custom GIAT icon instead of the default Python icon
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ugm.pln.giat.app.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    apply_dark_theme(app)

    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    ico_path = os.path.join(assets_dir, "giat_icon.ico")
    png_path = os.path.join(assets_dir, "giat_icon.png")
    if os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))
    elif os.path.exists(png_path):
        app.setWindowIcon(QIcon(png_path))

    connector = PowerFactoryConnector()
    window = MainWindow(connector)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
