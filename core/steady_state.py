# -*- coding: utf-8 -*-
"""
Steady-State Assessment Engine (PowerFactory API Calculation Controller).
Executes native DIgSILENT PowerFactory ComLdf (Load Flow) and ComShc (Short Circuit) commands safely
and reads official PowerFactory summary attributes (c:GenP, c:GenQ, c:NetP, c:NetQ, c:LoadP, c:LoadQ, etc.)
and generator rated capacities (sgn/pgini) directly.
"""

import logging
import numpy as np
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

def is_low_load_scenario(scenario_name: str, load_factor: float = 1.0) -> bool:
    """Accurately checks whether scenario is Low Load without false positives from substrings like 'flow'."""
    if load_factor < 1.0:
        return True
    s_lower = scenario_name.lower().replace("flow", "")
    words = set(s_lower.replace("-", " ").replace("_", " ").replace("(", " ").replace(")", " ").split())
    return "lwbp" in s_lower or "low" in words or "off-peak" in s_lower or "minimum" in words or "min" in words


class SteadyStateEngine:
    """Executes Load Flow and Short Circuit calculations inside DIgSILENT PowerFactory."""

    def __init__(self, pf_connector):
        self.connector = pf_connector

    def _activate_scheme(self, is_low_load: bool) -> bool:
        """Activates native Peak Load (WBP) or Low Load (LWBP) Operational Scenario in PowerFactory."""
        if not self.connector or not self.connector.is_connected or not self.connector.app:
            return False
        app = self.connector.app
        try:
            user_sel = (
                getattr(self.connector, "user_selected_low_scen", None)
                if is_low_load
                else getattr(self.connector, "user_selected_peak_scen", None)
            )
            target_obj = getattr(self.connector, "low_scen_obj", None) if is_low_load else getattr(self.connector, "peak_scen_obj", None)
            
            # Inspect currently active scenario in PowerFactory
            active_scen = None
            try:
                if hasattr(app, "GetActiveScenario"):
                    active_scen = app.GetActiveScenario()
            except Exception:
                pass

            # If user explicitly chose [None / Use % Load Scaling Fallback] in the dropdown
            if user_sel and user_sel.startswith("[None"):
                if active_scen:
                    try:
                        active_scen.Deactivate()
                    except Exception:
                        pass
                return False

            if target_obj:
                try:
                    if active_scen:
                        if active_scen == target_obj:
                            logger.info(f"Target Scenario Object '{safe_get_attr(target_obj, 'loc_name')}' is already active.")
                            return True
                        else:
                            try:
                                active_scen.Deactivate()
                            except Exception:
                                pass
                    err = target_obj.Activate()
                    if err == 0:
                        logger.info(f"Successfully activated PowerFactory Scenario Object '{safe_get_attr(target_obj, 'loc_name')}'")
                        return True
                    else:
                        logger.warning(f"PowerFactory Scenario Object '{safe_get_attr(target_obj, 'loc_name')}' Activate() returned err={err}")
                except Exception as ex:
                    logger.warning(f"Error activating target_obj: {ex}")

            # If executing Peak Load and no peak scenario object exists, deactivate active scenario (e.g. Low Load) to return to Base Case
            if not is_low_load and active_scen:
                try:
                    active_scen.Deactivate()
                    logger.info(f"Deactivated scenario '{safe_get_attr(active_scen, 'loc_name')}' to revert to Base Case (Peak Load).")
                except Exception as ex:
                    logger.warning(f"Could not deactivate active scenario: {ex}")

            # Fallback by name lookup across project folders
            targets = self.connector.auto_detect_5_targets()
            target_name = user_sel or (targets.get("low_scenario") if is_low_load else targets.get("peak_scenario"))
            if not target_name or target_name.startswith("[None"):
                return False

            for f_name in ["scen", "scheme", "study", "var"]:
                folder = app.GetProjectFolder(f_name)
                if folder:
                    for ext in ["*.IntScenario", "*.SetSchm", "*.IntScheme"]:
                        objs = folder.GetContents(ext, 1) or []
                        for s in objs:
                            s_name = safe_get_attr(s, "loc_name", "")
                            if s_name and (s_name.lower() == target_name.lower() or target_name.lower() in s_name.lower() or s_name.lower() in target_name.lower()):
                                try:
                                    if active_scen and active_scen != s:
                                        try:
                                            active_scen.Deactivate()
                                        except Exception:
                                            pass
                                    err = s.Activate()
                                    if err == 0:
                                        logger.info(f"Successfully activated PowerFactory Scenario: {s_name}")
                                        return True
                                    else:
                                        logger.warning(f"Scenario {s_name} Activate() returned err={err}")
                                except Exception as ex:
                                    logger.warning(f"Could not activate scenario {s_name}: {ex}")
        except Exception as e:
            logger.warning(f"Error during scheme activation: {e}")
        return False

    def _apply_scenario_state(self, with_smr: bool, load_factor: float = 1.0, smr_name: Optional[str] = None, has_native_scenario: bool = False):
        """
        Applies scenario state with intelligent priority:
        1. Toggles SMR generator in-service / out-of-service status (with_smr) for With/Without SMR cases.
        2. If a native Operation Scenario (Peak/Low) was detected and activated (has_native_scenario=True),
           it preserves all internal generator dispatch and load levels defined within that scenario.
        3. Fallback: Only if NO native Operation Scenario exists in the project, it applies
           proportional load scaling on ElmLod using load_factor from the Scenario Mapper.
        """
        if not self.connector or not self.connector.is_connected or not self.connector.app:
            return

        app = self.connector.app
        try:
            # 1. Toggle SMR Generator Out-of-Service status for With SMR vs Without SMR comparison
            gens = app.GetCalcRelevantObjects("*.ElmSym") or []
            for g in gens:
                name = safe_get_attr(g, "loc_name", "")
                is_smr = False
                if smr_name and (name.lower() == smr_name.lower() or smr_name.lower() in name.lower() or name.lower() in smr_name.lower()):
                    is_smr = True
                elif "smr" in name.lower() or "thorcon" in name.lower() or "pltn" in name.lower():
                    is_smr = True

                if is_smr:
                    try:
                        g.SetAttribute("outserv", 0 if with_smr else 1)
                        logger.info(f"Set generator '{name}' outserv = {0 if with_smr else 1}")
                    except Exception as ex:
                        logger.warning(f"Failed setting outserv for {name}: {ex}")

            # 2. When a native Operation Scenario is active, preserve its internal dispatch and load levels
            if has_native_scenario:
                logger.info("Native PowerFactory Operation Scenario is active: preserved its internal generator dispatch and load levels without scaling.")
                return

            # 3. Fallback: Apply proportional load scaling on ElmLod only if no native scenario exists
            loads = app.GetCalcRelevantObjects("*.ElmLod") or []
            target_scale = float(load_factor)
            for ld in loads:
                try:
                    ld.SetAttribute("scale_factor", target_scale)
                except Exception:
                    pass
            logger.info(f"Fallback: No native Operation Scenario detected. Applied proportional load scaling (scale_factor={target_scale}) across {len(loads)} loads.")
        except Exception as e:
            logger.warning(f"Error applying scenario state: {e}")

    def run_load_flow(self, scenario_name: str, with_smr: bool = True, load_factor: float = 1.0, smr_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes native PowerFactory Load Flow (ComLdf) and reads official PowerFactory summary attributes:
        c:GenP, c:GenQ, c:GenS, c:NetP, c:NetQ, c:NetS, c:InterP, c:InterQ, c:LoadP, c:LoadQ, c:LoadS,
        c:LoadPnom, c:LoadQnom, c:LoadSnom, c:LoadPdiff, c:LoadQdiff, c:MotP, c:MotQ, c:MotS,
        c:LossP, c:LossQ, c:LossQnld, c:ComprQ, c:CompQ, c:GenPnom, c:GenPdiff, c:Gencos, c:Loadcos, c:Motcos
        """
        if self.connector and self.connector.is_connected and self.connector.app:
            app = self.connector.app
            logger.info(f"Executing PowerFactory Load Flow: '{scenario_name}' (With SMR: {with_smr}, Load Factor: {load_factor}, SMR: {smr_name})")

            # Activate native operational scheme (WBP vs LWBP) and apply generator/load state
            is_low = is_low_load_scenario(scenario_name, load_factor)
            activated = self._activate_scheme(is_low_load=is_low)
            self._apply_scenario_state(with_smr=with_smr, load_factor=load_factor, smr_name=smr_name, has_native_scenario=activated)

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

            # READ ALL ELEMENT OBJECTS DIRECTLY (Collect all buses in backend; visual filtering is done in dashboard_page.py)
            terms = app.GetCalcRelevantObjects("*.ElmTerm") or []
            bus_voltages = {}
            bus_voltages_kv = {}
            bus_nominal_kv = {}
            for bus in terms:
                name = safe_get_attr(bus, "loc_name")
                if name:
                    u_pu = safe_get_attr(bus, "m:u")
                    if u_pu is None or u_pu == 0.0:
                        u_pu = safe_get_attr(bus, "m:u1")
                    uknom = safe_get_attr(bus, "uknom", 150.0) or 150.0
                    u_kv = safe_get_attr(bus, "m:Ul")
                    if u_pu is not None and u_pu != 0.0:
                        bus_voltages[name] = float(u_pu)
                        bus_nominal_kv[name] = float(uknom)
                        if u_kv is not None and float(u_kv) > 0.0:
                            bus_voltages_kv[name] = round(float(u_kv), 3)
                        else:
                            bus_voltages_kv[name] = round(float(u_pu) * float(uknom), 3)

            lines = app.GetCalcRelevantObjects("*.ElmLne") or []
            line_loadings = {}
            line_losses = {}
            for line in lines:
                name = safe_get_attr(line, "loc_name")
                if name:
                    loading_pct = safe_get_attr(line, "c:loading", 0.0) or safe_get_attr(line, "m:loading", 0.0)
                    ploss_mw = safe_get_attr(line, "c:Ploss", 0.0) or safe_get_attr(line, "m:Ploss", 0.0)
                    line_loadings[name] = float(loading_pct or 0.0)
                    if ploss_mw is not None:
                        line_losses[name] = float(abs(ploss_mw))

            gens = app.GetCalcRelevantObjects("*.ElmSym") or []
            generators = {}
            installed_cap_mw = 0.0
            for gen in gens:
                name = safe_get_attr(gen, "loc_name")
                if name:
                    p_mw = safe_get_attr(gen, "m:P:bus1", 0.0) or safe_get_attr(gen, "pgini", 0.0)
                    q_mvar = safe_get_attr(gen, "m:Q:bus1", 0.0) or safe_get_attr(gen, "qgini", 0.0)
                    rated_cap = float(safe_get_attr(gen, "sgn", 0.0) or safe_get_attr(gen, "pgini", 0.0) or 0.0)
                    outserv = safe_get_attr(gen, "outserv", 0)
                    if outserv == 0:
                        installed_cap_mw += rated_cap
                    generators[name] = {"p_mw": float(p_mw or 0.0), "q_mvar": float(q_mvar or 0.0)}

            # EXTRACT OFFICIAL POWERFACTORY SUMMARY ATTRIBUTES DIRECTLY
            pf_summary = {}
            summary_objs = []
            try:
                if hasattr(app, "GetCalcRelevantObjects"):
                    summary_objs.extend(app.GetCalcRelevantObjects("*.ElmNet") or [])
                    summary_objs.extend(app.GetCalcRelevantObjects("*.ElmSummary") or [])
                    summary_objs.extend(app.GetCalcRelevantObjects("*.ElmArea") or [])
                    summary_objs.extend(app.GetCalcRelevantObjects("*.ElmZone") or [])
                if not summary_objs and hasattr(app, "GetActiveGrid"):
                    g = app.GetActiveGrid()
                    if g:
                        summary_objs.append(g)
                if not summary_objs and hasattr(app, "GetActiveProject"):
                    proj = app.GetActiveProject()
                    if proj:
                        summary_objs.append(proj)
            except Exception as ex:
                logger.debug(f"Summary object collection note: {ex}")

            summary_attrs = [
                "c:GenP", "c:GenQ", "c:GenS",
                "c:NetP", "c:NetQ", "c:NetS",
                "c:InterP", "c:InterQ",
                "c:LoadP", "c:LoadQ", "c:LoadS",
                "c:LoadPnom", "c:LoadQnom", "c:LoadSnom",
                "c:LoadPdiff", "c:LoadQdiff",
                "c:MotP", "c:MotQ", "c:MotS",
                "c:LossP", "c:LossQ",
                "c:LossQnld",
                "c:ComprQ", "c:CompQ",
                "c:GenPnom", "c:GenPdiff",
                "c:Gencos", "c:Loadcos", "c:Motcos"
            ]

            for sobj in summary_objs:
                for attr in summary_attrs:
                    if attr not in pf_summary:
                        val = safe_get_attr(sobj, attr)
                        if val is not None:
                            pf_summary[attr] = float(val)

            gen_p = pf_summary.get("c:GenP", sum(g["p_mw"] for g in generators.values()))
            gen_q = pf_summary.get("c:GenQ", sum(g["q_mvar"] for g in generators.values()))
            gen_s = pf_summary.get("c:GenS", np.sqrt(gen_p**2 + gen_q**2))

            net_p = pf_summary.get("c:NetP", 0.0)
            net_q = pf_summary.get("c:NetQ", 0.0)
            net_s = pf_summary.get("c:NetS", np.sqrt(net_p**2 + net_q**2) if (net_p != 0 or net_q != 0) else 0.0)

            inter_p = pf_summary.get("c:InterP", 0.0)
            inter_q = pf_summary.get("c:InterQ", 0.0)

            all_loads = app.GetCalcRelevantObjects("*.ElmLod") or []
            loads_dict = {}
            bus_powers = {}

            # 1. Initialize bus_powers for all ElmTerm objects
            for bus in terms:
                b_name = safe_get_attr(bus, "loc_name")
                if not b_name:
                    continue
                p_load = safe_get_attr(bus, "m:Plod")
                if p_load is None:
                    p_load = safe_get_attr(bus, "m:P:lod")
                q_load = safe_get_attr(bus, "m:Qlod")
                if q_load is None:
                    q_load = safe_get_attr(bus, "m:Q:lod")

                p_net = safe_get_attr(bus, "m:P") or safe_get_attr(bus, "m:Pnet") or safe_get_attr(bus, "m:P:bus1")
                q_net = safe_get_attr(bus, "m:Q") or safe_get_attr(bus, "m:Qnet") or safe_get_attr(bus, "m:Q:bus1")

                p_val = float(abs(p_load)) if p_load is not None else (float(abs(p_net)) if p_net is not None else 0.0)
                q_val = float(abs(q_load)) if q_load is not None else (float(abs(q_net)) if q_net is not None else 0.0)

                bus_powers[b_name] = {
                    "p_mw": round(p_val, 2),
                    "q_mvar": round(q_val, 2),
                    "p_load_mw": round(float(abs(p_load)), 2) if p_load is not None else 0.0,
                    "q_load_mvar": round(float(abs(q_load)), 2) if q_load is not None else 0.0,
                    "p_gen_mw": 0.0,
                    "q_gen_mvar": 0.0
                }

            # 2. Extract load flows directly from all ElmLod objects and associate with buses
            for ld in all_loads:
                ld_name = safe_get_attr(ld, "loc_name", "")
                p_ld = float(safe_get_attr(ld, "m:P:bus1", 0.0) or safe_get_attr(ld, "m:P", 0.0) or safe_get_attr(ld, "plini", 0.0) or 0.0)
                q_ld = float(safe_get_attr(ld, "m:Q:bus1", 0.0) or safe_get_attr(ld, "m:Q", 0.0) or safe_get_attr(ld, "qlini", 0.0) or 0.0)

                term_obj = safe_get_attr(ld, "bus1")
                term_name = ""
                if term_obj:
                    if hasattr(term_obj, "loc_name"):
                        term_name = term_obj.loc_name
                    if hasattr(term_obj, "cterm") and term_obj.cterm:
                        term_name = safe_get_attr(term_obj.cterm, "loc_name", term_name)
                    elif hasattr(term_obj, "GetParent"):
                        parent_obj = term_obj.GetParent()
                        if parent_obj and hasattr(parent_obj, "loc_name"):
                            term_name = parent_obj.loc_name

                loads_dict[ld_name] = {
                    "p_mw": round(abs(p_ld), 2),
                    "q_mvar": round(abs(q_ld), 2),
                    "bus": term_name
                }

                if term_name:
                    if term_name not in bus_powers:
                        bus_powers[term_name] = {
                            "p_mw": 0.0, "q_mvar": 0.0,
                            "p_load_mw": 0.0, "q_load_mvar": 0.0,
                            "p_gen_mw": 0.0, "q_gen_mvar": 0.0
                        }
                    bus_powers[term_name]["p_load_mw"] += round(abs(p_ld), 2)
                    bus_powers[term_name]["q_load_mvar"] += round(abs(q_ld), 2)
                    if bus_powers[term_name]["p_mw"] == 0.0:
                        bus_powers[term_name]["p_mw"] = bus_powers[term_name]["p_load_mw"]
                        bus_powers[term_name]["q_mvar"] = bus_powers[term_name]["q_load_mvar"]

            # 3. Associate generator flows with their connection bus terminals
            for gen in gens:
                term_obj = safe_get_attr(gen, "bus1")
                term_name = ""
                if term_obj:
                    if hasattr(term_obj, "loc_name"):
                        term_name = term_obj.loc_name
                    if hasattr(term_obj, "cterm") and term_obj.cterm:
                        term_name = safe_get_attr(term_obj.cterm, "loc_name", term_name)
                    elif hasattr(term_obj, "GetParent"):
                        parent_obj = term_obj.GetParent()
                        if parent_obj and hasattr(parent_obj, "loc_name"):
                            term_name = parent_obj.loc_name

                p_g = float(safe_get_attr(gen, "m:P:bus1", 0.0) or safe_get_attr(gen, "pgini", 0.0) or 0.0)
                q_g = float(safe_get_attr(gen, "m:Q:bus1", 0.0) or safe_get_attr(gen, "qgini", 0.0) or 0.0)
                if term_name and term_name in bus_powers:
                    bus_powers[term_name]["p_gen_mw"] += round(abs(p_g), 2)
                    bus_powers[term_name]["q_gen_mvar"] += round(abs(q_g), 2)
                    if bus_powers[term_name]["p_mw"] == 0.0:
                        bus_powers[term_name]["p_mw"] = bus_powers[term_name]["p_gen_mw"]
                        bus_powers[term_name]["q_mvar"] = bus_powers[term_name]["q_gen_mvar"]

            load_p = pf_summary.get("c:LoadP", sum(float(safe_get_attr(ld, "m:P:bus1", 0.0) or safe_get_attr(ld, "plini", 0.0) or 0.0) for ld in all_loads))
            load_q = pf_summary.get("c:LoadQ", sum(float(safe_get_attr(ld, "m:Q:bus1", 0.0) or safe_get_attr(ld, "qlini", 0.0) or 0.0) for ld in all_loads))
            load_s = pf_summary.get("c:LoadS", np.sqrt(load_p**2 + load_q**2))

            load_pnom = pf_summary.get("c:LoadPnom", load_p)
            load_qnom = pf_summary.get("c:LoadQnom", load_q)
            load_snom = pf_summary.get("c:LoadSnom", load_s)

            load_pdiff = pf_summary.get("c:LoadPdiff", 0.0)
            load_qdiff = pf_summary.get("c:LoadQdiff", 0.0)

            mot_p = pf_summary.get("c:MotP", 0.0)
            mot_q = pf_summary.get("c:MotQ", 0.0)
            mot_s = pf_summary.get("c:MotS", np.sqrt(mot_p**2 + mot_q**2) if (mot_p != 0 or mot_q != 0) else 0.0)

            loss_p = pf_summary.get("c:LossP", sum(line_losses.values()) if line_losses else max(0.0, gen_p - load_p))
            loss_q = pf_summary.get("c:LossQ", max(0.0, gen_q - load_q))

            loss_qnld = pf_summary.get("c:LossQnld", 0.0)
            compr_q = pf_summary.get("c:ComprQ", 0.0)
            comp_q = pf_summary.get("c:CompQ", 0.0)

            installed_cap_mw = pf_summary.get("c:GenPnom", installed_cap_mw)
            spinning_reserve = pf_summary.get("c:GenPdiff", max(0.0, installed_cap_mw - gen_p) if installed_cap_mw > 0 else 0.0)

            gencos = pf_summary.get("c:Gencos", (gen_p / gen_s) if gen_s > 0 else 0.95)
            loadcos = pf_summary.get("c:Loadcos", (load_p / load_s) if load_s > 0 else 0.95)
            motcos = pf_summary.get("c:Motcos", 0.0)

            v_vals = list(bus_voltages.values()) if bus_voltages else [1.0]
            l_vals = list(line_loadings.values()) if line_loadings else [0.0]

            return {
                "scenario": scenario_name,
                "project_name": self.connector.active_project_name,
                "bus_voltages_pu": bus_voltages,
                "bus_voltages_kv": bus_voltages_kv,
                "bus_nominal_kv": bus_nominal_kv,
                "bus_powers": bus_powers,
                "loads": loads_dict,
                "line_loadings_pct": line_loadings,
                "generators": generators,
                "min_voltage_pu": round(min(v_vals), 4),
                "max_voltage_pu": round(max(v_vals), 4),
                "max_line_loading_pct": round(max(l_vals), 1),
                "total_generation_mw": round(gen_p, 2),
                "total_generation_mvar": round(gen_q, 2),
                "total_generation_mva": round(gen_s, 2),
                "total_net_p_mw": round(net_p, 2),
                "total_net_q_mvar": round(net_q, 2),
                "total_net_s_mva": round(net_s, 2),
                "inter_area_p_mw": round(inter_p, 2),
                "inter_area_q_mvar": round(inter_q, 2),
                "total_load_mw": round(load_p, 2),
                "total_load_mvar": round(load_q, 2),
                "total_load_mva": round(load_s, 2),
                "load_pnom_mw": round(load_pnom, 2),
                "load_qnom_mvar": round(load_qnom, 2),
                "load_snom_mva": round(load_snom, 2),
                "load_pdiff_mw": round(load_pdiff, 2),
                "load_qdiff_mvar": round(load_qdiff, 2),
                "mot_p_mw": round(mot_p, 2),
                "mot_q_mvar": round(mot_q, 2),
                "mot_s_mva": round(mot_s, 2),
                "total_loss_mw": round(loss_p, 2),
                "total_loss_mvar": round(loss_q, 2),
                "loss_qnld_mvar": round(loss_qnld, 2),
                "compr_q_mvar": round(compr_q, 2),
                "comp_q_mvar": round(comp_q, 2),
                "installed_capacity_mw": round(installed_cap_mw, 2),
                "spinning_reserve_mw": round(spinning_reserve, 2),
                "gencos": round(gencos, 2),
                "loadcos": round(loadcos, 2),
                "motcos": round(motcos, 2),
                "is_live_pf": True
            }

        # Offline / Fallback execution with scenario-sensitive grid metrics
        grid_el = self.connector.get_hv_grid_elements(min_voltage_kv=100.0) if self.connector else {}
        buses = grid_el.get("buses", ["Pangkalpinang (150kV)", "Sungailiat (150kV)", "Air Anyir (150kV)", "Kelapa (150kV)", "Muntok (150kV)", "Koba (150kV)"])
        lines = grid_el.get("lines", ["Muntok-Kelapa 150kV", "Kelapa-Pangkal 150kV", "Pangkal-AirAnyir 150kV", "AirAnyir-Sungailiat 150kV"])
        gens = grid_el.get("generators", ["PLTD Merawang", "PLTD Air Anyir", "PLTG MPP Air Anyir", "SMR Thorcon Unit 1"])

        v_offset = (0.015 if with_smr else -0.012) + (0.008 if load_factor < 1.0 else -0.005)

        bus_voltages = {}
        for i, b in enumerate(buses):
            base_v = 1.012 + (abs(hash(b)) % 7) * 0.003 - 0.004
            bus_voltages[b] = round(base_v + v_offset, 4)

        line_loadings = {}
        for i, l in enumerate(lines):
            base_load = (48.0 + (abs(hash(l)) % 40) * 0.95)
            scaled_load = base_load * load_factor * (0.88 if with_smr else 1.15)
            line_loadings[l] = round(min(scaled_load, 110.0), 1)

        generators = {}
        for i, g in enumerate(gens):
            is_smr = "smr" in g.lower() or "thorcon" in g.lower() or "pltn" in g.lower()
            if is_smr:
                p = round((100.0 if load_factor >= 1.0 else 60.0) if with_smr else 0.0, 1)
                q = round((20.0 if load_factor >= 1.0 else 12.0) if with_smr else 0.0, 1)
            else:
                p = round((30.0 + (abs(hash(g)) % 85)) * load_factor * (1.20 if not with_smr else 0.90), 1)
                q = round((10.0 + (abs(hash(g)) % 25)) * load_factor, 1)
            generators[g] = {"p_mw": p, "q_mvar": q}

        v_vals = list(bus_voltages.values())
        l_vals = list(line_loadings.values())
        min_v = min(v_vals)
        max_v = max(v_vals)
        max_l = max(l_vals)
        total_loss = round(sum(l_vals) * 0.15 + (12.4 if load_factor >= 1.0 else 7.2) * (0.9 if with_smr else 1.3), 2)

        bus_powers = {}
        for b in buses:
            bp = round((35.0 + (abs(hash(b)) % 40)) * load_factor, 1)
            bq = round((10.0 + (abs(hash(b)) % 15)) * load_factor, 1)
            bus_powers[b] = {
                "p_mw": bp,
                "q_mvar": bq,
                "p_load_mw": bp,
                "q_load_mvar": bq,
                "p_gen_mw": 0.0,
                "q_gen_mvar": 0.0
            }

        return {
            "scenario": scenario_name,
            "bus_voltages_pu": bus_voltages,
            "bus_powers": bus_powers,
            "line_loadings_pct": line_loadings,
            "generators": generators,
            "min_voltage_pu": round(min_v, 4),
            "max_voltage_pu": round(max_v, 4),
            "max_line_loading_pct": round(max_l, 1),
            "total_loss_mw": total_loss,
            "is_live_pf": False
        }

    def run_short_circuit(self, scenario_name: str, with_smr: bool = True, load_factor: float = 1.0, target_bus_name: Optional[str] = None, smr_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes native PowerFactory 3-Phase Short Circuit (ComShc) calculation and reads 100% direct results.
        """
        if self.connector and self.connector.is_connected and self.connector.app:
            app = self.connector.app
            logger.info(f"Executing PowerFactory Short Circuit: '{scenario_name}' (With SMR: {with_smr}, Load Factor: {load_factor}, Target Bus: {target_bus_name}, SMR: {smr_name})")

            is_low = is_low_load_scenario(scenario_name, load_factor)
            activated = self._activate_scheme(is_low_load=is_low)
            self._apply_scenario_state(with_smr=with_smr, load_factor=load_factor, smr_name=smr_name, has_native_scenario=activated)

            shc = app.GetFromStudyCase("ComShc")
            if not shc:
                shc = app.CreateObject("ComShc", "Short Circuit")

            terms = app.GetCalcRelevantObjects("*.ElmTerm") or []
            target_bus = None
            if terms:
                if target_bus_name:
                    for b in terms:
                        name = safe_get_attr(b, "loc_name")
                        if name and (target_bus_name.lower() == name.lower() or target_bus_name.lower() in name.lower() or name.lower() in target_bus_name.lower()):
                            target_bus = b
                            break
                if not target_bus:
                    target_bus = terms[0]

            if target_bus:
                shc.shcobj = target_bus
                shc.iopt_allbus = 0  # 0 = Fault at user selected target bus (shcobj)
                shc.iopt_mshc = 0    # 3-Phase Short Circuit
                shc.iopt_method = 0  # IEC 60909 Standard Calculation
                
                # Explicitly enable thermal, peak, and breaking current calculations in PowerFactory ComShc
                for opt in ["iopt_ith", "iopt_ip", "iopt_ib", "iopt_asc"]:
                    try:
                        shc.SetAttribute(opt, 1)
                    except Exception:
                        pass

                err = shc.Execute()

                # Get nominal line-to-line voltage in kV
                uknom = float(safe_get_attr(target_bus, "uknom", 0.0) or 0.0)
                if uknom <= 0.0:
                    uknom = float(safe_get_attr(target_bus, "u0", 0.0) or safe_get_attr(target_bus, "m:u", 0.0) or 0.0)

                # READ DIRECTLY FROM POWERFACTORY OBJECT ATTRIBUTES
                # Initial symmetrical short-circuit current (kA)
                ik_ka = float(
                    safe_get_attr(target_bus, "m:Ikss", 0.0)
                    or safe_get_attr(target_bus, "m:Ik\"", 0.0)
                    or safe_get_attr(target_bus, "m:Ik", 0.0)
                    or safe_get_attr(target_bus, "m:Ip", 0.0)
                    or 0.0
                )

                # Initial symmetrical short-circuit power (MVA)
                # Official PowerFactory attribute for IEC 60909 is m:Skss
                sk_mva = float(
                    safe_get_attr(target_bus, "m:Skss", 0.0)
                    or safe_get_attr(target_bus, "m:Sk\"", 0.0)
                    or safe_get_attr(target_bus, "m:Sk", 0.0)
                    or 0.0
                )

                # If m:Skss is not populated directly by the API version, calculate via theoretical IEC formula:
                # S"k = sqrt(3) * Un * I"k
                if sk_mva <= 0.0 and ik_ka > 0.0 and uknom > 0.0:
                    sk_mva = float(np.sqrt(3.0) * uknom * ik_ka)

                # Peak short-circuit current (ip) in kA
                ip_ka = float(
                    safe_get_attr(target_bus, "m:ip", 0.0)
                    or safe_get_attr(target_bus, "m:Ip", 0.0)
                    or 0.0
                )

                # Symmetrical short-circuit breaking current (Ib) in kA
                ib_ka = float(
                    safe_get_attr(target_bus, "m:Ib", 0.0)
                    or safe_get_attr(target_bus, "m:ib", 0.0)
                    or 0.0
                )

                # Thermal equivalent short-circuit current (Ith) in kA directly from PowerFactory
                ith_ka = float(
                    safe_get_attr(target_bus, "m:Ith", 0.0)
                    or safe_get_attr(target_bus, "m:ith", 0.0)
                    or safe_get_attr(target_bus, "m:Ithr", 0.0)
                    or 0.0
                )

                # Grid R/X ratio at the fault bus
                rx_ratio = float(
                    safe_get_attr(target_bus, "m:rx", 0.0)
                    or safe_get_attr(target_bus, "m:Rx", 0.0)
                    or 0.0
                )

                # Short-circuit impedance angle (deg) directly from PowerFactory
                phi_deg = float(
                    safe_get_attr(target_bus, "m:phi", 0.0)
                    or safe_get_attr(target_bus, "m:phik", 0.0)
                    or safe_get_attr(target_bus, "m:phi_k", 0.0)
                    or 0.0
                )
                if phi_deg == 0.0 and rx_ratio > 0.0:
                    phi_deg = float(np.degrees(np.arctan(1.0 / rx_ratio)))

                # If ip or Ib were not populated by the specific PF command profile, compute via IEC 60909:
                eff_rx = rx_ratio if rx_ratio > 0.0 else 0.10
                kappa = 1.02 + 0.98 * np.exp(-3.0 * eff_rx)

                if ip_ka <= 0.0 and ik_ka > 0.0:
                    ip_ka = float(kappa * np.sqrt(2.0) * ik_ka)

                if ib_ka <= 0.0 and ik_ka > 0.0:
                    ib_ka = ik_ka

                # True IEC 60909 Thermal Equivalent Current formula: Ith = Ik'' * sqrt(m + n)
                # Where m accounts for DC component decay over fault duration Tk, and n accounts for AC decay
                if ith_ka <= 0.0 and ik_ka > 0.0:
                    tk_dur = float(safe_get_attr(shc, "Tk", 1.0) or 1.0)
                    f_hz = 50.0
                    term = 2.0 * f_hz * tk_dur * np.log(max(1.0001, kappa) - 1.0)
                    m_factor = (np.exp(2.0 * term) - 1.0) / (2.0 * term) if term != 0 else 0.0
                    m_factor = max(0.0, float(m_factor))
                    n_factor = 1.0  # far-from-generator factor per IEC 60909-0
                    ith_ka = float(ik_ka * np.sqrt(m_factor + n_factor))

                pcc_name = safe_get_attr(target_bus, "loc_name", target_bus_name or "PCC Bus")

                # Get SMR unit active / rated power capacity directly from mapped generator or keywords
                smr_mw = 100.0
                gens = app.GetCalcRelevantObjects("*.ElmSym") or []
                target_gen = None
                if smr_name:
                    for g in gens:
                        g_name = safe_get_attr(g, "loc_name", "")
                        if g_name and (smr_name.lower() == g_name.lower() or smr_name.lower() in g_name.lower() or g_name.lower() in smr_name.lower()):
                            target_gen = g
                            break
                if not target_gen:
                    for g in gens:
                        g_name = safe_get_attr(g, "loc_name", "").lower()
                        if "smr" in g_name or "thorcon" in g_name or "pltn" in g_name:
                            target_gen = g
                            break
                if target_gen:
                    try:
                        smr_mw = float(safe_get_attr(target_gen, "pgini", 0.0) or safe_get_attr(target_gen, "sgn", 0.0) or 100.0)
                        if smr_mw <= 0.0:
                            smr_mw = float(safe_get_attr(target_gen, "sgn", 100.0) or 100.0)
                    except Exception:
                        smr_mw = 100.0

                scpr = (sk_mva / smr_mw) if smr_mw > 0 and sk_mva > 0 else 0.0

                return {
                    "pcc_bus": pcc_name,
                    "short_circuit_power_mva": round(sk_mva, 2),
                    "short_circuit_current_ka": round(ik_ka, 2),
                    "peak_current_ka": round(ip_ka, 2),
                    "breaking_current_ka": round(ib_ka, 2),
                    "thermal_current_ka": round(ith_ka, 2),
                    "rx_ratio": round(rx_ratio, 3),
                    "phi_deg": round(phi_deg, 1),
                    "scpr_ratio": round(scpr, 2),
                    "is_live_pf": True
                }

        # Offline / Fallback execution with realistic short circuit parameters
        with_smr_val = "With SMR" in scenario_name or with_smr
        sk = round(1150.4 if with_smr_val else 850.5, 1)
        ik = round(4.43 if with_smr_val else 3.27, 2)
        rx = 0.10
        kappa = 1.02 + 0.98 * np.exp(-3.0 * rx)
        ip = round(kappa * np.sqrt(2.0) * ik, 2)
        ib = round(ik * 0.98 if with_smr_val else ik, 2)
        ith = round(ik, 2)
        scr = round(4.60 if with_smr_val else 3.40, 2)
        chosen_bus = target_bus_name or "Air Anyir"

        return {
            "pcc_bus": chosen_bus,
            "short_circuit_power_mva": sk,
            "short_circuit_current_ka": ik,
            "peak_current_ka": ip,
            "breaking_current_ka": ib,
            "thermal_current_ka": ith,
            "rx_ratio": rx,
            "scpr_ratio": scr,
            "is_live_pf": False
        }
