# -*- coding: utf-8 -*-
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFileDialog, QFrame, QMessageBox, QLineEdit, QComboBox, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class ImportPage(QScrollArea):
    def __init__(self, connector):
        super().__init__()
        self.connector = connector
        self.selected_file_path = None
        self.is_dark = True

        self.setWidgetResizable(True)
        self.main_content = QWidget()
        self.setWidget(self.main_content)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self.main_content)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(20)

        header_box = QVBoxLayout()
        self.header = QLabel("Step 1: PowerFactory Environment & Project Import")
        self.header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.desc = QLabel("Connect to DIgSILENT PowerFactory or select an active project database / upload a custom .pfd model.")
        self.desc.setFont(QFont("Segoe UI", 10))
        header_box.addWidget(self.header)
        header_box.addWidget(self.desc)
        layout.addLayout(header_box)

        # API Folder Setup Card
        self.card_api = QFrame()
        api_layout = QVBoxLayout(self.card_api)
        api_layout.setSpacing(12)

        self.lbl_api_title = QLabel("1. PowerFactory Python API Folder Path:")
        self.lbl_api_title.setFont(QFont("Segoe UI", 11, QFont.Bold))

        api_input_box = QHBoxLayout()
        self.txt_api_path = QLineEdit(self.connector.pf_path)
        self.txt_api_path.setFont(QFont("Segoe UI", 10))
        self.txt_api_path.setMinimumHeight(36)

        self.btn_browse_api = QPushButton("Browse API Folder...")
        self.btn_browse_api.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_browse_api.setMinimumHeight(36)
        self.btn_browse_api.clicked.connect(self.browse_api_folder)

        self.btn_connect_api = QPushButton("⚡ Reconnect API")
        self.btn_connect_api.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_connect_api.setMinimumHeight(36)
        self.btn_connect_api.clicked.connect(self.reconnect_api)

        api_input_box.addWidget(self.txt_api_path)
        api_input_box.addWidget(self.btn_browse_api)
        api_input_box.addWidget(self.btn_connect_api)

        api_layout.addWidget(self.lbl_api_title)
        api_layout.addLayout(api_input_box)
        layout.addWidget(self.card_api)

        # Database Project Selector Card
        self.card_db = QFrame()
        db_layout = QVBoxLayout(self.card_db)
        db_layout.setSpacing(12)

        self.lbl_db_title = QLabel("2. Select Installed PowerFactory Project Database:")
        self.lbl_db_title.setFont(QFont("Segoe UI", 11, QFont.Bold))

        db_input_box = QHBoxLayout()
        self.combo_projects = QComboBox()
        self.combo_projects.setFont(QFont("Segoe UI", 10))
        self.combo_projects.setMinimumHeight(36)

        self.btn_refresh_projects = QPushButton("🔄 Refresh Projects")
        self.btn_refresh_projects.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_refresh_projects.setMinimumHeight(36)
        self.btn_refresh_projects.clicked.connect(self.refresh_installed_projects)

        self.btn_activate_project = QPushButton("✅ Activate Selected Project")
        self.btn_activate_project.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_activate_project.setMinimumHeight(36)
        self.btn_activate_project.clicked.connect(self.activate_selected_project)

        db_input_box.addWidget(self.combo_projects)
        db_input_box.addWidget(self.btn_refresh_projects)
        db_input_box.addWidget(self.btn_activate_project)

        db_layout.addWidget(self.lbl_db_title)
        db_layout.addLayout(db_input_box)
        layout.addWidget(self.card_db)

        # Custom PFD Import Card
        self.card_pfd = QFrame()
        pfd_layout = QVBoxLayout(self.card_pfd)
        pfd_layout.setSpacing(12)

        self.lbl_pfd_title = QLabel("3. Import Custom PowerFactory Project File (.pfd):")
        self.lbl_pfd_title.setFont(QFont("Segoe UI", 11, QFont.Bold))

        pfd_input_box = QHBoxLayout()
        self.txt_pfd_path = QLineEdit()
        self.txt_pfd_path.setPlaceholderText("Select custom .pfd file...")
        self.txt_pfd_path.setFont(QFont("Segoe UI", 10))
        self.txt_pfd_path.setMinimumHeight(36)

        self.btn_browse_pfd = QPushButton("Browse .pfd File...")
        self.btn_browse_pfd.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_browse_pfd.setMinimumHeight(36)
        self.btn_browse_pfd.clicked.connect(self.browse_pfd_file)

        self.btn_load_pfd = QPushButton("📥 Load & Import .pfd")
        self.btn_load_pfd.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_load_pfd.setMinimumHeight(36)
        self.btn_load_pfd.clicked.connect(self.import_pfd)

        pfd_input_box.addWidget(self.txt_pfd_path)
        pfd_input_box.addWidget(self.btn_browse_pfd)
        pfd_input_box.addWidget(self.btn_load_pfd)

        pfd_layout.addWidget(self.lbl_pfd_title)
        pfd_layout.addLayout(pfd_input_box)
        layout.addWidget(self.card_pfd)

        # Active Model Info Card
        self.card_info = QFrame()
        info_layout = QVBoxLayout(self.card_info)
        info_layout.setSpacing(8)

        self.lbl_info_title = QLabel("Active Grid Model Status Summary:")
        self.lbl_info_title.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.lbl_status = QLabel("Checking connection...")
        self.lbl_status.setFont(QFont("Segoe UI", 10))
        self.lbl_buses = QLabel("Substation Buses: --")
        self.lbl_buses.setFont(QFont("Segoe UI", 10))
        self.lbl_gens = QLabel("Generators: --")
        self.lbl_gens.setFont(QFont("Segoe UI", 10))
        self.lbl_lines = QLabel("Transmission Lines: --")
        self.lbl_lines.setFont(QFont("Segoe UI", 10))

        info_layout.addWidget(self.lbl_info_title)
        info_layout.addWidget(self.lbl_status)
        info_layout.addWidget(self.lbl_buses)
        info_layout.addWidget(self.lbl_gens)
        info_layout.addWidget(self.lbl_lines)

        layout.addWidget(self.card_info)
        layout.addStretch()

        self.refresh_installed_projects()
        self.update_summary_display()
        self.apply_styles()

    def notify_main_window_of_project_change(self):
        main_win = self.window()
        if hasattr(main_win, "scenario_page"):
            main_win.scenario_page.elements_loaded = False
            main_win.scenario_page.refresh_element_mapping()

    def browse_api_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select PowerFactory Python 3.12 API Folder", self.connector.pf_path)
        if folder:
            self.txt_api_path.setText(folder)

    def reconnect_api(self):
        path = self.txt_api_path.text().strip()
        if self.connector.set_custom_api_path(path):
            QMessageBox.information(self, "Connected", f"✅ Connected to PowerFactory API at:\n{path}")
            self.refresh_installed_projects()
            self.update_summary_display()
            self.notify_main_window_of_project_change()
        else:
            QMessageBox.critical(self, "Connection Failed", f"❌ Failed to connect at:\n{path}\n\nDetails:\n{self.connector.last_error_message}")

    def refresh_installed_projects(self):
        projects = self.connector.get_installed_projects()
        self.combo_projects.clear()
        if projects:
            self.combo_projects.addItems(projects)
            if self.connector.active_project_name and self.connector.active_project_name in projects:
                self.combo_projects.setCurrentText(self.connector.active_project_name)

    def activate_selected_project(self):
        proj_name = self.combo_projects.currentText()
        if not proj_name:
            return
        if self.connector.activate_project_by_name(proj_name):
            QMessageBox.information(self, "Project Activated", f"✅ PowerFactory Project '{proj_name}' is now active!")
            self.update_summary_display()
            self.notify_main_window_of_project_change()
        else:
            QMessageBox.warning(self, "Activation Failed", f"⚠️ Could not activate project '{proj_name}'.")

    def browse_pfd_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PowerFactory Project File", "", "PowerFactory Files (*.pfd);;All Files (*.*)")
        if path:
            self.txt_pfd_path.setText(path)

    def import_pfd(self):
        path = self.txt_pfd_path.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Invalid File", "Please select a valid .pfd file path.")
            return

        if self.connector.load_custom_pfd(path):
            QMessageBox.information(self, "Import Successful", f"✅ Successfully imported and activated:\n{path}")
            self.update_summary_display()
            self.notify_main_window_of_project_change()
        else:
            QMessageBox.information(self, "PFD Loaded", f"ℹ️ Registered custom model path:\n{path}\nProceed to Step 2 to configure scenarios.")
            self.update_summary_display()
            self.notify_main_window_of_project_change()

    def update_summary_display(self):
        summary = self.connector.get_summary()
        self.lbl_status.setText(f"Engine Status: {summary.get('status', 'Ready')}")
        self.lbl_buses.setText(f"Substation Buses: {len(summary.get('buses', []))} buses ({', '.join(summary.get('buses', [])[:4])}...)")
        self.lbl_gens.setText(f"Generators: {len(summary.get('generators', []))} units ({', '.join(summary.get('generators', [])[:3])}...)")
        self.lbl_lines.setText(f"Transmission Lines: {len(summary.get('lines', []))} lines")

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self.apply_styles()

    def apply_styles(self):
        cards = [self.card_api, self.card_db, self.card_pfd, self.card_info]
        titles = [self.lbl_api_title, self.lbl_db_title, self.lbl_pfd_title, self.lbl_info_title]

        if self.is_dark:
            self.setStyleSheet("QScrollArea { border: none; background-color: #0B0F19; }")
            self.main_content.setStyleSheet("background-color: #0B0F19;")
            self.header.setStyleSheet("color: #F8FAFC;")
            self.desc.setStyleSheet("color: #94A3B8;")

            for c in cards:
                c.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 20px;")
            for t in titles:
                t.setStyleSheet("color: #38BDF8;")

            self.txt_api_path.setStyleSheet("background-color: #0F172A; color: #F8FAFC; border: 1px solid #475569; border-radius: 6px; padding: 6px 12px;")
            self.txt_pfd_path.setStyleSheet("background-color: #0F172A; color: #F8FAFC; border: 1px solid #475569; border-radius: 6px; padding: 6px 12px;")
            self.combo_projects.setStyleSheet("background-color: #0F172A; color: #F8FAFC; border: 1px solid #475569; border-radius: 6px; padding: 6px 12px;")

            self.lbl_status.setStyleSheet("color: #38BDF8; font-weight: bold;")
            self.lbl_buses.setStyleSheet("color: #F8FAFC;")
            self.lbl_gens.setStyleSheet("color: #F8FAFC;")
            self.lbl_lines.setStyleSheet("color: #F8FAFC;")

            self.btn_browse_api.setStyleSheet("background-color: #334155; color: white; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_connect_api.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_refresh_projects.setStyleSheet("background-color: #334155; color: white; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_activate_project.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_browse_pfd.setStyleSheet("background-color: #334155; color: white; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_load_pfd.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 8px 14px;")
        else:
            self.setStyleSheet("QScrollArea { border: none; background-color: #F8FAFC; }")
            self.main_content.setStyleSheet("background-color: #F8FAFC;")
            self.header.setStyleSheet("color: #0F172A;")
            self.desc.setStyleSheet("color: #475569;")

            for c in cards:
                c.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 20px;")
            for t in titles:
                t.setStyleSheet("color: #0284C7;")

            self.txt_api_path.setStyleSheet("background-color: #F8FAFC; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px;")
            self.txt_pfd_path.setStyleSheet("background-color: #F8FAFC; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px;")
            self.combo_projects.setStyleSheet("background-color: #F8FAFC; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px;")

            self.lbl_status.setStyleSheet("color: #0284C7; font-weight: bold;")
            self.lbl_buses.setStyleSheet("color: #0F172A;")
            self.lbl_gens.setStyleSheet("color: #0F172A;")
            self.lbl_lines.setStyleSheet("color: #0F172A;")

            self.btn_browse_api.setStyleSheet("background-color: #E2E8F0; color: #0F172A; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_connect_api.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_refresh_projects.setStyleSheet("background-color: #E2E8F0; color: #0F172A; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_activate_project.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_browse_pfd.setStyleSheet("background-color: #E2E8F0; color: #0F172A; border: none; border-radius: 6px; padding: 8px 14px;")
            self.btn_load_pfd.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 8px 14px;")
