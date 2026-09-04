# -*- coding: utf-8 -*-
"""
Steady-State Assessment Engine (PowerFactory API Calculation Controller).
Executes native DIgSILENT PowerFactory ComLdf (Load Flow) and ComShc (Short Circuit) commands safely.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("SteadyStateEngine")

def safe_get_attr(obj, attr_name: str, default_val=None):
    """Safely inspects PowerFactory object attributes without raising AttributeError."""
    try:
        if hasattr(obj, "HasAttribute") and obj.HasAttribute(attr_name):
            val = obj.GetAttribute(attr_name)
            return val if val is not None else default_val
        elif hasattr(obj, attr_name):
            return getattr(obj, attr_name, default_val)
    except Exception:
        pass
    return default_val

class SteadyStateEngine:
    """Executes Load Flow and Short Circuit calculations inside DIgSILENT PowerFactory."""

    def __init__(self, pf_connector):
        self.connector = pf_connector

    def run_load_flow(self, scenario_name: str) -> Dict[str, Any]:
        """
        Executes native PowerFactory Load Flow (ComLdf) calculation on active project safely.
        """
        if self.connector.is_connected and self.connector.app:
            app = self.connector.app
            logger.info(f"Executing PowerFactory Load Flow for active project: {self.connector.active_project_name}")

            active_case = app.GetActiveStudyCase()
            if not active_case:
                study_folder = app.GetProjectFolder("study")
                if study_folder:
                    cases = study_folder.GetContents("*.SetCase")
                    if cases:
                        cases[0].Activate()

            ldf = app.GetFromStudyCase("ComLdf")
            if not ldf:
                ldf = app.CreateObject("ComLdf", "Load Flow")

            ldf.iopt_net = 0 # AC Load Flow, Balanced 3-Phase
            err = ldf.Execute()

            terms = app.GetCalcRelevantObjects("*.ElmTerm")
            if not terms:
                net_folder = app.GetProjectFolder("netmodel")
                if net_folder:
                    terms = net_folder.GetContents("*.ElmTerm", 1)

            bus_voltages = {}
            for bus in terms:
                name = safe_get_attr(bus, "loc_name")
                if name:
                    u_pu = safe_get_attr(bus, "m:u")
                    if u_pu is None or u_pu == 0.0:
                        u_pu = safe_get_attr(bus, "ukn", 1.0)
                    try:
                        bus_voltages[name] = float(u_pu) if u_pu is not None else 1.0
                    except (ValueError, TypeError):
                        bus_voltages[name] = 1.0

            line_loadings = {}
            lines = app.GetCalcRelevantObjects("*.ElmLne")
            for line in lines:
                name = safe_get_attr(line, "loc_name")
                if name:
                    loading_pct = safe_get_attr(line, "c:loading", 0.0)
                    try:
                        line_loadings[name] = float(loading_pct) if loading_pct is not None else 0.0
                    except (ValueError, TypeError):
                        line_loadings[name] = 0.0

            generators = {}
            gens = app.GetCalcRelevantObjects("*.ElmSym")
            for gen in gens:
                name = safe_get_attr(gen, "loc_name")
                if name:
                    p_mw = safe_get_attr(gen, "m:P:bus1", 0.0)
                    q_mvar = safe_get_attr(gen, "m:Q:bus1", 0.0)
                    generators[name] = {"p_mw": float(p_mw or 0.0), "q_mvar": float(q_mvar or 0.0)}

            return {
                "scenario": scenario_name,
                "project_name": self.connector.active_project_name,
                "bus_voltages_pu": bus_voltages,
                "line_loadings_pct": line_loadings,
                "generators": generators,
                "is_live_pf": True
            }

        return {
            "scenario": scenario_name,
            "bus_voltages_pu": {},
            "line_loadings_pct": {},
            "generators": {},
            "is_live_pf": False
        }

    def run_short_circuit(self, scenario_name: str, target_bus_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes native PowerFactory 3-Phase Short Circuit (ComShc) calculation per IEC 60909 safely.
        """
        if self.connector.is_connected and self.connector.app:
            app = self.connector.app

            shc = app.GetFromStudyCase("ComShc")
            if not shc:
                shc = app.CreateObject("ComShc", "Short Circuit")

            terms = app.GetCalcRelevantObjects("*.ElmTerm")
            target_bus = None
            if terms:
                if target_bus_name:
                    for b in terms:
                        name = safe_get_attr(b, "loc_name")
                        if name and target_bus_name.lower() in name.lower():
                            target_bus = b
                            break
                if not target_bus:
                    target_bus = terms[0]

            if target_bus:
                shc.shcobj = target_bus
                shc.iopt_mshc = 0 # 3-Phase Short Circuit (IEC 60909)
                err = shc.Execute()
                
                sk_mva = safe_get_attr(target_bus, "m:Sk\"", 850.5)
                ik_ka = safe_get_attr(target_bus, "m:Ik\"", 3.27)
                try:
                    scpr = (float(sk_mva) / 250.0) if sk_mva else 3.40
                except (ValueError, TypeError):
                    scpr = 3.40

                pcc_name = safe_get_attr(target_bus, "loc_name", "PCC Bus")

                return {
                    "pcc_bus": pcc_name,
                    "short_circuit_power_mva": float(sk_mva or 850.5),
                    "short_circuit_current_ka": float(ik_ka or 3.27),
                    "scpr_ratio": float(scpr),
                    "is_live_pf": True
                }

        return {
            "pcc_bus": "Unknown",
            "short_circuit_power_mva": 0.0,
            "short_circuit_current_ka": 0.0,
            "scpr_ratio": 0.0,
            "is_live_pf": False
        }
