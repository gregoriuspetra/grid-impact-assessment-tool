# -*- coding: utf-8 -*-
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QFrame, QSizePolicy, QApplication, QToolTip)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

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
        self.is_sidebar_collapsed = False
        self.setWindowTitle("GIAT — Grid Impact Assessment Tool (UGM & PT. PLN Persero)")
        self.resize(1380, 900)

        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        ico_path = os.path.join(assets_dir, "giat_icon.ico")
        png_path = os.path.join(assets_dir, "giat_icon.png")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))
        elif os.path.exists(png_path):
            self.setWindowIcon(QIcon(png_path))

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
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(20, 18, 20, 24)
        self.sidebar_layout.setSpacing(12)

        # Collapse / Minimize Sidebar Toggle Button Row
        self.collapse_row = QHBoxLayout()
        self.collapse_row.setContentsMargins(0, 0, 0, 0)
        self.btn_collapse = QPushButton("«")
        self.btn_collapse.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.btn_collapse.setFixedSize(32, 32)
        self.btn_collapse.setCursor(Qt.PointingHandCursor)
        self.btn_collapse.setToolTip("Collapse Sidebar")
        self.btn_collapse.clicked.connect(self.toggle_sidebar)
        self.collapse_row.addStretch()
        self.collapse_row.addWidget(self.btn_collapse)
        self.sidebar_layout.addLayout(self.collapse_row)

        # Branding Container (UGM & PLN Logos + Title/Subtitle)
        self.branding_widget = QWidget()
        branding_layout = QVBoxLayout(self.branding_widget)
        branding_layout.setContentsMargins(0, 0, 0, 8)
        branding_layout.setSpacing(10)

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
        branding_layout.addLayout(logo_layout)

        # Title & Description Labels
        self.lbl_title = QLabel("Grid Impact Assessment Tool")
        self.lbl_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)

        self.lbl_desc = QLabel("Collaboration between UGM and PT. PLN Persero")
        self.lbl_desc.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setWordWrap(True)

        branding_layout.addWidget(self.lbl_title)
        branding_layout.addWidget(self.lbl_desc)
        self.sidebar_layout.addWidget(self.branding_widget)

        # Navigation Buttons
        self.nav_items = [
            ("1. Project & PFD Setup", "1"),
            ("2. Scenario Mapper", "2"),
            ("3. Visual Dashboard", "3"),
            ("4. Executive PDF Report", "4"),
            ("📖 User Manual & Guide", "📖"),
        ]
        self.btn_step1 = self.create_nav_btn(*self.nav_items[0])
        self.btn_step2 = self.create_nav_btn(*self.nav_items[1])
        self.btn_step3 = self.create_nav_btn(*self.nav_items[2])
        self.btn_step4 = self.create_nav_btn(*self.nav_items[3])
        self.btn_tutorial = self.create_nav_btn(*self.nav_items[4])

        self.sidebar_layout.addWidget(self.btn_step1)
        self.sidebar_layout.addWidget(self.btn_step2)
        self.sidebar_layout.addWidget(self.btn_step3)
        self.sidebar_layout.addWidget(self.btn_step4)
        self.sidebar_layout.addWidget(self.btn_tutorial)

        self.sidebar_layout.addStretch()

        # Dark/Light Theme Toggle
        self.btn_theme = QPushButton("🌙 Dark Mode")
        self.btn_theme.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_theme.setCheckable(True)
        self.btn_theme.setChecked(True)
        self.btn_theme.setToolTip("Toggle Dark / Light Mode")
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.sidebar_layout.addWidget(self.btn_theme)

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

    def create_nav_btn(self, full_text: str, short_text: str) -> QPushButton:
        display_text = full_text.replace("&", "&&")
        btn = QPushButton(display_text)
        btn.setProperty("full_text", display_text)
        btn.setProperty("short_text", short_text)
        btn.setToolTip(full_text)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setMinimumHeight(44)
        btn.setCheckable(True)
        return btn

    def toggle_sidebar(self):
        self.is_sidebar_collapsed = not self.is_sidebar_collapsed
        buttons = [self.btn_step1, self.btn_step2, self.btn_step3, self.btn_step4, self.btn_tutorial]

        if self.is_sidebar_collapsed:
            self.sidebar.setFixedWidth(64)
            self.sidebar_layout.setContentsMargins(8, 18, 8, 24)
            self.branding_widget.setVisible(False)
            self.btn_collapse.setText("»")
            self.btn_collapse.setFixedSize(48, 32)
            self.btn_collapse.setToolTip("Expand Sidebar")
            for btn in buttons:
                btn.setText(btn.property("short_text"))
            self.btn_theme.setText("🌙" if self.is_dark else "☀️")
        else:
            self.sidebar.setFixedWidth(290)
            self.sidebar_layout.setContentsMargins(20, 18, 20, 24)
            self.branding_widget.setVisible(True)
            self.btn_collapse.setText("«")
            self.btn_collapse.setFixedSize(32, 32)
            self.btn_collapse.setToolTip("Collapse Sidebar")
            for btn in buttons:
                btn.setText(btn.property("full_text"))
            self.btn_theme.setText("🌙 Dark Mode" if self.is_dark else "☀️ Light Mode")

        self.apply_styles()

    def switch_page(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        buttons = [self.btn_step1, self.btn_step2, self.btn_step3, self.btn_step4, self.btn_tutorial]
        for i, btn in enumerate(buttons):
            btn.setChecked(i == index)
            self.update_btn_style(btn, i == index)

        if index == 1:
            self.scenario_page.refresh_element_mapping()
        elif index == 2:
            self.dashboard_page.on_page_shown()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        if self.is_sidebar_collapsed:
            self.btn_theme.setText("🌙" if self.is_dark else "☀️")
        else:
            self.btn_theme.setText("🌙 Dark Mode" if self.is_dark else "☀️ Light Mode")
        self.import_page.set_theme(self.is_dark)
        self.scenario_page.set_theme(self.is_dark)
        self.dashboard_page.set_theme(self.is_dark)
        self.report_page.set_theme(self.is_dark)
        self.tutorial_page.set_theme(self.is_dark)
        self.apply_styles()

    def update_btn_style(self, btn: QPushButton, is_active: bool):
        align_rule = "text-align: center; padding: 0px;" if self.is_sidebar_collapsed else "text-align: left; padding-left: 14px;"
        if self.is_dark:
            tip_rule = "QToolTip { background-color: #1E293B; color: #F8FAFC; border: 1px solid #38BDF8; padding: 4px 8px; }"
            if is_active:
                btn.setStyleSheet(f"QPushButton {{ background-color: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; {align_rule} font-weight: bold; }} {tip_rule}")
            else:
                weight_rule = "font-weight: bold;" if self.is_sidebar_collapsed else ""
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: transparent; color: #94A3B8; border: none; border-radius: 6px; {align_rule} {weight_rule} }}"
                    f"QPushButton:hover {{ background-color: #1E293B; color: #F8FAFC; }} {tip_rule}"
                )
        else:
            tip_rule = "QToolTip { background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 4px 8px; }"
            if is_active:
                btn.setStyleSheet(f"QPushButton {{ background-color: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; {align_rule} font-weight: bold; }} {tip_rule}")
            else:
                weight_rule = "font-weight: bold;" if self.is_sidebar_collapsed else ""
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: transparent; color: #475569; border: none; border-radius: 6px; {align_rule} {weight_rule} }}"
                    f"QPushButton:hover {{ background-color: #F1F5F9; color: #0F172A; }} {tip_rule}"
                )

    def apply_styles(self):
        buttons = [self.btn_step1, self.btn_step2, self.btn_step3, self.btn_step4, self.btn_tutorial]
        for i, btn in enumerate(buttons):
            self.update_btn_style(btn, btn.isChecked())

        app = QApplication.instance()
        if self.is_dark:
            self.sidebar.setStyleSheet(
                "QFrame#sidebar { background-color: #0F172A; border-right: 1px solid #1E293B; }"
                "QToolTip { background-color: #1E293B; color: #F8FAFC; border: 1px solid #38BDF8; padding: 4px 8px; }"
            )
            self.lbl_title.setStyleSheet("color: #F8FAFC; border: none; background: transparent;")
            self.lbl_desc.setStyleSheet("color: #38BDF8; border: none; background: transparent;")
            self.btn_collapse.setStyleSheet(
                "QPushButton { background-color: transparent; color: #94A3B8; border: none; border-radius: 6px; padding: 0px 0px 3px 0px; }"
                "QPushButton:hover { background-color: #1E293B; color: #38BDF8; }"
                "QToolTip { background-color: #1E293B; color: #F8FAFC; border: 1px solid #38BDF8; padding: 4px 8px; }"
            )
            self.btn_theme.setStyleSheet(
                "QPushButton { background-color: #1E293B; color: #F8FAFC; border: 1px solid #334155; border-radius: 6px; padding: 8px; }"
                "QPushButton:hover { background-color: #334155; }"
                "QToolTip { background-color: #1E293B; color: #F8FAFC; border: 1px solid #38BDF8; padding: 4px 8px; }"
            )

            if app:
                app_pal = app.palette()
                app_pal.setColor(QPalette.Window, QColor("#1A202C"))
                app_pal.setColor(QPalette.WindowText, QColor("#F8FAFC"))
                app_pal.setColor(QPalette.Base, QColor("#2D3748"))
                app_pal.setColor(QPalette.Text, QColor("#F8FAFC"))
                app_pal.setColor(QPalette.ToolTipBase, QColor("#1E293B"))
                app_pal.setColor(QPalette.ToolTipText, QColor("#F8FAFC"))
                app.setPalette(app_pal)
                pal = QToolTip.palette()
                pal.setColor(QPalette.ToolTipBase, QColor("#1E293B"))
                pal.setColor(QPalette.ToolTipText, QColor("#F8FAFC"))
                pal.setColor(QPalette.Text, QColor("#F8FAFC"))
                pal.setColor(QPalette.WindowText, QColor("#F8FAFC"))
                QToolTip.setPalette(pal)
                app.setStyleSheet(
                    "QToolTip { background-color: #1E293B; color: #F8FAFC; border: 1px solid #38BDF8; padding: 4px 8px; font-size: 11px; }"
                    "QMessageBox { background-color: #1E293B; color: #F8FAFC; }"
                    "QMessageBox QLabel { color: #F8FAFC; font-size: 11px; font-weight: 500; }"
                    "QMessageBox QPushButton { background-color: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold; min-width: 80px; }"
                    "QMessageBox QPushButton:hover { background-color: #0369A1; }"
                    "QComboBox { background-color: #0F172A; color: #F8FAFC; border: 1px solid #475569; border-radius: 6px; padding: 4px 8px; }"
                    "QComboBox QAbstractItemView { background-color: #0F172A; color: #F8FAFC; selection-background-color: #0284C7; selection-color: #FFFFFF; border: 1px solid #334155; border-radius: 6px; outline: 0px; padding: 4px; }"
                    "QComboBox QAbstractItemView::item { min-height: 26px; padding: 4px 8px; color: #F8FAFC; background-color: #0F172A; }"
                    "QComboBox QAbstractItemView::item:selected { background-color: #0284C7; color: #FFFFFF; }"
                    "QComboBox QAbstractItemView::item:hover { background-color: #1E293B; color: #F8FAFC; }"
                )
        else:
            self.sidebar.setStyleSheet(
                "QFrame#sidebar { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }"
                "QToolTip { background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 4px 8px; }"
            )
            self.lbl_title.setStyleSheet("color: #0F172A; border: none; background: transparent;")
            self.lbl_desc.setStyleSheet("color: #0284C7; border: none; background: transparent;")
            self.btn_collapse.setStyleSheet(
                "QPushButton { background-color: transparent; color: #64748B; border: none; border-radius: 6px; padding: 0px 0px 3px 0px; }"
                "QPushButton:hover { background-color: #F1F5F9; color: #0284C7; }"
                "QToolTip { background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 4px 8px; }"
            )
            self.btn_theme.setStyleSheet(
                "QPushButton { background-color: #F1F5F9; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px; }"
                "QPushButton:hover { background-color: #E2E8F0; }"
                "QToolTip { background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 4px 8px; }"
            )

            if app:
                app_pal = app.palette()
                app_pal.setColor(QPalette.Window, QColor("#F8FAFC"))
                app_pal.setColor(QPalette.WindowText, QColor("#0F172A"))
                app_pal.setColor(QPalette.Base, QColor("#FFFFFF"))
                app_pal.setColor(QPalette.Text, QColor("#0F172A"))
                app_pal.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
                app_pal.setColor(QPalette.ToolTipText, QColor("#0F172A"))
                app.setPalette(app_pal)
                pal = QToolTip.palette()
                pal.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
                pal.setColor(QPalette.ToolTipText, QColor("#0F172A"))
                pal.setColor(QPalette.Text, QColor("#0F172A"))
                pal.setColor(QPalette.WindowText, QColor("#0F172A"))
                QToolTip.setPalette(pal)
                app.setStyleSheet(
                    "QToolTip { background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 4px 8px; font-size: 11px; }"
                    "QMessageBox { background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; }"
                    "QMessageBox QLabel { color: #0F172A; font-size: 11px; font-weight: 500; }"
                    "QMessageBox QPushButton { background-color: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold; min-width: 80px; }"
                    "QMessageBox QPushButton:hover { background-color: #0369A1; }"
                    "QComboBox { background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px 8px; }"
                    "QComboBox QAbstractItemView { background-color: #FFFFFF; color: #0F172A; selection-background-color: #0284C7; selection-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; outline: 0px; padding: 4px; }"
                    "QComboBox QAbstractItemView::item { min-height: 26px; padding: 4px 8px; color: #0F172A; background-color: #FFFFFF; }"
                    "QComboBox QAbstractItemView::item:selected { background-color: #0284C7; color: #FFFFFF; }"
                    "QComboBox QAbstractItemView::item:hover { background-color: #E2E8F0; color: #0F172A; }"
                )
