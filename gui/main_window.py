# -*- coding: utf-8 -*-
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QFrame, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap

from gui.import_page import ImportPage
from gui.scenario_page import ScenarioPage
from gui.dashboard_page import DashboardPage
from gui.report_page import ReportPage
from gui.tutorial_page import TutorialPage

class MainWindow(QMainWindow):
    def __init__(self, connector):
        super().__init__()
        self.connector = connector
        self.is_dark = True
        self.setWindowTitle("Grid Impact Assessment Tool — UGM & PT. PLN Persero (ESDM No. 20/2020)")
        self.resize(1380, 900)

        self.setup_ui()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Frame
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(290)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 24, 20, 24)
        sidebar_layout.setSpacing(14)

        # Exact User-Uploaded UGM & PLN Logos Header Row
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(20)
        logo_layout.setAlignment(Qt.AlignCenter)

        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        ugm_path = os.path.join(assets_dir, "ugm_logo.png")
        pln_path = os.path.join(assets_dir, "pln_logo.png")

        lbl_ugm_logo = QLabel()
        lbl_ugm_logo.setStyleSheet("border: none; background: transparent;")
        if os.path.exists(ugm_path):
            pix_ugm = QPixmap(ugm_path).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_ugm_logo.setPixmap(pix_ugm)

        lbl_pln_logo = QLabel()
        lbl_pln_logo.setStyleSheet("border: none; background: transparent;")
        if os.path.exists(pln_path):
            pix_pln = QPixmap(pln_path).scaled(64, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_pln_logo.setPixmap(pix_pln)

        logo_layout.addWidget(lbl_ugm_logo)
        logo_layout.addWidget(lbl_pln_logo)
        sidebar_layout.addLayout(logo_layout)

        # Title & Description Labels
        self.lbl_title = QLabel("Grid Impact Assessment Tool")
        self.lbl_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)

        self.lbl_desc = QLabel("Collaboration between UGM and PT. PLN Persero")
        self.lbl_desc.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setWordWrap(True)

        sidebar_layout.addWidget(self.lbl_title)
        sidebar_layout.addWidget(self.lbl_desc)
        sidebar_layout.addSpacing(16)

        # Navigation Buttons
        self.btn_step1 = self.create_nav_btn("1. Project & PFD Setup")
        self.btn_step2 = self.create_nav_btn("2. Scenario Mapper")
        self.btn_step3 = self.create_nav_btn("3. Visual Dashboard")
        self.btn_step4 = self.create_nav_btn("4. Executive PDF Report")
        self.btn_tutorial = self.create_nav_btn("📖 User Manual & Guide")

        sidebar_layout.addWidget(self.btn_step1)
        sidebar_layout.addWidget(self.btn_step2)
        sidebar_layout.addWidget(self.btn_step3)
        sidebar_layout.addWidget(self.btn_step4)
        sidebar_layout.addWidget(self.btn_tutorial)

        sidebar_layout.addStretch()

        # Dark/Light Theme Toggle
        self.btn_theme = QPushButton("🌙 Dark Mode")
        self.btn_theme.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_theme.setCheckable(True)
        self.btn_theme.setChecked(True)
        self.btn_theme.clicked.connect(self.toggle_theme)
        sidebar_layout.addWidget(self.btn_theme)

        main_layout.addWidget(self.sidebar)

        # Main Pages Stack
        self.stacked_widget = QStackedWidget()
        self.import_page = ImportPage(self.connector)
        self.scenario_page = ScenarioPage(self.connector)
        self.dashboard_page = DashboardPage(self.connector)
        self.report_page = ReportPage(self.connector)
        self.tutorial_page = TutorialPage(self.connector)

        self.stacked_widget.addWidget(self.import_page)
        self.stacked_widget.addWidget(self.scenario_page)
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.report_page)
        self.stacked_widget.addWidget(self.tutorial_page)

        main_layout.addWidget(self.stacked_widget)

        # Connect Navigation
        self.btn_step1.clicked.connect(lambda: self.switch_page(0))
        self.btn_step2.clicked.connect(lambda: self.switch_page(1))
        self.btn_step3.clicked.connect(lambda: self.switch_page(2))
        self.btn_step4.clicked.connect(lambda: self.switch_page(3))
        self.btn_tutorial.clicked.connect(lambda: self.switch_page(4))

        self.switch_page(0)
        self.apply_styles()

    def create_nav_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setMinimumHeight(44)
        btn.setCheckable(True)
        return btn

    def switch_page(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        buttons = [self.btn_step1, self.btn_step2, self.btn_step3, self.btn_step4, self.btn_tutorial]
        for i, btn in enumerate(buttons):
            btn.setChecked(i == index)
            self.update_btn_style(btn, i == index)

        if index == 1:
            self.scenario_page.refresh_element_mapping()
        elif index == 2 and not self.dashboard_page.is_data_loaded:
            self.dashboard_page.load_analytics_data()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.btn_theme.setText("🌙 Dark Mode" if self.is_dark else "☀️ Light Mode")
        self.import_page.set_theme(self.is_dark)
        self.scenario_page.set_theme(self.is_dark)
        self.dashboard_page.set_theme(self.is_dark)
        self.report_page.set_theme(self.is_dark)
        self.tutorial_page.set_theme(self.is_dark)
        self.apply_styles()

    def update_btn_style(self, btn: QPushButton, is_active: bool):
        if self.is_dark:
            if is_active:
                btn.setStyleSheet("background-color: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; text-align: left; padding-left: 14px; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: transparent; color: #94A3B8; border: none; text-align: left; padding-left: 14px;")
        else:
            if is_active:
                btn.setStyleSheet("background-color: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; text-align: left; padding-left: 14px; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: transparent; color: #475569; border: none; text-align: left; padding-left: 14px;")

    def apply_styles(self):
        buttons = [self.btn_step1, self.btn_step2, self.btn_step3, self.btn_step4, self.btn_tutorial]
        for i, btn in enumerate(buttons):
            self.update_btn_style(btn, btn.isChecked())

        app = QApplication.instance()
        if self.is_dark:
            self.sidebar.setStyleSheet(
                "QFrame#sidebar { background-color: #0F172A; border-right: 1px solid #1E293B; }"
                "QLabel { border: none; background: transparent; }"
            )
            self.lbl_title.setStyleSheet("color: #F8FAFC; border: none; background: transparent;")
            self.lbl_desc.setStyleSheet("color: #38BDF8; border: none; background: transparent;")
            self.btn_theme.setStyleSheet("background-color: #1E293B; color: #F8FAFC; border: 1px solid #334155; border-radius: 6px; padding: 8px;")

            if app:
                app.setStyleSheet(
                    "QMessageBox { background-color: #1E293B; color: #F8FAFC; }"
                    "QMessageBox QLabel { color: #F8FAFC; font-size: 11px; font-weight: 500; }"
                    "QMessageBox QPushButton { background-color: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold; min-width: 80px; }"
                    "QMessageBox QPushButton:hover { background-color: #0369A1; }"
                )
        else:
            self.sidebar.setStyleSheet(
                "QFrame#sidebar { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }"
                "QLabel { border: none; background: transparent; }"
            )
            self.lbl_title.setStyleSheet("color: #0F172A; border: none; background: transparent;")
            self.lbl_desc.setStyleSheet("color: #0284C7; border: none; background: transparent;")
            self.btn_theme.setStyleSheet("background-color: #F1F5F9; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px;")

            if app:
                app.setStyleSheet(
                    "QMessageBox { background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; }"
                    "QMessageBox QLabel { color: #0F172A; font-size: 11px; font-weight: 500; }"
                    "QMessageBox QPushButton { background-color: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold; min-width: 80px; }"
                    "QMessageBox QPushButton:hover { background-color: #0369A1; }"
                )
