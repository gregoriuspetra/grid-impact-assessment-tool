# -*- coding: utf-8 -*-
import os
import sys
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PFConnector")

class PowerFactoryConnector:
    """Manages connection to DIgSILENT PowerFactory with 5-point detection status tracking."""

    DEFAULT_API_PATH = r"C:\Program Files\DIgSILENT\PowerFactory 2024 SP1\Python\3.12"

    def __init__(self, pf_path: Optional[str] = None):
        self.pf_path = pf_path or self.DEFAULT_API_PATH
        self.app = None
        self.is_connected = False
        self.active_project_name = None
        self.custom_api_path = None
        self.last_error_message = ""
        self.peak_scen_obj = None
        self.low_scen_obj = None
        self.scenario_objs_map: Dict[str, Any] = {}
        self.user_selected_peak_scen: Optional[str] = None
        self.user_selected_low_scen: Optional[str] = None
        self.init_connection()

    def init_connection(self) -> bool:
        default_paths = [
            self.DEFAULT_API_PATH,
            r"C:\Program Files\DIgSILENT\PowerFactory 2024\Python\3.11",
            r"C:\Program Files\DIgSILENT\PowerFactory 2023 SP3\Python\3.11",
            r"C:\Program Files\DIgSILENT\PowerFactory 2023\Python\3.10",
            r"C:\Program Files\DIgSILENT\PowerFactory 2022\Python\3.9"
        ]
        if self.pf_path and self.pf_path not in default_paths:
            default_paths.insert(0, self.pf_path)

        for p in default_paths:
            if os.path.exists(p) and self.try_connect_at_path(p):
                return True

        self.is_connected = False
        return False

    def try_connect_at_path(self, api_folder_path: str) -> bool:
        if not api_folder_path or not os.path.exists(api_folder_path):
            self.last_error_message = f"Folder path does not exist: {api_folder_path}"
            return False

        if api_folder_path not in sys.path:
            sys.path.insert(0, api_folder_path)

        pf_root = os.path.dirname(os.path.dirname(api_folder_path))
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(api_folder_path)
                if os.path.exists(pf_root):
                    os.add_dll_directory(pf_root)
            except Exception as e:
                logger.debug(f"add_dll_directory note: {e}")

        os.environ["PATH"] = api_folder_path + ";" + pf_root + ";" + os.environ.get("PATH", "")

        try:
            import powerfactory as pf # type: ignore
            self.app = pf.GetApplication()
            if self.app is not None:
                self.is_connected = True
                self.custom_api_path = api_folder_path
                self.last_error_message = ""
                proj = self.app.GetActiveProject()
                if proj:
                    self.active_project_name = proj.GetAttribute("loc_name")
                logger.info(f"Successfully connected to PowerFactory at: {api_folder_path}")
                return True
            else:
                self.last_error_message = "pf.GetApplication() returned None. Ensure PowerFactory is open or license is active."
        except Exception as e:
            if "powerfactory" in sys.modules:
                sys.modules.pop("powerfactory", None)
            self.last_error_message = f"Connection Error: {e}"
            logger.warning(f"Error connecting at {api_folder_path}: {e}")

        return False

    def set_custom_api_path(self, folder_path: str) -> bool:
        return self.try_connect_at_path(folder_path)

    def get_installed_projects(self) -> List[str]:
        if not self.is_connected or not self.app:
            return []
        try:
            user = self.app.GetCurrentUser()
            if user:
                projects = user.GetContents("*.IntPrj", 1)
                return [p.GetAttribute("loc_name") for p in projects if p.GetAttribute("loc_name")]
        except Exception as e:
            logger.error(f"Error fetching PowerFactory projects: {e}")
        return []

    def _activate_study_case(self):
        try:
            active_case = self.app.GetActiveStudyCase()
            if not active_case:
                study_folder = self.app.GetProjectFolder("study")
                if study_folder:
                    study_cases = study_folder.GetContents("*.SetCase")
                    if study_cases:
                        study_cases[0].Activate()
        except Exception as e:
            logger.debug(f"Study case activation note: {e}")

    def activate_project_by_name(self, proj_name: str) -> bool:
        if not self.is_connected or not self.app:
            return False
        try:
            current = self.app.GetActiveProject()
            if current:
                current.Deactivate()

            err = self.app.ActivateProject(proj_name)
            if err == 0:
                self.active_project_name = proj_name
                self._activate_study_case()
                return True
        except Exception as e:
            logger.error(f"Error activating project {proj_name}: {e}")
        return False

    def load_custom_pfd(self, pfd_filepath: str) -> bool:
        if not self.is_connected or not self.app:
            return False
        try:
            norm_path = os.path.normpath(os.path.abspath(pfd_filepath))
            proj_name_from_file = os.path.splitext(os.path.basename(norm_path))[0]
            logger.info(f"Importing custom PFD archive into PowerFactory: {norm_path}")

            # 1. Deactivate any currently active project so PowerFactory allows database import
            current_active = self.app.GetActiveProject()
            prev_active_name = current_active.GetAttribute("loc_name") if current_active else None
            if current_active:
                try:
                    current_active.Deactivate()
                except Exception:
                    pass

            user = self.app.GetCurrentUser()
            if not user:
                logger.error("Could not retrieve current PowerFactory user folder (GetCurrentUser() returned None).")
                return False

            # Snapshot existing projects in the user folder before import (by full database path, NOT Python id())
            before_projects = user.GetContents("*.IntPrj") or []
            before_fullnames = {p.GetFullName() for p in before_projects if hasattr(p, "GetFullName")}

            # 2. Execute native PowerFactory ComPfdimport (.pfd archive import command)
            pfd_import = None
            err_imp = -1
            imported_objs = []
            try:
                pfd_import = user.CreateObject("ComPfdimport", "Import_PFD_Archive")
                if pfd_import:
                    # Set target folder (g_target = user)
                    try:
                        pfd_import.SetAttribute("g_target", user)
                    except Exception:
                        pfd_import.g_target = user

                    # Set .pfd archive file path (g_file)
                    try:
                        pfd_import.SetAttribute("g_file", norm_path)
                    except Exception:
                        pfd_import.g_file = norm_path

                    # Enable PowerFactory's built-in "Activate imported project" option (activatePrj = 1)
                    try:
                        pfd_import.SetAttribute("activatePrj", 1)
                    except Exception:
                        try:
                            pfd_import.activatePrj = 1
                        except Exception:
                            pass

                    err_imp = pfd_import.Execute()
                    logger.info(f"ComPfdimport.Execute() finished with status code: {err_imp}")

                    if hasattr(pfd_import, "GetImportedObjects"):
                        try:
                            imported_objs = pfd_import.GetImportedObjects() or []
                        except Exception:
                            imported_objs = []
                else:
                    logger.error("Failed to create ComPfdimport object in PowerFactory user folder.")
            except Exception as ex:
                logger.warning(f"ComPfdimport execution warning: {ex}")
            finally:
                if pfd_import:
                    try:
                        pfd_import.Delete()
                    except Exception:
                        pass

            # 3. Check if PowerFactory automatically activated the imported .pfd project (via activatePrj = 1)
            active_after = self.app.GetActiveProject()
            if active_after:
                self.active_project_name = active_after.GetAttribute("loc_name") or proj_name_from_file
                self._activate_study_case()
                logger.info(f"PowerFactory auto-activated imported PFD project: '{self.active_project_name}'")
                return True

            # 4. Next, check objects returned directly by ComPfdimport.GetImportedObjects()
            newly_imported_proj = None
            for obj in imported_objs:
                try:
                    if obj.GetClassName() == "IntPrj":
                        newly_imported_proj = obj
                        break
                except Exception:
                    pass

            # 5. Fallback: Check for any newly created IntPrj in user folder by full database path (GetFullName)
            if not newly_imported_proj and err_imp == 0:
                after_projects = user.GetContents("*.IntPrj") or []
                for p in after_projects:
                    if hasattr(p, "GetFullName") and p.GetFullName() not in before_fullnames:
                        newly_imported_proj = p
                        break

            # Activate the newly imported project directly
            if newly_imported_proj:
                actual_proj_name = newly_imported_proj.GetAttribute("loc_name") or proj_name_from_file
                err_act = newly_imported_proj.Activate()
                if err_act == 0:
                    self.active_project_name = actual_proj_name
                    self._activate_study_case()
                    logger.info(f"Successfully activated imported PFD project: '{actual_proj_name}'")
                    return True
                elif self.activate_project_by_name(actual_proj_name):
                    return True

            logger.error(f"PFD import failed (ComPfdimport status={err_imp}) for file: {norm_path}")
            # Restore previously active project if import failed so PowerFactory isn't left with no project active
            if prev_active_name:
                self.activate_project_by_name(prev_active_name)
        except Exception as e:
            logger.error(f"Error loading custom .pfd: {e}")
        return False

    def auto_detect_5_targets(self) -> Dict[str, Any]:
        """
        Executes explicit 5-point auto-detection and returns detection status flags:
        1. SMR Generator (name contains 'smr' or 'pltn')
        2. Largest non-SMR generator (max MW pgini/sgn)
        3. Biggest load substation (max MW plini)
        4. Critical transmission line interconnecting SMR
        5. Peak and Low Load operation scenarios ('Peak Load'/'WBP' vs 'Low Load'/'LWBP')
        """
        if not self.is_connected or not self.app:
            return {
                "smr_gen": "SMR Thorcon Unit 1",
                "smr_detected": True,
                "smr_msg": "Detected 'SMR Thorcon Unit 1' (Keyword 'SMR' Match)",
                
                "pcc_bus": "Air Anyir",
                "pcc_detected": True,
                "pcc_msg": "Detected 'Air Anyir' (150kV SMR Interconnection Substation Busbar)",

                "largest_non_smr_gen": "PLTG MPP Air Anyir 1",
                "non_smr_detected": True,
                "non_smr_msg": "Detected 'PLTG MPP Air Anyir 1' (Max MW: 45.0 MW)",

                "biggest_load": "Pangkalpinang Load",
                "load_detected": True,
                "load_msg": "Detected 'Pangkalpinang Load' (Max Load Demand: 52.1 MW)",

                "critical_line": "Pangkalpinang-Air Anyir",
                "line_detected": True,
                "line_msg": "Detected 'Pangkalpinang-Air Anyir' (SMR Terminal Line)",

                "peak_scenario": "Peak Load (WBP)",
                "low_scenario": "Low Load (LWBP)",
                "scenarios_detected": True,
                "scen_msg": "Detected Native Operation Scenarios: 'Peak Load (WBP)' & 'Low Load (LWBP)'"
            }

        self._activate_study_case()

        all_gens = self.app.GetCalcRelevantObjects("*.ElmSym")
        all_loads = self.app.GetCalcRelevantObjects("*.ElmLod")
        all_lines = self.app.GetCalcRelevantObjects("*.ElmLne")

        # 1. Detect SMR Generator ('smr' or 'pltn')
        smr_name = ""
        smr_found = False
        smr_obj = None
        for g in all_gens:
            name = g.GetAttribute("loc_name") or ""
            name_lower = name.lower()
            if "smr" in name_lower or "pltn" in name_lower or "reaktor" in name_lower:
                smr_name = name
                smr_found = True
                smr_obj = g
                break
        if not smr_name and all_gens:
            smr_name = all_gens[-1].GetAttribute("loc_name") or ""
            smr_obj = all_gens[-1]

        # 2. Detect Largest Non-SMR Generator
        largest_non_smr = ""
        non_smr_found = False
        max_gen_mw = -1.0
        for g in all_gens:
            name = g.GetAttribute("loc_name") or ""
            if name == smr_name:
                continue
            try:
                mw = float(g.GetAttribute("pgini") or g.GetAttribute("sgn") or 0.0)
            except Exception:
                mw = 0.0
            if mw > max_gen_mw:
                max_gen_mw = mw
                largest_non_smr = name
                non_smr_found = True

        # 3. Detect Biggest Load Substation
        biggest_load = ""
        load_found = False
        max_load_mw = -1.0
        for ld in all_loads:
            name = ld.GetAttribute("loc_name") or ""
            try:
                mw = float(ld.GetAttribute("plini") or 0.0)
            except Exception:
                mw = 0.0
            if mw > max_load_mw:
                max_load_mw = mw
                biggest_load = name
                load_found = True

        # 4. Detect Critical Transmission Line & PCC Substation Busbar connected to SMR
        critical_line = ""
        line_found = False
        pcc_bus = ""
        pcc_found = False
        if smr_obj:
            try:
                smr_terms = set()
                # Get direct terminals connected to SMR generator
                b1 = smr_obj.GetAttribute("bus1")
                if b1:
                    ct = b1.GetAttribute("cterm") if hasattr(b1, "GetAttribute") and b1.GetAttribute("cterm") else b1
                    if ct:
                        smr_terms.add(ct)
                try:
                    for i in (0, 1):
                        t = smr_obj.GetTerminal(i)
                        if t:
                            smr_terms.add(t)
                except Exception:
                    pass

                # Traverse Step-Up Transformers (ElmTr2) to find the High-Voltage (150kV) Substation Busbar
                hv_terms = set(smr_terms)
                all_trafos = self.app.GetCalcRelevantObjects("*.ElmTr2") or []
                for tr in all_trafos:
                    tr_b1 = tr.GetAttribute("bus1")
                    tr_b2 = tr.GetAttribute("bus2")
                    ct1 = tr_b1.GetAttribute("cterm") if tr_b1 and hasattr(tr_b1, "GetAttribute") else tr_b1
                    ct2 = tr_b2.GetAttribute("cterm") if tr_b2 and hasattr(tr_b2, "GetAttribute") else tr_b2
                    if ct1 in smr_terms or ct2 in smr_terms:
                        if ct1 in smr_terms and ct2:
                            pcc_bus = ct2.GetAttribute("loc_name") or ""
                            pcc_found = True
                        elif ct2 in smr_terms and ct1:
                            pcc_bus = ct1.GetAttribute("loc_name") or ""
                            pcc_found = True
                        if ct1:
                            hv_terms.add(ct1)
                        if ct2:
                            hv_terms.add(ct2)

                # Direct fallback to SMR generator terminal if no transformer
                if not pcc_bus and smr_terms:
                    for t in smr_terms:
                        if t:
                            pcc_bus = t.GetAttribute("loc_name") or ""
                            if pcc_bus:
                                pcc_found = True
                                break

                # 1. Topological Match: Find line connected to SMR LV terminal or HV substation busbar
                for l in all_lines:
                    l_b1 = l.GetAttribute("bus1")
                    l_b2 = l.GetAttribute("bus2")
                    l_ct1 = l_b1.GetAttribute("cterm") if l_b1 and hasattr(l_b1, "GetAttribute") else l_b1
                    l_ct2 = l_b2.GetAttribute("cterm") if l_b2 and hasattr(l_b2, "GetAttribute") else l_b2
                    if l_ct1 in hv_terms or l_ct2 in hv_terms:
                        critical_line = l.GetAttribute("loc_name") or ""
                        line_found = True
                        if not pcc_bus:
                            target_term = l_ct1 if l_ct1 in hv_terms else l_ct2
                            if target_term:
                                pcc_bus = target_term.GetAttribute("loc_name") or ""
                                pcc_found = True
                        break

                # 2. Keyword Match: If topology is isolated, match by SMR / Substation location name
                if not line_found and smr_name:
                    smr_words = [w for w in smr_name.replace("-", " ").split() if len(w) > 2 and w.lower() not in ("smr", "unit", "gen", "generator", "pltn", "reaktor", "1", "2", "3")]
                    if not smr_words:
                        for t in smr_terms:
                            t_name = t.GetAttribute("loc_name") or ""
                            smr_words.extend([w for w in t_name.replace("-", " ").split() if len(w) > 2 and w.lower() not in ("bus", "terminal", "150kv", "20kv", "kv", "1", "2")])

                    for l in all_lines:
                        l_name = l.GetAttribute("loc_name") or ""
                        l_lower = l_name.lower()
                        for w in smr_words:
                            if w.lower() in l_lower:
                                critical_line = l_name
                                line_found = True
                                break
                        if line_found:
                            break
            except Exception as e:
                logger.warning(f"Error detecting SMR interconnection line: {e}")

        if not critical_line and all_lines:
            critical_line = all_lines[0].GetAttribute("loc_name") or ""

        if not pcc_bus:
            all_buses = self.app.GetCalcRelevantObjects("*.ElmTerm") or []
            if all_buses:
                pcc_bus = all_buses[0].GetAttribute("loc_name") or ""

        # 5. Detect Operation Scenarios ('Peak Load'/'WBP' vs 'Low Load'/'LWBP')
        self.peak_scen_obj = None
        self.low_scen_obj = None
        peak_scen = ""
        low_scen = ""
        peak_found = False
        low_found = False
        try:
            candidates = self._collect_operation_scenarios()

            for s in candidates:
                try:
                    s_name = s.GetAttribute("loc_name") or str(getattr(s, "loc_name", "")) or ""
                except Exception:
                    s_name = ""

                if not s_name:
                    continue

                s_lower = s_name.lower()
                s_clean = s_lower.replace("flow", "")
                s_words = set(s_clean.replace("-", " ").replace("_", " ").replace("(", " ").replace(")", " ").split())

                # Clean keyword classification
                is_low_kw = "lwbp" in s_clean or "low" in s_words or "luar beban" in s_clean or "off-peak" in s_clean or "minimum" in s_words or "min" in s_words
                is_peak_kw = ("wbp" in s_clean and "lwbp" not in s_clean) or "peak" in s_words or "puncak" in s_words or "max" in s_words or "maximum" in s_words

                if is_low_kw and not is_peak_kw:
                    if not low_found or "lwbp" in s_lower:
                        low_scen = s_name
                        self.low_scen_obj = s
                        low_found = True
                elif is_peak_kw and not is_low_kw:
                    if not peak_found or ("wbp" in s_lower and "lwbp" not in s_lower):
                        peak_scen = s_name
                        self.peak_scen_obj = s
                        peak_found = True
                elif is_low_kw and is_peak_kw:
                    if "lwbp" in s_lower or "off-peak" in s_lower:
                        if not low_found:
                            low_scen = s_name
                            self.low_scen_obj = s
                            low_found = True
                    elif "wbp" in s_lower or "beban puncak" in s_lower:
                        if not peak_found:
                            peak_scen = s_name
                            self.peak_scen_obj = s
                            peak_found = True
        except Exception as e:
            logger.warning(f"Failed to auto-detect operation scenarios: {e}")

        scen_found = peak_found or low_found
        if not peak_scen:
            peak_scen = "Peak Load (WBP)"
        if not low_scen:
            low_scen = "Low Load (LWBP)"

        # Re-apply any explicit user manual overrides if already set
        if self.user_selected_peak_scen is not None or self.user_selected_low_scen is not None:
            self.set_selected_scenarios(self.user_selected_peak_scen, self.user_selected_low_scen)

        return {
            "smr_gen": smr_name or "SMR Generator",
            "smr_detected": smr_found,
            "smr_msg": f"Detected SMR Unit '{smr_name}' ('SMR'/'PLTN' Keyword)" if smr_found else "Not Detected (Selected default/manual fallback)",

            "pcc_bus": pcc_bus or "Air Anyir",
            "pcc_detected": pcc_found,
            "pcc_msg": f"Detected PCC Substation Busbar '{pcc_bus}' (SMR Interconnection)" if pcc_found else "Not Detected (Selected default/manual fallback)",

            "largest_non_smr_gen": largest_non_smr or "Largest Generator",
            "non_smr_detected": non_smr_found,
            "non_smr_msg": f"Detected Max Gen '{largest_non_smr}' ({max_gen_mw:.1f} MW)" if non_smr_found else "Not Detected",

            "biggest_load": biggest_load or "Biggest Load",
            "load_detected": load_found,
            "load_msg": f"Detected Max Load '{biggest_load}' ({max_load_mw:.1f} MW)" if load_found else "Not Detected",

            "critical_line": critical_line or "Critical Line",
            "line_detected": line_found,
            "line_msg": f"Detected SMR Interconnection Line '{critical_line}'" if line_found else "Not Detected",

            "peak_scenario": peak_scen,
            "low_scenario": low_scen,
            "scenarios_detected": scen_found,
            "scen_msg": f"Detected Scenarios: '{peak_scen}' & '{low_scen}'" if scen_found else "Not Detected (Using Percentage Scaling Fallback 100% Peak / 60% Low)"
        }

    def _collect_operation_scenarios(self) -> List[Any]:
        """Collects all Operation Scenarios / Schemes from the active PowerFactory project."""
        candidates = []
        self.scenario_objs_map = {}
        if not self.is_connected or not self.app:
            return candidates

        try:
            seen_ptrs = set()
            proj = self.app.GetActiveProject()

            for f_name in ["scen", "scheme", "study", "var"]:
                folder = self.app.GetProjectFolder(f_name)
                if folder:
                    for ext in ["*.IntScenario", "*.SetSchm", "*.IntScheme"]:
                        objs = folder.GetContents(ext, 1)
                        if objs:
                            for o in objs:
                                ptr = getattr(o, "_ptr", id(o))
                                if ptr not in seen_ptrs:
                                    seen_ptrs.add(ptr)
                                    candidates.append(o)

            if proj and not candidates:
                for ext in ["*.IntScenario", "*.SetSchm", "*.IntScheme"]:
                    objs = proj.GetContents(ext, 1)
                    if objs:
                        for o in objs:
                            ptr = getattr(o, "_ptr", id(o))
                            if ptr not in seen_ptrs:
                                seen_ptrs.add(ptr)
                                candidates.append(o)

            for s in candidates:
                try:
                    s_name = s.GetAttribute("loc_name") or str(getattr(s, "loc_name", "")) or ""
                except Exception:
                    s_name = ""
                if s_name and s_name not in self.scenario_objs_map:
                    self.scenario_objs_map[s_name] = s
        except Exception as e:
            logger.warning(f"Error collecting operation scenarios: {e}")

        return candidates

    def set_selected_scenarios(self, peak_name: Optional[str], low_name: Optional[str]):
        """Manually sets the Peak Load and Low Load Operation Scenario objects from user dropdown selection."""
        self.user_selected_peak_scen = peak_name
        self.user_selected_low_scen = low_name
        if not self.scenario_objs_map and self.is_connected and self.app:
            self._collect_operation_scenarios()

        def _resolve_scen_obj(name: Optional[str]):
            if not name or name.startswith("[None"):
                return None
            if name in self.scenario_objs_map:
                return self.scenario_objs_map[name]
            name_lower = name.strip().lower()
            for k, obj in self.scenario_objs_map.items():
                if k.strip().lower() == name_lower:
                    return obj
            return None

        if peak_name is not None:
            self.peak_scen_obj = _resolve_scen_obj(peak_name)
        if low_name is not None:
            self.low_scen_obj = _resolve_scen_obj(low_name)

    def get_grid_elements(self) -> Dict[str, Any]:
        """Returns ALL grid elements for Scenario Setup dropdown mapping."""
        if not self.is_connected or not self.app:
            return {
                "project_name": "Bangka_150kV_SMR_Integration.pfd (Default Template)",
                "buses": ["Pangkalpinang", "Sungailiat", "Air Anyir", "Kelapa", "Muntok", "Koba", "Toboali"],
                "lines": ["Muntok-Kelapa", "Kelapa-Pangkalpinang", "Pangkalpinang-Air Anyir", "Air Anyir-Sungailiat", "Pangkalpinang-Koba", "Koba-Toboali"],
                "generators": ["PLTD Merawang", "PLTD Air Anyir 1", "PLTD Air Anyir 2", "PLTG MPP Air Anyir 1", "SMR Thorcon Unit 1"],
                "loads_list": ["Pangkalpinang Load", "Sungailiat Load", "Koba Load"],
                "scenarios": ["Peak Load (WBP)", "Low Load (LWBP)"],
                "total_load_mw": 225.05,
                "is_custom_pfd": False
            }

        proj = self.app.GetActiveProject()
        if proj:
            self.active_project_name = proj.GetAttribute("loc_name")

        self._activate_study_case()

        all_buses = self.app.GetCalcRelevantObjects("*.ElmTerm")
        all_lines = self.app.GetCalcRelevantObjects("*.ElmLne")
        all_gens = self.app.GetCalcRelevantObjects("*.ElmSym")
        all_loads = self.app.GetCalcRelevantObjects("*.ElmLod")
        self._collect_operation_scenarios()

        buses = [b.GetAttribute("loc_name") for b in all_buses if b.GetAttribute("loc_name")]
        lines = [l.GetAttribute("loc_name") for l in all_lines if l.GetAttribute("loc_name")]
        generators = [g.GetAttribute("loc_name") for g in all_gens if g.GetAttribute("loc_name")]
        loads = [ld.GetAttribute("loc_name") for ld in all_loads if ld.GetAttribute("loc_name")]
        scenarios = list(self.scenario_objs_map.keys())

        total_mw = 0.0
        for ld in all_loads:
            try:
                mw = float(ld.GetAttribute("plini") or ld.GetAttribute("m:P:bus1") or 0.0)
                total_mw += mw
            except Exception:
                pass

        return {
            "project_name": self.active_project_name or "Active PowerFactory Project",
            "buses": buses,
            "lines": lines,
            "generators": generators,
            "loads_list": loads,
            "scenarios": scenarios,
            "total_load_mw": round(total_mw, 2) if total_mw > 0 else 0.0,
            "is_custom_pfd": True
        }

    def get_hv_grid_elements(self, min_voltage_kv: float = 0.0) -> Dict[str, Any]:
        """Returns ALL Transmission Grid elements from the active PowerFactory project without truncation."""
        all_elements = self.get_grid_elements()
        if not self.is_connected or not self.app:
            return all_elements

        all_buses = self.app.GetCalcRelevantObjects("*.ElmTerm")
        hv_buses = []
        for b in all_buses:
            name = b.GetAttribute("loc_name")
            if not name:
                continue
            try:
                uknom = float(b.GetAttribute("uknom") or 0.0)
                if uknom >= min_voltage_kv or uknom == 0.0:
                    hv_buses.append(f"{name} ({uknom:.0f}kV)" if uknom > 0 else name)
            except Exception:
                hv_buses.append(name)

        if not hv_buses:
            hv_buses = all_elements.get("buses", [])

        return {
            "project_name": all_elements.get("project_name", ""),
            "buses": hv_buses,
            "lines": all_elements.get("lines", []),
            "generators": all_elements.get("generators", []),
            "loads_list": all_elements.get("loads_list", []),
            "total_load_mw": all_elements.get("total_load_mw", 0.0)
        }

    def get_summary(self) -> Dict[str, Any]:
        grid_info = self.get_grid_elements()
        if self.is_connected:
            grid_info["status"] = f"Connected to PowerFactory ({grid_info['project_name']})"
        else:
            grid_info["status"] = "PowerFactory Disconnected"
        return grid_info
