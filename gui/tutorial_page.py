# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class TutorialPage(QScrollArea):
    """Integrated Step-by-Step User Guide and Operating Manual."""

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
        layout.setSpacing(24)

        # Header
        header_box = QVBoxLayout()
        self.header = QLabel("📖 Operating Manual & Step-by-Step User Guide")
        self.header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.desc = QLabel("Comprehensive guide for conducting 22-Scenario Grid Impact Studies under Indonesian Grid Code (ESDM No. 20/2020).")
        self.desc.setFont(QFont("Segoe UI", 10))
        header_box.addWidget(self.header)
        header_box.addWidget(self.desc)
        layout.addLayout(header_box)

        # Card 1: Overview & Workflow Strategy
        self.card_overview = QFrame()
        cov_layout = QVBoxLayout(self.card_overview)
        self.t_cov = QLabel("1. Software Workflow Overview")
        self.t_cov.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.b_cov = QLabel(
            "This software automates statutory 22-scenario grid impact assessment studies for integrating Small Modular Reactors (SMR), "
            "Nuclear Power Plants (PLTN), or large-scale power plants into DIgSILENT PowerFactory grid models.\n\n"
            "The workflow follows 4 simple sequential steps:\n"
            "  • Step 1: Project & PFD Setup (Connect PowerFactory & load grid model)\n"
            "  • Step 2: Universal Grid Mapper (Inspect 5-point auto-detection or manually select elements)\n"
            "  • Step 3: Visual Dashboard (Inspect High-Voltage transmission charts & Executive Summary)\n"
            "  • Step 4: Executive PDF Exporter (Export official multi-page report for PLN & ESDM review)"
        )
        self.b_cov.setWordWrap(True)
        self.b_cov.setFont(QFont("Segoe UI", 10))
        cov_layout.addWidget(self.t_cov)
        cov_layout.addWidget(self.b_cov)
        layout.addWidget(self.card_overview)

        # Card 2: Step 1 Detailed Guide
        self.card_s1 = QFrame()
        cs1_layout = QVBoxLayout(self.card_s1)
        self.t_s1 = QLabel("2. Step 1: Project Initialization & PFD Model Setup")
        self.t_s1.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.b_s1 = QLabel(
            "How to operate Step 1:\n"
            "  1. Ensure DIgSILENT PowerFactory (2024 / 2023 / 2022) is installed on your computer.\n"
            "  2. Select an installed PowerFactory project from the dropdown (e.g., '39 Bus New England System' or 'Bangka_150kV_SMR_Integration').\n"
            "  3. Click '⚡ Activate PowerFactory Project' to load the grid model.\n"
            "  4. Alternatively, click '📁 Browse & Import .pfd File' to load a custom PowerFactory project file directly.\n"
            "  5. Verify the Connection Status Banner displays '🟢 Connected to PowerFactory'."
        )
        self.b_s1.setWordWrap(True)
        self.b_s1.setFont(QFont("Segoe UI", 10))
        cs1_layout.addWidget(self.t_s1)
        cs1_layout.addWidget(self.b_s1)
        layout.addWidget(self.card_s1)

        # Card 3: Step 2 Detailed Guide (Auto-Detection Rules)
        self.card_s2 = QFrame()
        cs2_layout = QVBoxLayout(self.card_s2)
        self.t_s2 = QLabel("3. Step 2: 5-Point Smart Auto-Detection & Scenario Setup")
        self.t_s2.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.b_s2 = QLabel(
            "How 5-Point Auto-Detection works:\n"
            "  1. SMR Generator Unit: Auto-detects generators containing keywords 'SMR' or 'PLTN'.\n"
            "  2. Largest Non-SMR Generator: Auto-detects non-SMR generator with highest MW capacity (pgini / sgn).\n"
            "  3. Biggest Load Substation: Auto-detects load substation with largest MW demand (plini).\n"
            "  4. Critical Transmission Line: Auto-detects line interconnecting the SMR terminal bus.\n"
            "  5. Operation Scenarios: Auto-detects native 'Peak Load' ('WBP') and 'Low Load' ('LWBP') scenarios.\n\n"
            "Manual Override:\n"
            "  • If any component displays '⚠️ NOT DETECTED (MANUAL FALLBACK)', or if you want to select a specific generator/line, "
            "simply select your desired element from the dropdown menus.\n"
            "  • Click '🚀 Execute All 22 Impact Assessment Scenarios' to launch the batch simulation engine."
        )
        self.b_s2.setWordWrap(True)
        self.b_s2.setFont(QFont("Segoe UI", 10))
        cs2_layout.addWidget(self.t_s2)
        cs2_layout.addWidget(self.b_s2)
        layout.addWidget(self.card_s2)

        # Card 4: Step 3 Detailed Guide
        self.card_s3 = QFrame()
        cs3_layout = QVBoxLayout(self.card_s3)
        self.t_s3 = QLabel("4. Step 3: Visual Dashboard & Executive Summary")
        self.t_s3.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.b_s3 = QLabel(
            "Navigating the Dashboard:\n"
            "  • Executive Summary Panel: Displays overall compliance score (%) and crisp, high-contrast diagnostic explanations for any Non-Compliant scenarios.\n"
            "  • Load Flow Tab: Displays Bus Voltages (0.90 – 1.05 p.u.), Active/Reactive Power (P & Q), Transmission Line Loading (≤100%), and Generator Dispatch for High-Voltage Transmission Buses (≥100 kV).\n"
            "  • Short Circuit Tab: Displays Short-Circuit Power S\"k (MVA), Fault Current I\"k (kA), and Short Circuit Power Ratio (SCR ≥ 3.0).\n"
            "  • Dynamic RMS Tab: Overlays all 4 contingency trip events (SMR Trip, Gen Trip, Load Trip, Line Trip N-1) together on every dynamic chart (Frequency f(t), Voltage V(t), Active Power P(t), Reactive Power Q(t)).\n"
            "  • Compliance Matrix Tab: Complete 22-scenario results table."
        )
        self.b_s3.setWordWrap(True)
        self.b_s3.setFont(QFont("Segoe UI", 10))
        cs3_layout.addWidget(self.t_s3)
        cs3_layout.addWidget(self.b_s3)
        layout.addWidget(self.card_s3)

        # Card 5: Step 4 Detailed Guide
        self.card_s4 = QFrame()
        cs4_layout = QVBoxLayout(self.card_s4)
        self.t_s4 = QLabel("5. Step 4: Executive PDF Exporter")
        self.t_s4.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.b_s4 = QLabel(
            "Exporting Official PDF Reports:\n"
            "  1. Click '📄 Export Executive Grid Impact PDF Report'.\n"
            "  2. Choose a save location on your computer.\n"
            "  3. The exporter will generate a multi-page PDF report featuring active project element names, "
            "Master 22-Scenario Compliance Matrix, embedded 4-panel visual charts, and technical narratives with clean human-readable text."
        )
        self.b_s4.setWordWrap(True)
        self.b_s4.setFont(QFont("Segoe UI", 10))
        cs4_layout.addWidget(self.t_s4)
        cs4_layout.addWidget(self.b_s4)
        layout.addWidget(self.card_s4)

        layout.addStretch()
        self.apply_styles()

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self.apply_styles()

    def apply_styles(self):
        cards = [self.card_overview, self.card_s1, self.card_s2, self.card_s3, self.card_s4]
        titles = [self.t_cov, self.t_s1, self.t_s2, self.t_s3, self.t_s4]
        bodies = [self.b_cov, self.b_s1, self.b_s2, self.b_s3, self.b_s4]

        if self.is_dark:
            self.setStyleSheet("QScrollArea { border: none; background-color: #0B0F19; }")
            self.main_content.setStyleSheet("background-color: #0B0F19;")
            self.header.setStyleSheet("color: #F8FAFC;")
            self.desc.setStyleSheet("color: #94A3B8;")

            for c in cards:
                c.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 20px;")
            for t in titles:
                t.setStyleSheet("color: #38BDF8;")
            for b in bodies:
                b.setStyleSheet("color: #F8FAFC;")
        else:
            self.setStyleSheet("QScrollArea { border: none; background-color: #F8FAFC; }")
            self.main_content.setStyleSheet("background-color: #F8FAFC;")
            self.header.setStyleSheet("color: #0F172A;")
            self.desc.setStyleSheet("color: #475569;")

            for c in cards:
                c.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 20px;")
            for t in titles:
                t.setStyleSheet("color: #0284C7;")
            for b in bodies:
                b.setStyleSheet("color: #0F172A;")
