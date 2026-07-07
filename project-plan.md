# Spillguard — Build Plan (Solo · 5 Days)

**Deadline:** July 11 2026, 9:00 PM PKT · **Today:** July 7 (Day 1)
**Locked decisions:** Solo dev · AMD GPU access *pending* · Polished React UI · Gemma 3 **12B**
**Companion docs:** [system-architecture.md](system-architecture.md) · [project-info.md](project-info.md) · [track3-ideas-shortlist.md](track3-ideas-shortlist.md)

---

## 🧭 The core strategy (read this first)

Your GPU isn't ready yet, so we **refuse to let that block us.** The architecture's swappable model backend means we build the *entire* product against a **`mock`** brain (Day 1) and a **`fireworks`** brain (Day 2) — real Gemma, no GPU needed. By **end of Day 3 you have a complete, working, demoable product.** AMD self-hosting then becomes a *one-env-var upgrade* (Day 4), not a dependency.

```
   Day 1        Day 2            Day 3              Day 4               Day 5
 ┌────────┐  ┌──────────┐   ┌────────────┐   ┌──────────────┐   ┌───────────────┐
 │skeleton│→ │real brain│ → │  THE DEMO  │ → │  AMD upgrade │ → │ polish+submit │
 │ (mock) │  │(fireworks│   │ React + eval│  │ self-host on │   │ README/deck/  │
 │  /scan │  │ =Gemma)  │   │ works fully │  │  MI300X +    │   │ video/submit  │
 │ works  │  │          │   │ on fallback │  │ air-gap proof│   │               │
 └────────┘  └──────────┘   └────────────┘   └──────────────┘   └───────────────┘
                                  ▲                  ▲
                        SUBMISSION-SAFE HERE   BONUS-ELIGIBLE HERE
                        (even if GPU never      ($2k AMD-hosted
                         arrives, we can ship)   Gemma unlocked)
```

**Critical-path rule (solo survival):** always keep `scan → verdict → UI` working. Build depth *after* the path is green, never before.

---

## ⚡ IMMEDIATE actions (do these TODAY, before any coding)

These unblock everything and some have multi-day approval lag:

- [ ] **A0.1** Apply for / confirm **AMD Developer Cloud access + credits** (new-member credits take 2–3 days manual approval — start the clock *now*). This is the single most important unblock.
- [ ] **A0.2** Accept the **Gemma license on Hugging Face** and generate an **HF access token** (the model is gated — needed for both Fireworks and self-hosting).
- [ ] **A0.3** Get a **Fireworks AI API key** (from your hackathon credits) — this is our "real Gemma" path until the GPU lands.
- [ ] **A0.4** Confirm local dev tooling: Python 3.11, Docker Desktop, Node 20+ (for the React build).

---

## 📅 Day-by-day plan with tasks & subtasks

### ▶️ DAY 1 (Jul 7) — Skeleton that returns a real verdict end-to-end (on `mock`)
**Goal / Definition of Done:** `curl` a pasted paragraph to `/scan` and get back a real `ALLOW/FLAG/BLOCK` JSON. No GPU, no AI yet — just the full plumbing proven.

- [ ] **T1 — Repo scaffold & tooling**
  - [ ] T1.1 Create folder structure per architecture (`app/`, `eval/`, `tests/`, `docker/`, `scripts/`, `ui/`)
  - [ ] T1.2 `requirements.txt` (fastapi, uvicorn, pydantic v2, pydantic-settings, httpx, python-dotenv), `.env.example`
  - [ ] T1.3 `app/config.py` — settings: `MODEL_BACKEND`, `MODEL_URL`, `MODEL_NAME`, thresholds
  - [ ] T1.4 `README.md` skeleton + `.gitignore`
- [ ] **T2 — Data contracts** (`app/schemas.py`)
  - [ ] T2.1 Enums: `Verdict`, `ClassificationLevel`, `CUICategory`
  - [ ] T2.2 Models: `ScanRequest`, `Span`, `Signals`, `Verdict` (the §5 schema)
- [ ] **T3 — Model backend interface + mock**
  - [ ] T3.1 `app/model/client.py` — `ModelClient` abstract interface
  - [ ] T3.2 `app/model/mock_client.py` — canned structured outputs keyed by input keywords (lets us build everything before Gemma exists)
  - [ ] T3.3 Backend factory in `config.py` (`MODEL_BACKEND` → client)
- [ ] **T4 — Deterministic layer** (`app/pipeline/deterministic.py`) — *also the demo baseline*
  - [ ] T4.1 Regex: SSN, banner lines (`CUI//…`, `SECRET//…`), marking-format check
  - [ ] T4.2 A `baseline_verdict()` we can show in the "old DLP" pane
- [ ] **T8 — Decision engine** (`app/pipeline/decision.py`) — pure, unit-testable
  - [ ] T8.1 Implement the §4 fusion table → final verdict + `degraded` flag
- [ ] **T9 — Orchestrator (skeleton)** (`app/pipeline/orchestrator.py`)
  - [ ] T9.1 Wire Stage1 → (Stage2 stub) → decision → `Verdict`, with latency timing
- [ ] **T11a — Minimal API** (`app/main.py`)
  - [ ] T11a.1 `POST /scan` (text in → Verdict out), `GET /health`
- [ ] **T-test** — smoke test: `pytest` with mock backend green

---

### ▶️ DAY 2 (Jul 8) — Real intelligence: rules + Gemma via Fireworks
**Goal / DoD:** With `MODEL_BACKEND=fireworks`, **real Gemma catches an unmarked-CUI paragraph that the deterministic baseline misses.** That's the whole product thesis, proven.

- [ ] **T5 — Rules & knowledge** (`app/rules/`)
  - [ ] T5.1 `cui_categories.py` — 5–6 categories (CTI, PRVCY, EXPT/ITAR, PROCURE, LEI) with plain descriptions + examples
  - [ ] T5.2 `patterns.py` — keyword/phrase lists per category (feeds Stage 1)
  - [ ] T5.3 `system_prompt.md` — rules-in-context prompt instructing Gemma to emit our exact JSON
- [ ] **T6 — Semantic layer** (`app/pipeline/semantic.py`)
  - [ ] T6.1 Build prompt (system rules + document), define the JSON schema for guided decoding
  - [ ] T6.2 Call model client; parse into `Signals.model`
  - [ ] T6.3 **JSON-repair retry** → **degrade-to-unavailable** fallback (never hard-fail)
- [ ] **T16 — Fireworks backend** (`app/model/fireworks_client.py`)
  - [ ] T16.1 Call Gemma via Fireworks with JSON/structured mode → same schema
  - [ ] T16.2 Verify end-to-end: fireworks verdict flows through the pipeline
- [ ] **T7 — Portion-marking checker** (`app/pipeline/markings.py`)
  - [ ] T7.1 has-vs-required comparison → `marking_mismatch`, missing-marking spillage case
- [ ] **T9b — Orchestrator (full)** — plug in Stages 2 & 3, finalize `Verdict` assembly
- [ ] **T10 — Audit log** (`app/storage/audit.py`)
  - [ ] T10.1 SQLite append-only: `{ts, doc_hash, verdict, categories, latency}` — **hash, not content**
  - [ ] T10.2 `GET /audit` route
- [ ] **T14 — Synthetic dataset** (`scripts/gen_synthetic_data.py`)
  - [ ] T14.1 25–30 labelled docs: clean · **CUI-unmarked (the money case)** · CUI-marked · mismatched-marking · explicit-banner
  - [ ] T14.2 Write to `eval/dataset/*.jsonl` with ground-truth labels

---

### ▶️ DAY 3 (Jul 9) — THE DEMO: React UI + eval proof  ⭐ *submission-safe milestone*
**Goal / DoD:** Full end-to-end demo works **in the browser on Fireworks**, with side-by-side baseline, highlighted offending sentences, the egress widget, and real accuracy numbers on screen. **If the GPU never arrives, we could submit this.**

- [ ] **T11b — Full API** (`app/main.py`)
  - [ ] T11b.1 `POST /scan/file` (txt/pdf text extraction), `GET /egress-status`
  - [ ] T11b.2 Serve React static build at `/`
- [ ] **T12 — Egress monitor** (`app/egress/monitor.py`)
  - [ ] T12.1 Check model-network isolation, expose blocked-status + byte counter via `/egress-status` (returns simulated-but-honest status now; real once air-gapped on Day 4)
- [ ] **T13 — React single-page UI** (`ui/`)
  - [ ] T13.1 Vite + React scaffold; clean "defense/security" visual style
  - [ ] T13.2 `InputPane` (paste/upload)
  - [ ] T13.3 `VerdictCards` — **side-by-side: Old DLP baseline vs Spillguard**
  - [ ] T13.4 `RationalePanel` — highlight the exact offending spans in the text
  - [ ] T13.5 `EgressWidget` — "0 bytes left the box"
  - [ ] T13.6 `AuditLog` + `AccuracyTile` (reads eval report)
  - [ ] T13.7 `npm run build` → wire FastAPI to serve the static bundle
- [ ] **T15 — Eval harness** (`eval/run_eval.py`)
  - [ ] T15.1 Run all dataset docs through the pipeline
  - [ ] T15.2 Compute precision / recall / false-positive-rate + confusion matrix
  - [ ] T15.3 Emit `eval/report.md` + a JSON the UI's AccuracyTile displays
- [ ] **T-rehearse** — run the full demo script once, front-to-back, on Fireworks

---

### ▶️ DAY 4 (Jul 10) — AMD upgrade: self-host Gemma + real air-gap  🏆 *bonus-eligible milestone*
**Goal / DoD:** The *identical* demo now runs on **Gemma self-hosted on the MI300X**, with a **provable zero-egress** air-gap. (Assumes GPU access has landed — chase A0.1 hard.)

- [ ] **T17 — vLLM-local backend + AMD deploy**
  - [ ] T17.1 `app/model/vllm_client.py` — OpenAI-compatible calls to the local vLLM
  - [ ] T17.2 `gemma-vllm` service in compose using `rocm/vllm` + `google/gemma-3-12b-it` + HF token
  - [ ] T17.3 Enable **guided decoding (xgrammar)** for the forced JSON schema
  - [ ] T17.4 Provision MI300X on AMD Developer Cloud, `docker compose up`, run `scripts/warmup.py`
  - [ ] T17.5 Flip `MODEL_BACKEND=vllm-local`; confirm identical verdicts
- [ ] **T18 — Real air-gap**
  - [ ] T18.1 Put `gemma-vllm` on the `internal: true` network only
  - [ ] T18.2 Verify outbound is impossible; `/egress-status` shows real blocked + 0 bytes
- [ ] **T19a — Start recording** demo footage from the **live AMD system** (primary), keep the Fireworks run as backup
- [ ] **T-eval-amd** — re-run `run_eval.py` against self-hosted Gemma; capture the real accuracy numbers for the deck

> **Contingency:** if GPU access slips, Day 4 work shifts to Day 5 and we submit the Fireworks demo (still Gemma, still self-hostable-by-design) while the README documents the AMD path. We lose the $2k bonus edge but remain a complete Track-3 entry. *Priority: get A0.1 done today.*

---

### ▶️ DAY 5 (Jul 11) — Polish & submission (⏰ hard stop 9 PM PKT)
**Goal / DoD:** Submitted on lablab.ai before 9 PM, runnable from a clean clone.

- [ ] **T20 — README & clean-clone test**
  - [ ] T20.1 Setup + usage instructions; a table of **what runs on AMD vs the fallback**
  - [ ] T20.2 Fresh-clone test with `MODEL_BACKEND=fireworks` (and `mock`) → `docker compose up` works with only a `.env`
- [ ] **T21 — Media**
  - [ ] T21.1 Cover image
  - [ ] T21.2 Slide deck (problem → insight → demo → market → AMD/Gemma → ask)
  - [ ] T21.3 Edit the **demo video** (lead with the "old DLP said ALLOW, we said BLOCK, 0 bytes left the box" moment)
- [ ] **T22 — lablab.ai submission**
  - [ ] T22.1 Title, short + long description, tech/category tags
  - [ ] T22.2 Public GitHub repo, cover, video, deck, live app URL
  - [ ] T22.3 Submit — then **buffer time** for whatever broke

---

## 📌 Task dependency map (what blocks what)

```
A0.1 GPU access ─────────────────────────────► T17/T18 (AMD) ──► T19a recording
A0.2 HF token ──────────► T16 Fireworks ──► T6 semantic ──► T9b orchestrator ──┐
A0.3 Fireworks key ─────►                                                      │
T2 schemas ──► T3 mock ──► T4 deterministic ──► T8 decision ──► T9 orchestrator ├─► T11 API ──► T13 React ──► DEMO
T5 rules ─────────────────────────────────────► T6 semantic ──────────────────┘        │
T14 dataset ──────────────────────────────────────────────► T15 eval ──► AccuracyTile ─┘
```

---

## ⚠️ Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| GPU access slips past Day 4 | **High** | Whole product already works on Fireworks by Day 3; AMD is an upgrade. Chase A0.1 today. |
| Guided decoding / JSON hiccup on ROCm | Med | JSON-repair retry + degrade-to-deterministic; validated first on Fireworks. |
| Solo time crunch on React polish | Med | UI scoped to one page; pipeline path is protected first. Can fall back to simpler styling. |
| Live demo breaks on camera | Med | Pre-record the full run from the live system as insurance (T19a). |
| Accuracy looks weak | Low-Med | Curate the synthetic set to high-signal cases; report honest numbers; frame as advisory copilot + human sign-off. |
| Model too slow live | Low | 12B chosen for speed; warm on boot; front the URL with a light frontend. |

---

## ✅ Definition of "done and winning"

1. `docker compose up` from a clean clone → working app (fallback backend).
2. Live URL running **Gemma self-hosted on MI300X** with a provable **0-byte egress**.
3. A 90-second demo where the old baseline says ALLOW and Spillguard says BLOCK on unmarked CUI, with highlighted evidence.
4. An accuracy tile with real precision/recall from the eval set.
5. README, cover, deck, video, submission fields — all complete.
```
