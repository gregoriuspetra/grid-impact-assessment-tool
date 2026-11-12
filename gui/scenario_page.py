# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QComboBox, QDoubleSpinBox, QMessageBox, QScrollArea, QProgressBar,
                             QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.batch_runner import GridImpactBatchRunner

class ScenarioPage(QScrollArea):
    def __init__(self, connector):
        super().__init__()
        self.connector = connector
        self.batch_runner = GridImpactBatchRunner(connector)
        self.is_dark = True
        self.latest_batch_results = None
        self.elements_loaded = False

        self.setWidgetResizable(True)
        self.main_content = QWidget()
        self.setWidget(self.main_content)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self.main_content)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(20)

        header_box = QVBoxLayout()
        self.header = QLabel("Step 2: Universal Grid Mapper & 22-Scenario Assessment")
        self.header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.desc = QLabel("Inspect 5-point auto-detection status (DETECTED / NOT DETECTED) or manually override via dropdowns.")
        self.desc.setFont(QFont("Segoe UI", 10))
        header_box.addWidget(self.header)
        header_box.addWidget(self.desc)
        layout.addLayout(header_box)

        # Target Grid Element Mapper Card with Status Badges
        self.card_mapper = QFrame()
        map_layout = QVBoxLayout(self.card_mapper)
        map_layout.setSpacing(12)

        self.title_mapper = QLabel("1. Target Grid Element Mapper & Auto-Detection Status:")
        self.title_mapper.setFont(QFont("Segoe UI", 11, QFont.Bold))
        map_layout.addWidget(self.title_mapper)

        # 1. SMR Status & Dropdown
        box_smr = QHBoxLayout()
        self.lbl_smr = QLabel("1. SMR Generator Unit ('SMR' / 'PLTN'):")
        self.lbl_smr_status = QLabel("🟢 DETECTED")
        self.lbl_smr_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        box_smr.addWidget(self.lbl_smr)
        box_smr.addStretch()
        box_smr.addWidget(self.lbl_smr_status)

        self.combo_smr = QComboBox()
        self.combo_smr.setFont(QFont("Segoe UI", 10))
        self.combo_smr.setMinimumHeight(36)
        self.lbl_smr_msg = QLabel("Status message...")
        self.lbl_smr_msg.setFont(QFont("Segoe UI", 8))

        map_layout.addLayout(box_smr)
        map_layout.addWidget(self.combo_smr)
        map_layout.addWidget(self.lbl_smr_msg)

        # 2. PCC Substation Busbar Status & Dropdown (Short Circuit Location)
        box_pcc = QHBoxLayout()
        self.lbl_pcc = QLabel("2. PCC Substation Busbar (Short Circuit Location):")
        self.lbl_pcc_status = QLabel("🟢 DETECTED")
        self.lbl_pcc_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        box_pcc.addWidget(self.lbl_pcc)
        box_pcc.addStretch()
        box_pcc.addWidget(self.lbl_pcc_status)

        self.combo_pcc_bus = QComboBox()
        self.combo_pcc_bus.setFont(QFont("Segoe UI", 10))
        self.combo_pcc_bus.setMinimumHeight(36)
        self.lbl_pcc_msg = QLabel("Status message...")
        self.lbl_pcc_msg.setFont(QFont("Segoe UI", 8))

        map_layout.addLayout(box_pcc)
        map_layout.addWidget(self.combo_pcc_bus)
        map_layout.addWidget(self.lbl_pcc_msg)

        # 3. Non-SMR Gen Status & Dropdown
        box_non_smr = QHBoxLayout()
        self.lbl_non_smr = QLabel("3. Largest Non-SMR Generator (Max MW Capacity):")
        self.lbl_non_smr_status = QLabel("🟢 DETECTED")
        self.lbl_non_smr_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        box_non_smr.addWidget(self.lbl_non_smr)
        box_non_smr.addStretch()
        box_non_smr.addWidget(self.lbl_non_smr_status)

        self.combo_non_smr = QComboBox()
        self.combo_non_smr.setFont(QFont("Segoe UI", 10))
        self.combo_non_smr.setMinimumHeight(36)
        self.lbl_non_smr_msg = QLabel("Status message...")
        self.lbl_non_smr_msg.setFont(QFont("Segoe UI", 8))

        map_layout.addLayout(box_non_smr)
        map_layout.addWidget(self.combo_non_smr)
        map_layout.addWidget(self.lbl_non_smr_msg)

        # 4. Load Status & Dropdown
        box_load = QHBoxLayout()
        self.lbl_big_load = QLabel("4. Biggest Load Substation (Max MW Demand):")
        self.lbl_load_status = QLabel("🟢 DETECTED")
        self.lbl_load_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        box_load.addWidget(self.lbl_big_load)
        box_load.addStretch()
        box_load.addWidget(self.lbl_load_status)

        self.combo_big_load = QComboBox()
        self.combo_big_load.setFont(QFont("Segoe UI", 10))
        self.combo_big_load.setMinimumHeight(36)
        self.lbl_load_msg = QLabel("Status message...")
        self.lbl_load_msg.setFont(QFont("Segoe UI", 8))

        map_layout.addLayout(box_load)
        map_layout.addWidget(self.combo_big_load)
        map_layout.addWidget(self.lbl_load_msg)

        # 5. Line Status & Dropdown
        box_line = QHBoxLayout()
        self.lbl_crit_line = QLabel("5. Critical Transmission Line (SMR Interconnection):")
        self.lbl_line_status = QLabel("🟢 DETECTED")
        self.lbl_line_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        box_line.addWidget(self.lbl_crit_line)
        box_line.addStretch()
        box_line.addWidget(self.lbl_line_status)

        self.combo_crit_line = QComboBox()
        self.combo_crit_line.setFont(QFont("Segoe UI", 10))
        self.combo_crit_line.setMinimumHeight(36)
        self.lbl_line_msg = QLabel("Status message...")
        self.lbl_line_msg.setFont(QFont("Segoe UI", 8))

        map_layout.addLayout(box_line)
        map_layout.addWidget(self.combo_crit_line)
        map_layout.addWidget(self.lbl_line_msg)

        # 5b. Second Critical Transmission Line Dropdown (for N-2 Line Trip)
        self.lbl_crit_line_2 = QLabel("5b. Second Critical Transmission Line (Manual Selection for N-2 Line Trip):")
        self.combo_crit_line_2 = QComboBox()
        self.combo_crit_line_2.setFont(QFont("Segoe UI", 10))
        self.combo_crit_line_2.setMinimumHeight(36)

        map_layout.addWidget(self.lbl_crit_line_2)
        map_layout.addWidget(self.combo_crit_line_2)

        layout.addWidget(self.card_mapper)

        # 2. Hybrid Load & Dynamic Simulation Settings Card
        self.card_load = QFrame()
        load_layout = QVBoxLayout(self.card_load)
        load_layout.setSpacing(12)

        self.title_load = QLabel("2. Operation Scenarios & Dynamic Simulation Settings:")
        self.title_load.setFont(QFont("Segoe UI", 11, QFont.Bold))

        box_scen = QHBoxLayout()
        self.lbl_scen_title = QLabel("6. Operation Scenarios ('Peak Load'/'WBP' vs 'Low Load'/'LWBP'):")
        self.lbl_scen_status = QLabel("🟢 DETECTED")
        self.lbl_scen_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        box_scen.addWidget(self.lbl_scen_title)
        box_scen.addStretch()
        box_scen.addWidget(self.lbl_scen_status)

        self.lbl_scen_msg = QLabel("Status message...")
        self.lbl_scen_msg.setFont(QFont("Segoe UI", 8))

        self.lbl_peak_scen = QLabel("Peak Load Operation Scenario (WBP / Maximum Load):")
        self.combo_peak_scen = QComboBox()
        self.combo_peak_scen.setFont(QFont("Segoe UI", 10))
        self.combo_peak_scen.setMinimumHeight(36)
        self.combo_peak_scen.currentTextChanged.connect(self.on_scenario_dropdown_changed)

        self.lbl_low_scen = QLabel("Low Load Operation Scenario (LWBP / Off-Peak Load):")
        self.combo_low_scen = QComboBox()
        self.combo_low_scen.setFont(QFont("Segoe UI", 10))
        self.combo_low_scen.setMinimumHeight(36)
        self.combo_low_scen.currentTextChanged.connect(self.on_scenario_dropdown_changed)

        self.lbl_low_ratio = QLabel("Low Load Ratio (% of Peak Load Fallback):")
        self.spin_low_ratio = QDoubleSpinBox()
        self.spin_low_ratio.setFont(QFont("Segoe UI", 10))
        self.spin_low_ratio.setMinimumHeight(36)
        self.spin_low_ratio.setRange(30.0, 90.0)
        self.spin_low_ratio.setValue(60.0)
        self.spin_low_ratio.setSuffix(" %")

        self.lbl_sim_stop_time = QLabel("Dynamic RMS Simulation Stop Time (tstop in seconds):")
        self.spin_sim_stop_time = QDoubleSpinBox()
        self.spin_sim_stop_time.setFont(QFont("Segoe UI", 10))
        self.spin_sim_stop_time.setMinimumHeight(36)
        self.spin_sim_stop_time.setRange(1.5, 120.0)
        self.spin_sim_stop_time.setSingleStep(1.0)
        self.spin_sim_stop_time.setDecimals(1)
        self.spin_sim_stop_time.setValue(5.0)
        self.spin_sim_stop_time.setSuffix(" s")

        load_layout.addWidget(self.title_load)
        load_layout.addLayout(box_scen)
        load_layout.addWidget(self.lbl_scen_msg)
        load_layout.addWidget(self.lbl_peak_scen)
        load_layout.addWidget(self.combo_peak_scen)
        load_layout.addWidget(self.lbl_low_scen)
        load_layout.addWidget(self.combo_low_scen)
        load_layout.addWidget(self.lbl_low_ratio)
        load_layout.addWidget(self.spin_low_ratio)
        load_layout.addWidget(self.lbl_sim_stop_time)
        load_layout.addWidget(self.spin_sim_stop_time)
        layout.addWidget(self.card_load)

        # 3. Batch Launcher Card
        self.card_run = QFrame()
        run_layout = QVBoxLayout(self.card_run)
        run_layout.setSpacing(12)

        self.btn_run_22 = QPushButton("🚀 Execute All 26 Impact Assessment Scenarios")
        self.btn_run_22.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_run_22.setMinimumHeight(46)
        self.btn_run_22.clicked.connect(self.run_22_scenarios)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(22)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.lbl_status_log = QLabel("Status: Ready to execute 26 scenarios.")
        self.lbl_status_log.setFont(QFont("Segoe UI", 9))

        run_layout.addWidget(self.btn_run_22)
        run_layout.addWidget(self.progress_bar)
        run_layout.addWidget(self.lbl_status_log)
        layout.addWidget(self.card_run)

        layout.addStretch()
        self.apply_styles()

    def update_badge(self, label_status: QLabel, label_msg: QLabel, is_detected: bool, msg: str):
        label_msg.setText(msg)
        if is_detected:
            label_status.setText("🟢 DETECTED")
            label_status.setStyleSheet("color: #38A169; font-weight: bold;" if self.is_dark else "color: #15803D; font-weight: bold;")
            label_msg.setStyleSheet("color: #38BDF8;" if self.is_dark else "color: #0284C7;")
        else:
            label_status.setText("⚠️ NOT DETECTED (MANUAL FALLBACK)")
            label_status.setStyleSheet("color: #DD6B20; font-weight: bold;" if self.is_dark else "color: #C2410C; font-weight: bold;")
            label_msg.setStyleSheet("color: #CBD5E1;" if self.is_dark else "color: #475569;")

    def refresh_element_mapping(self):
        """Executes 5-point smart auto-detection and populates status badges."""
        # Reset manual overrides when refreshing from project
        self.connector.user_selected_peak_scen = None
        self.connector.user_selected_low_scen = None

        grid = self.connector.get_grid_elements()
        gens = grid.get("generators", [])
        buses = grid.get("buses", [])
        loads = grid.get("loads_list", [])
        lines = grid.get("lines", [])
        scenarios = grid.get("scenarios", [])

        auto_targets = self.connector.auto_detect_5_targets()

        self.combo_smr.clear()
        self.combo_pcc_bus.clear()
        self.combo_non_smr.clear()
        self.combo_big_load.clear()
        self.combo_crit_line.clear()
        self.combo_crit_line_2.clear()

        self.combo_peak_scen.blockSignals(True)
        self.combo_low_scen.blockSignals(True)
        self.combo_peak_scen.clear()
        self.combo_low_scen.clear()

        if gens:
            self.combo_smr.addItems(gens)
            self.combo_non_smr.addItems(gens)
            if auto_targets["smr_gen"] in gens:
                self.combo_smr.setCurrentText(auto_targets["smr_gen"])
            if auto_targets["largest_non_smr_gen"] in gens:
                self.combo_non_smr.setCurrentText(auto_targets["largest_non_smr_gen"])
        else:
            self.combo_smr.addItem(auto_targets["smr_gen"])
            self.combo_non_smr.addItem(auto_targets["largest_non_smr_gen"])

        if buses:
            self.combo_pcc_bus.addItems(buses)
            if auto_targets.get("pcc_bus") in buses:
                self.combo_pcc_bus.setCurrentText(auto_targets["pcc_bus"])
        else:
            self.combo_pcc_bus.addItem(auto_targets.get("pcc_bus", "Air Anyir"))

        if loads:
            self.combo_big_load.addItems(loads)
            if auto_targets["biggest_load"] in loads:
                self.combo_big_load.setCurrentText(auto_targets["biggest_load"])
        else:
            self.combo_big_load.addItem(auto_targets["biggest_load"])

        if lines:
            self.combo_crit_line.addItems(lines)
            self.combo_crit_line_2.addItems(lines)
            if auto_targets["critical_line"] in lines:
                self.combo_crit_line.setCurrentText(auto_targets["critical_line"])
            # Default second critical line to another distinct line if available
            first_line = self.combo_crit_line.currentText()
            second_line = next((l for l in lines if l != first_line), first_line)
            if second_line in lines:
                self.combo_crit_line_2.setCurrentText(second_line)
        else:
            self.combo_crit_line.addItem(auto_targets["critical_line"])
            self.combo_crit_line_2.addItem(auto_targets["critical_line"])

        fallback_opt = "[None / Use % Load Scaling Fallback]"
        scen_items = list(scenarios) if scenarios else []
        for auto_s in (auto_targets.get("peak_scenario"), auto_targets.get("low_scenario")):
            if auto_s and auto_s not in scen_items and auto_targets.get("scenarios_detected"):
                scen_items.append(auto_s)
        if fallback_opt not in scen_items:
            scen_items.append(fallback_opt)

        self.combo_peak_scen.addItems(scen_items)
        self.combo_low_scen.addItems(scen_items)

        if auto_targets.get("scenarios_detected") and auto_targets.get("peak_scenario") in scen_items:
            self.combo_peak_scen.setCurrentText(auto_targets["peak_scenario"])
        else:
            self.combo_peak_scen.setCurrentText(fallback_opt)

        if auto_targets.get("scenarios_detected") and auto_targets.get("low_scenario") in scen_items:
            self.combo_low_scen.setCurrentText(auto_targets["low_scenario"])
        else:
            self.combo_low_scen.setCurrentText(fallback_opt)

        self.combo_peak_scen.blockSignals(False)
        self.combo_low_scen.blockSignals(False)

        self.update_badge(self.lbl_smr_status, self.lbl_smr_msg, auto_targets["smr_detected"], auto_targets["smr_msg"])
        self.update_badge(self.lbl_pcc_status, self.lbl_pcc_msg, auto_targets.get("pcc_detected", True), auto_targets.get("pcc_msg", "Detected PCC Substation Busbar"))
        self.update_badge(self.lbl_non_smr_status, self.lbl_non_smr_msg, auto_targets["non_smr_detected"], auto_targets["non_smr_msg"])
        self.update_badge(self.lbl_load_status, self.lbl_load_msg, auto_targets["load_detected"], auto_targets["load_msg"])
        self.update_badge(self.lbl_line_status, self.lbl_line_msg, auto_targets["line_detected"], auto_targets["line_msg"])
        self.update_badge(self.lbl_scen_status, self.lbl_scen_msg, auto_targets["scenarios_detected"], auto_targets["scen_msg"])

        self.elements_loaded = True

    def on_scenario_dropdown_changed(self, _text: str = ""):
        """Updates connector scenario bindings and status badge when user manually selects a scenario."""
        peak_sel = self.combo_peak_scen.currentText()
        low_sel = self.combo_low_scen.currentText()
        if not peak_sel and not low_sel:
            return
        self.connector.set_selected_scenarios(peak_sel, low_sel)
        using_native = not (peak_sel.startswith("[None") and low_sel.startswith("[None"))
        if using_native:
            self.update_badge(
                self.lbl_scen_status,
                self.lbl_scen_msg,
                True,
                f"Active Operation Scenarios: Peak='{peak_sel}' | Low='{low_sel}'"
            )
        else:
            self.update_badge(
                self.lbl_scen_status,
                self.lbl_scen_msg,
                False,
                "Manual Fallback Active (Using Percentage Scaling Fallback 100% Peak / Low Ratio %)"
            )

    def run_22_scenarios(self):
        if not self.elements_loaded:
            self.refresh_element_mapping()

        if not self.connector.is_connected:
            reply = QMessageBox.question(
                self, 
                "PowerFactory Connection Notice", 
                "DIgSILENT PowerFactory live API is not currently connected.\n\n"
                "Would you like to execute the 26-Scenario Assessment in Grid Simulation Mode?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply != QMessageBox.Yes:
                return

        peak_scen_sel = self.combo_peak_scen.currentText()
        low_scen_sel = self.combo_low_scen.currentText()
        self.connector.set_selected_scenarios(peak_scen_sel, low_scen_sel)

        mapping = {
            "smr_gen": self.combo_smr.currentText(),
            "pcc_bus": self.combo_pcc_bus.currentText(),
            "largest_non_smr_gen": self.combo_non_smr.currentText(),
            "biggest_load": self.combo_big_load.currentText(),
            "critical_line": self.combo_crit_line.currentText(),
            "critical_line_2": self.combo_crit_line_2.currentText(),
            "peak_scenario": peak_scen_sel,
            "low_scenario": low_scen_sel
        }

        low_ratio = self.spin_low_ratio.value() / 100.0
        sim_stop_time_sec = float(self.spin_sim_stop_time.value())

        def update_progress(pct: int, msg: str):
            self.progress_bar.setValue(pct)
            self.lbl_status_log.setText(f"Status: [{pct}%] {msg}")
            QApplication.processEvents()

        results = self.batch_runner.run_all_22_scenarios(
            mapping,
            low_ratio,
            update_progress,
            sim_duration_sec=sim_stop_time_sec
        )
        self.latest_batch_results = results

        main_win = self.window()
        if hasattr(main_win, "dashboard_page"):
            main_win.dashboard_page.set_batch_results(results)

        QMessageBox.information(
            self, 
            "Batch Assessment Complete", 
            f"✅ All {results['total_count']} Assessment Scenarios Executed Successfully!\n\n"
            f"• Project: {results['project_name']}\n"
            f"• Fault PCC Bus: {mapping['pcc_bus']}\n"
            f"• Dynamic RMS Stop Time: {sim_stop_time_sec:.1f} s\n"
            f"• Total Scenarios: {results['total_count']}\n"
            f"• ESDM Compliant: {results['passed_count']} / {results['total_count']}\n\n"
            f"Navigate to 'Step 3: Visual Dashboard' to inspect the Master Compliance Matrix & Comparative Charts!"
        )

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self.apply_styles()

    def apply_styles(self):
        cards = [self.card_mapper, self.card_load, self.card_run]
        titles = [self.title_mapper, self.title_load]
        sublabels = [
            self.lbl_smr, self.lbl_pcc, self.lbl_non_smr, self.lbl_big_load,
            self.lbl_crit_line, self.lbl_crit_line_2, self.lbl_scen_title,
            self.lbl_peak_scen, self.lbl_low_scen,
            self.lbl_low_ratio, self.lbl_sim_stop_time
        ]
        combos = [
            self.combo_smr, self.combo_pcc_bus, self.combo_non_smr, self.combo_big_load,
            self.combo_crit_line, self.combo_crit_line_2, self.combo_peak_scen, self.combo_low_scen
        ]

        if self.is_dark:
            self.setStyleSheet("QScrollArea { border: none; background-color: #0B0F19; }")
            self.main_content.setStyleSheet("background-color: #0B0F19;")
            self.header.setStyleSheet("color: #F8FAFC;")
            self.desc.setStyleSheet("color: #94A3B8;")

            for c in cards:
                c.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 20px;")
            for t in titles:
                t.setStyleSheet("color: #38BDF8;")
            for s in sublabels:
                s.setStyleSheet("color: #F8FAFC; font-weight: bold; font-size: 11px;")

            combo_style = (
                "QComboBox { background-color: #0F172A; color: #F8FAFC; border: 1px solid #475569; border-radius: 6px; padding: 6px 12px; }"
                "QComboBox QAbstractItemView { background-color: #0F172A; color: #F8FAFC; selection-background-color: #0284C7; selection-color: #FFFFFF; border: 1px solid #334155; border-radius: 6px; outline: 0px; padding: 4px; }"
                "QComboBox QAbstractItemView::item { min-height: 26px; padding: 4px 8px; color: #F8FAFC; background-color: #0F172A; }"
                "QComboBox QAbstractItemView::item:selected { background-color: #0284C7; color: #FFFFFF; }"
                "QComboBox QAbstractItemView::item:hover { background-color: #1E293B; color: #F8FAFC; }"
            )
            for cb in combos:
                cb.setStyleSheet(combo_style)
            spin_style_dark = "background-color: #0F172A; color: #F8FAFC; border: 1px solid #475569; border-radius: 6px; padding: 6px 12px;"
            self.spin_low_ratio.setStyleSheet(spin_style_dark)
            self.spin_sim_stop_time.setStyleSheet(spin_style_dark)

            self.btn_run_22.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 10px;")
            self.lbl_status_log.setStyleSheet("color: #94A3B8;")
        else:
            self.setStyleSheet("QScrollArea { border: none; background-color: #F8FAFC; }")
            self.main_content.setStyleSheet("background-color: #F8FAFC;")
            self.header.setStyleSheet("color: #0F172A;")
            self.desc.setStyleSheet("color: #475569;")

            for c in cards:
                c.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 20px;")
            for t in titles:
                t.setStyleSheet("color: #0284C7;")
            for s in sublabels:
                s.setStyleSheet("color: #0F172A; font-weight: bold; font-size: 11px;")

            combo_style = (
                "QComboBox { background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; }"
                "QComboBox QAbstractItemView { background-color: #FFFFFF; color: #0F172A; selection-background-color: #0284C7; selection-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; outline: 0px; padding: 4px; }"
                "QComboBox QAbstractItemView::item { min-height: 26px; padding: 4px 8px; color: #0F172A; background-color: #FFFFFF; }"
                "QComboBox QAbstractItemView::item:selected { background-color: #0284C7; color: #FFFFFF; }"
                "QComboBox QAbstractItemView::item:hover { background-color: #E2E8F0; color: #0F172A; }"
            )
            for cb in combos:
                cb.setStyleSheet(combo_style)
            spin_style_light = "background-color: #F8FAFC; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px;"
            self.spin_low_ratio.setStyleSheet(spin_style_light)
            self.spin_sim_stop_time.setStyleSheet(spin_style_light)

            self.btn_run_22.setStyleSheet("background-color: #0284C7; color: white; border: none; border-radius: 6px; padding: 10px;")
            self.lbl_status_log.setStyleSheet("color: #475569;")
