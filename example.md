# Niriksha Lab — PCB Defect Analysis Reference Scenario

### 1. Dataset Reference: DeepPCB & Real Arduino Hardware

The reference datasets provide paired template and tested boards with ground-truth coordinates:

* **Image Pairs:**
  1. **Circuit Design Image (Template):** Defect-free reference CAD / Gerber layer.
  2. **Circuit Physical Image (Tested):** Optical camera image showing the manufactured PCB under test.
  3. **Defect Types:** Open circuit, Short circuit, Mousebite, Spur, Pin-hole, and Spurious Copper with bounding box coordinates `[x1, y1, x2, y2]`.

---

### 2. Multi-Agent Verification Flow (Short-Circuit Case Study)

#### 📥 Inputs
1. **Error Code / Log:** `[ERROR] I2C Bus Arbitration Lost - SDA line held LOW. Error Code: 0x08`
2. **Specification Document:** `IPC-2221B Section 6.1 (Minimum Electrical Clearance)`
3. **Design Image (Template):** Arduino Uno CAD layer with I2C trace pairs.
4. **Tested Image (Tested Board):** Arduino Uno prototype photo with residual copper defect.

#### 🤖 Agent Execution Pipeline
1. **Agent 1 (Symptom Analyzer):** Parses error log `0x08` and flags a high probability of a physical short between SDA and GND.
2. **Agent 2A (Spec Precheck):** Extracts rule `IPC-2221B Sec 6.1` requiring $\ge 0.10\,\text{mm}$ conductor clearance.
3. **Agent 2B (CAD Mapper):** Maps SDA / GND nets to physical design ROI coordinates `[X: 445-520, Y: 215-275]`.
4. **Agent 3 (Physical Vision):** Inspects tested board image and confirms spurious copper bridge across the clearance channel.
5. **Agent 4 (Spec Resolver):** Flags IPC compliance violation, generates root cause, and prescribes rework steps.

#### 📤 Final Diagnostic Output
* **Root Cause:** Design spacing was within specification, but residual copper from manufacturing wash/etch failure formed a conductive micro-short between SDA and GND lines, driving SDA LOW.
* **Impact:** I2C bus communication deadlock, sensor telemetry loss, and potential MCU pin overcurrent hazard.
* **Resolution:** 
  1. Micro-deburr or laser-trim copper bridge at coordinates `[445,215 → 520,275]` and re-test continuity.
  2. Audit etching wash cycle pressure and chemical concentration on fabrication line.
  3. Update automated optical inspection (AOI) minimum gap threshold parameters.
