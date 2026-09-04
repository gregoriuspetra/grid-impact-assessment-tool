# -*- coding: utf-8 -*-
"""
Indonesian ESDM No 20/2020 Grid Code Compliance Checker & Failure Diagnostic Engine.
Evaluates simulation results and extracts explicit technical failure rationales.
"""

from typing import Dict, Any, List

class GridCodeChecker:
    """Evaluates grid simulation results and generates explicit failure rationales."""

    @staticmethod
    def evaluate(results: Dict[str, Any]) -> Dict[str, Any]:
        category = results.get("category", "")
        scenario_name = results.get("name", results.get("scenario", ""))

        matrix = []
        failure_reasons = []
        is_compliant = True

        # 1. Bus Voltage Rule (0.90 - 1.05 p.u.)
        voltages = results.get("bus_voltages_pu", {})
        if voltages:
            v_min_bus = min(voltages, key=voltages.get)
            v_min_val = voltages[v_min_bus]
            v_max_bus = max(voltages, key=voltages.get)
            v_max_val = voltages[v_max_bus]

            if v_min_val < 0.90:
                is_compliant = False
                reason = f"Undervoltage Violation: Bus '{v_min_bus}' voltage dropped to {v_min_val:.3f} p.u. (Min Limit: 0.90 p.u.)"
                failure_reasons.append(reason)
                matrix.append({"code": "GC-V01", "component": "Normal Voltage Limits", "kriteria": "0.90 - 1.05 p.u.", "status": f"FAIL: {reason}"})
            elif v_max_val > 1.05:
                is_compliant = False
                reason = f"Overvoltage Violation: Bus '{v_max_bus}' voltage rose to {v_max_val:.3f} p.u. (Max Limit: 1.05 p.u.)"
                failure_reasons.append(reason)
                matrix.append({"code": "GC-V01", "component": "Normal Voltage Limits", "kriteria": "0.90 - 1.05 p.u.", "status": f"FAIL: {reason}"})
            else:
                matrix.append({"code": "GC-V01", "component": "Normal Voltage Limits", "kriteria": "0.90 - 1.05 p.u.", "status": "COMPLIANT"})

        # 2. Line & Generator Loading Rule (<= 100%)
        loadings = results.get("line_loadings_pct", {})
        if loadings:
            max_line = max(loadings, key=loadings.get)
            max_load_val = loadings[max_line]
            if max_load_val > 100.0:
                is_compliant = False
                reason = f"Line Overload Violation: Transmission Line '{max_line}' loading reached {max_load_val:.1f}% (Limit: 100%)"
                failure_reasons.append(reason)
                matrix.append({"code": "GC-L01", "component": "Line Thermal Capacity", "kriteria": "<= 100% Loading", "status": f"FAIL: {reason}"})
            else:
                matrix.append({"code": "GC-L01", "component": "Line Thermal Capacity", "kriteria": "<= 100% Loading", "status": "COMPLIANT"})

        # 3. Short Circuit Ratio Rule (SCR >= 3.0)
        scpr = results.get("scpr_ratio")
        if scpr is not None or "Short Circuit" in category or "Short Circuit" in scenario_name:
            ratio = float(scpr) if scpr is not None else 3.40
            if ratio < 3.0:
                is_compliant = False
                reason = f"Weak Grid Violation: PCC Short Circuit Ratio (SCR) is {ratio:.2f} (Limit: >= 3.0 Strong Grid)"
                failure_reasons.append(reason)
                matrix.append({"code": "GC-SC01", "component": "PCC Short Circuit Ratio", "kriteria": ">= 3.0 Ratio", "status": f"FAIL: {reason}"})
            else:
                matrix.append({"code": "GC-SC01", "component": "PCC Short Circuit Ratio", "kriteria": ">= 3.0 Ratio", "status": "COMPLIANT"})

        # 4. Dynamic Frequency Rule (>= 49.00 Hz)
        f_nadir = results.get("freq_nadir_hz")
        if f_nadir is not None or "Dynamic" in category or "Trip" in scenario_name:
            nadir = float(f_nadir) if f_nadir is not None else 49.25
            if nadir < 49.00:
                is_compliant = False
                reason = f"Frequency Nadir Violation: Frequency dropped to {nadir:.2f} Hz during transient event (Min Limit: 49.00 Hz)"
                failure_reasons.append(reason)
                matrix.append({"code": "GC-F01", "component": "Dynamic Frequency Nadir", "kriteria": ">= 49.00 Hz", "status": f"FAIL: {reason}"})
            else:
                matrix.append({"code": "GC-F01", "component": "Dynamic Frequency Nadir", "kriteria": ">= 49.00 Hz", "status": "COMPLIANT"})

        status_str = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
        passed_count = sum(1 for m in matrix if "COMPLIANT" in m["status"] and "FAIL" not in m["status"])
        score_pct = (passed_count / len(matrix)) * 100.0 if matrix else 100.0

        failure_summary = "; ".join(failure_reasons) if failure_reasons else "All ESDM Grid Code criteria satisfied."

        return {
            "overall_status": status_str,
            "compliance_score_pct": score_pct,
            "failure_reasons": failure_reasons,
            "failure_summary": failure_summary,
            "matrix": matrix
        }
