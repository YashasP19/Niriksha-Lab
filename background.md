# Niriksha Lab — Background & System Context

### 1. Overview
Niriksha Lab (Argus) is an AI-powered multi-agent hardware validation framework that bridges the gap between hardware error logs, engineering specifications, CAD schematics, and optical PCB inspection images.

### 2. Multi-Agent Hardware Verification Flow
* **Agent 1 (Symptom Analyzer):** Parses raw hardware error logs (e.g. I2C Bus Arbitration failure, PCIe link downgrade) to identify suspect nets and components.
* **Agent 2A (Spec Precheck):** Extracts industry standards (IPC-2221B, IPC-A-600, JEDEC) to build an inspection watchlist.
* **Agent 2B (CAD Mapper):** Maps candidate nets to 2D coordinates on the design template image.
* **Agent 3 (Physical Vision):** Inspects the physical board photo and verifies actual defects (shorts, open circuits, spurious copper).
* **Agent 4 (Spec Resolver):** Synthesizes grounded root causes, compliance verdicts, and actionable rework steps.

### 3. Evaluation Criteria
* **Accuracy:** Grounded root cause and bounding box accuracy.
* **Traceability:** Explicit linking between specification rules, visual evidence, and system impact.
* **Actionability:** Clear, practical engineering remediation steps.
