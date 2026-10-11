# Niriksha Lab — Pitch Strategy & Architecture

### 1. Market Opportunity: "Disrupting Inefficiencies in Hardware Validation"

While software development has achieved continuous automation through CI/CD pipelines, hardware verification remains largely manual, fragmented, and slow.

* **Market Size (TAM):** In high-tech hardware and embedded electronics manufacturing, **30% to 40% of total R&D cycle time and budget is spent purely on validation and testing**. Verification delays directly translate to delayed Time-to-Market and substantial opportunity cost.
* **The Core Problem:**
  * Software failures point directly to the line of offending code.
  * Hardware failures output raw textual logs (e.g. bus arbitration failures, AER errors). Engineers must manually cross-reference cryptic log codes against schematic layouts (CAD images), microscopic physical PCB photos, and hundreds of pages of technical specification PDFs (IPC, JEDEC, PCIe).
  * **Data is siloed across 4 dimensions (text, schematics, physical photos, spec PDFs)**, creating weeks of diagnostic bottlenecks for engineering teams.
* **The Solution:** A multimodal, multi-agent AI pipeline powered by Gemma/Gemini that correlates all 4 data dimensions in seconds.

---

### 2. Multi-Agent Architecture (Input ➡️ Agents ➡️ Output)

A cascading relay of specialized agents progressively narrows down root causes:

**Input Setup:**
1. **Error Log:** e.g., `[ERROR] I2C Bus Arbitration Lost - SDA line held LOW. Error Code: 0x08`
2. **Specification Document:** IPC-2221B / Standard Datasheet PDF
3. **CAD Schematic / Design Image:** Board trace layout and routing capture
4. **Physical Tested PCB Image:** Optical camera inspection photo of the board under test

**Agent Workflow:**

* **Agent 1: Symptom Analyzer**
  * Parses error logs and telemetry to isolate suspect nets and candidate fault modes.
* **Agent 2A: Spec Precheck (Parallel)**
  * Evaluates electrical rules, clearances, and isolation requirements from specification documents.
* **Agent 2B: CAD Mapper (Parallel)**
  * Maps suspect components and signal nets to physical 2D regions on the design layout.
* **Agent 3: Physical Vision & Defect Inspector**
  * Inspects the tested board optical image and zooms into CAD-mapped coordinates to confirm physical defects.
* **Agent 4: Spec Resolver & Diagnosis Engine**
  * Correlates standard compliance violations with visual evidence to output the definitive root cause, system impact, and actionable rework steps.

---

### 3. Demo & UX Strategy

* **Live Pipeline Dashboard:** Visualizes the sequential activation of each agent stage.
* **Interactive Bounding Box Overlays:** Real-time visual grounding on physical and CAD images with bi-directional spec cross-referencing.
* **Comprehensive Diagnostic Report:** Complete root cause, impact assessment, and step-by-step engineering resolution instructions.
