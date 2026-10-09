# Argus — Pitch Script
### AI-Powered PCB Hardware Validator

---

## Opening Hook (30 sec)

> "When a circuit board fails on the manufacturing floor, engineers spend hours — sometimes days — reading error logs, cross-checking schematics, and hunting for the defect under a microscope. We built Argus to do that in seconds."

---

## The Problem (45 sec)

PCB hardware validation today is:

- **Manual** — engineers eyeball boards and logs one by one
- **Slow** — a single defect diagnosis can take hours
- **Expensive** — hardware failures caught late in production cost 10–100× more to fix
- **Not scalable** — skilled PCB engineers are a limited, expensive resource

---

## What Argus Does (1 min)

**One upload. Four AI agents. One diagnosis.**

Here's the flow — it's dead simple:

```
User uploads a photo of their broken circuit board
              ↓
   ┌──────────────────────────────────────────┐
   │         4 AI Agents run in parallel       │
   │                                           │
   │  Agent 1 → Reads the error log           │
   │  Agent 2 → Checks spec compliance        │
   │  Agent 3 → Maps suspect areas on board   │
   │  Agent 4 → Visually inspects the defect  │
   └──────────────────────────────────────────┘
              ↓
   Root cause + exact defect location
   + step-by-step fix — in seconds
```

All four agents run in parallel using **Gemma 4**, Google's latest model, and hand their findings off to a final **Spec Resolver** that ties everything together into a single, actionable diagnosis.

---

## What's Built (Honest Status)

| Layer | Status |
|---|---|
| ✅ **Frontend** | Complete — live UI with agent pipeline visualization, image comparison viewer, bounding box overlays, diagnosis dashboard |
| 🔧 **Backend** | In progress — FastAPI orchestration layer, multi-agent pipeline, OpenCV diff engine |
| 🤖 **AI Agents** | In progress — Gemma 4 integration, prompt engineering, parallel fan-out |

**The frontend is fully functional and demo-able right now.** The agent pipeline runs end-to-end in offline/demo mode — you can see the full user experience live.

---

## Live Demo Flow (2 min)

1. **Open Argus** at `localhost:5173`
2. **Drop a circuit board image** into the upload zone — it auto-classifies the file
3. Watch the **agent pipeline animate** in real time:
   - Agent 1 lights up → Error Analyzer reads the log
   - Agents 2 & 3 fire **simultaneously** → Spec Checker + CAD Mapper run in parallel
   - Agent 4 → Defect Inspector confirms the physical defect
   - Spec Resolver → Final root cause + resolution steps
4. See the **annotated board image** with defect bounding boxes highlighted
5. Read the **Diagnosis Dashboard** — root cause, impact, and fix in plain English

---

## Why Gemma 4

- **On-device capable** — can run at the edge on factory hardware, no cloud dependency
- **Multimodal** — handles both the error log (text) and board image (vision) natively
- **Fast** — parallel agent execution keeps total latency low
- **Open** — no vendor lock-in, deployable in private factory environments

---

## The Opportunity

- Global PCB market: **$75B+** and growing
- Hardware defect detection is still largely manual
- Every automotive, aerospace, and consumer electronics manufacturer needs this
- No competitor today combines multi-agent AI + visual inspection + spec compliance in one tool

---

## Ask

We are looking for:
- **Early design partners** — manufacturers willing to test with real boards
- **Compute / API credits** — to scale the Gemma 4 backend
- **Feedback** — on the demo and the workflow

---

## One Line

> *Argus turns a broken circuit board photo into a root-cause diagnosis and fix plan — in seconds, not hours.*
