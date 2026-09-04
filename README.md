# ⚡ Grid Impact Assessment Tool
### *Collaboration between Universitas Gadjah Mada (UGM) & PT. PLN (Persero)*

Official automated software suite for conducting statutory **22-Scenario Grid Impact Assessment Studies** for integrating Small Modular Reactors (SMR), Nuclear Power Plants (PLTN), and utility-scale generating units into electrical transmission grids using **DIgSILENT PowerFactory**.

Evaluated strictly against Indonesian Electricity Grid Code Regulations (**ESDM No. 20/2020**).

---

## 🌟 Key Features

* **⚡ DIgSILENT PowerFactory C-Extension Integration:** Direct Python 3.12 API coupling supporting PowerFactory 2024 SP1 / 2023 / 2022.
* **🤖 5-Point Smart Target Auto-Detection:**
  1. *SMR Generator Unit*: Auto-detects generators matching `'SMR'` / `'PLTN'` keywords with `[DETECTED]` status tracking.
  2. *Largest Non-SMR Generator*: Auto-detects maximum MW capacity thermal/hydro unit.
  3. *Biggest Load Substation*: Auto-detects maximum MW demand load center.
  4. *Critical Transmission Line*: Auto-detects line interconnecting the SMR terminal bus.
  5. *Operation Scenarios*: Auto-detects native PowerFactory `'Peak Load'` (`WBP`) & `'Low Load'` (`LWBP`) schemes.
* **📊 22-Scenario Batch Engine:**
  * **4 Load Flow Scenarios**: Peak & Low Load (With/Without SMR).
  * **4 Short Circuit Scenarios**: 3-Phase fault power $S_k''$, fault current $I_k''$, and Short Circuit Ratio ($\text{SCR} \ge 3.0$).
  * **14 RMS Dynamic Stability Scenarios**: Frequency transients $f(t)$, PCC Voltage $V(t)$, Active Power $P(t)$, and Reactive Power $Q(t)$ overlaying 4 contingency events (*SMR Trip*, *Gen Trip*, *Load Trip*, *Line Trip N-1*).
* **📈 High-Voltage Transmission Visual Focus ($\ge 100\text{ kV}$):** Uncluttered dashboard bar charts focusing on $115\text{ kV}, 150\text{ kV}, 275\text{ kV}, 500\text{ kV}$ transmission grid corridors.
* **📄 Executive PDF Exporter:** Multi-page ReportLab PDF exporter featuring embedded 4-panel visual charts, Master Compliance Matrix, and human-readable technical narratives.
* **🌙 Dark / ☀️ Light Mode Themes:** Dynamic theme adaptation across all UI pages, tables, status banners, and notification dialogs.

---

## 🛠️ Prerequisites & Installation

1. **Python 3.12** (64-bit required for PowerFactory C-extension bindings).
2. **DIgSILENT PowerFactory 2024 SP1** (or 2023 / 2022).

Install required dependencies:
```bash
pip install -r requirements.txt
---
