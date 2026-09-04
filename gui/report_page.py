# -*- coding: utf-8 -*-
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFileDialog, QFrame, QMessageBox, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from reporting.pdf_generator import GridImpactPDFGenerator

class ReportPage(QScrollArea):
    def __init__(self, connector):
        super().__init__()
        self.connector = connector
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
        self.header = QLabel("Step 4: Grid Impact Executive PDF Exporter")
        self.header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.desc = QLabel("Export statutory 22-Scenario Grid Impact Study PDF Report for ESDM & PT. PLN Persero review.")
        self.desc.setFont(QFont("Segoe UI", 10))
        header_box.addWidget(self.header)
        header_box.addWidget(self.desc)
        layout.addLayout(header_box)

        # PDF Export Action Card
        self.card_pdf = QFrame()
        pdf_layout = QVBoxLayout(self.card_pdf)
        pdf_layout.setSpacing(16)

        self.title_pdf = QLabel("Official ESDM Grid Impact Assessment PDF Export:")
        self.title_pdf.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.lbl_pdf_info = QLabel(
            "The exported PDF report includes:\n"
            "• Executive Summary Compliance Overview under ESDM No. 20/2020.\n"
            "• Master 22-Scenario Compliance Matrix & Failure Rationales Table.\n"
            "• Embedded Visual Charts & Engineering Descriptions for Load Flow, Short Circuit, and Dynamic Stability identical to the Visual Dashboard."
        )
        self.lbl_pdf_info.setFont(QFont("Segoe UI", 10))

        self.btn_export_pdf = QPushButton("📄 Export Executive Grid Impact PDF Report")
        self.btn_export_pdf.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_export_pdf.setMinimumHeight(48)
        self.btn_export_pdf.clicked.connect(self.export_pdf)

        pdf_layout.addWidget(self.title_pdf)
        pdf_layout.addWidget(self.lbl_pdf_info)
        pdf_layout.addWidget(self.btn_export_pdf)

        layout.addWidget(self.card_pdf)
        layout.addStretch()
        self.apply_styles()

    def export_pdf(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Grid Impact PDF Report",
            "Grid_Impact_Assessment_Report_22Scenarios.pdf",
            "PDF Files (*.pdf)"
        )
        if not save_path:
            return

        try:
            summary = self.connector.get_summary()
            hv_elements = self.connector.get_hv_grid_elements(min_voltage_kv=100.0)
            
            main_win = self.window()
            if hasattr(main_win, "scenario_page") and main_win.scenario_page.latest_batch_results:
                batch_res = main_win.scenario_page.latest_batch_results
            elif hasattr(main_win, "dashboard_page"):
                targets = main_win.dashboard_page.batch_runner.auto_detect_targets()
                batch_res = main_win.dashboard_page.batch_runner.run_all_22_scenarios(targets)
            else:
                batch_res = {}

            assessment_data = {**summary, **hv_elements, **batch_res}

            pdf_path = GridImpactPDFGenerator.generate_pdf(save_path, assessment_data)
            QMessageBox.information(
                self, 
                "PDF Exported Successfully", 
                f"✅ Official 22-Scenario Grid Impact Report saved to:\n\n{pdf_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"❌ Failed to generate PDF report:\n{e}")

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self.apply_styles()

    def apply_styles(self):
        if self.is_dark:
            self.setStyleSheet("QScrollArea { border: none; background-color: #0B0F19; }")
            self.main_content.setStyleSheet("background-color: #0B0F19;")
            self.header.setStyleSheet("color: #F8FAFC;")
            self.desc.setStyleSheet("color: #94A3B8;")
            self.card_pdf.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 20px;")
            self.title_pdf.setStyleSheet("color: #38BDF8;")
            self.lbl_pdf_info.setStyleSheet("color: #F8FAFC;")
            self.btn_export_pdf.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 12px;")
        else:
            self.setStyleSheet("QScrollArea { border: none; background-color: #F8FAFC; }")
            self.main_content.setStyleSheet("background-color: #F8FAFC;")
            self.header.setStyleSheet("color: #0F172A;")
            self.desc.setStyleSheet("color: #475569;")
            self.card_pdf.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 20px;")
            self.title_pdf.setStyleSheet("color: #0284C7;")
            self.lbl_pdf_info.setStyleSheet("color: #0F172A;")
            self.btn_export_pdf.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 12px;")
