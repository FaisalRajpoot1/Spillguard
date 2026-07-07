# Spillguard — System Architecture

**Author:** Engineering (senior review)
**Status:** Draft v1 — for approval before task breakdown
**Target:** AMD Developer Hackathon ACT II, Track 3. 5-day build. Team of 1–2 (Python/FastAPI).

---

## 1. What we are building (one paragraph)

Spillguard is an **inline document-inspection service**. A user submits a piece of text (or a file), and Spillguard returns a **verdict — ALLOW / FLAG / BLOCK** — plus *why*: which sensitive (CUI) categories it found, which required markings are missing, and the exact sentences that triggered the decision. The "brain" is **Google's Gemma model, self-hosted on an AMD Instinct GPU** via vLLM, running on a network with **no route to the internet** — so the document being inspected never leaves the box. A cheap, deterministic keyword/regex layer runs *first and always*, both as a safety net and as the "old-school DLP" baseline we beat live on stage.

---

## 2. Design principles (the "why" behind every decision)

These are the rules a senior engineer holds the whole design to. Each one is also a point we can defend to judges.

1. **Deterministic-first, LLM-second.** Cheap, explainable checks (regex, keyword, marking-format) run before the AI and *never* depend on it. The LLM adds semantic understanding on top. → *Engineering discipline, not "wrap everything in one prompt."*
2. **The LLM never has final authority.** A deterministic **decision engine** fuses the AI's opinion with the hard signals and applies explicit rules to produce the verdict. → *Auditable, defensible, no black-box liability.*
3. **Graceful degradation.** If the model container is down or returns junk, the system still returns a verdict (keyword-only, clearly labelled "degraded"). The demo can never hard-fail. → *Completeness score insurance.*
4. **Air-gap by construction, not by promise.** The model runs on a Docker network marked `internal: true`. It is *physically incapable* of reaching the internet, and we can prove it live. → *This is the product's entire reason to exist.*
5. **Swappable model backend.** One interface, three implementations: `vllm-local` (the real AMD deploy), `fireworks` (so a judge who clones the repo with no GPU can still run it), `mock` (canned outputs for tests/CI). → *Satisfies "runnable from a clean clone" without weakening the air-gap story.*
6. **Store hashes, not documents.** The audit log records a hash + the verdict, never the sensitive content. → *A DLP tool that hoards the secrets it inspects is a contradiction.*
7. **Scope brutally.** 5–6 CUI categories, not the full registry. Literal-banner detection, not semantic classified-indicator theater. One clean demo flow. → *Winners ship one thing that works.*

---

## 3. High-level architecture

```
                         ┌──────────────────────────────────────────────┐
                         │                BROWSER (demo UI)              │
                         │  paste/upload → verdict + rationale + egress  │
                         └───────────────────────┬──────────────────────┘
                                                 │  HTTP (external network)
                                                 ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                          spillguard-app  (FastAPI container)                    │
│                                                                                 │
│   Routes:  POST /scan   POST /scan/file   GET /egress-status   GET /audit       │
│                                                                                 │
│   ┌──────────────────────────  ANALYSIS PIPELINE  ───────────────────────────┐ │
│   │                                                                           │ │
│   │  Stage 1: Deterministic pre-check   ← regex, keywords, marking format     │ │
│   │           (also = "old DLP" baseline shown side-by-side in the demo)      │ │
│   │                        │                                                  │ │
│   │  Stage 2: Semantic scan (Gemma) ─────────► model client ──────┐           │ │
│   │           guided-decoding → strict JSON                       │           │ │
│   │                        │                                      │           │ │
│   │  Stage 3: Portion-marking checker (has-vs-required)           │           │ │
│   │                        │                                      │           │ │
│   │  Stage 4: Decision engine (fuse signals → ALLOW/FLAG/BLOCK)   │           │ │
│   │                        │                                      │           │ │
│   └────────────────────────┼──────────────────────────────────────┼──────────┘ │
│                            ▼                                       │            │
│                     SQLite audit log (hash + verdict)              │            │
└────────────────────────────────────────────────────────────────────┼───────────┘
                                                                     │
                        INTERNAL-ONLY DOCKER NETWORK (no internet)   │
                                                                     ▼
                            ┌───────────────────────────────────────────────────┐
                            │        gemma-vllm  (rocm/vllm container)           │
                            │  google/gemma-3-12b-it  (or 27b)                   │
                            │  OpenAI-compatible /v1/chat/completions            │
                            │  guided decoding (xgrammar) → forced JSON schema   │
                            │  runs on AMD Instinct MI300X (ROCm)                │
                            │  ⛔ no route to the public internet                 │
                            └───────────────────────────────────────────────────┘
```

**Two containers only.** No external database, no vector DB (the CUI ruleset is small enough to live *in the model's context window* — which is exactly why the 192 GB of GPU memory earns its keep). A judge runs `docker compose up` and the whole thing comes alive.

---

## 4. The analysis pipeline (the heart of the system)

A document flows through four stages. Each produces structured signals; the last one decides.

### Stage 1 — Deterministic pre-check  (`pipeline/deterministic.py`)
- Regex for SSNs, obvious identifiers, explicit CUI/classified **banner lines** (`CUI//SP-CTI`, `SECRET//…`).
- Keyword/phrase lists per CUI category (e.g., export-control terms).
- Marking-format validation (is a present marking even well-formed?).
- **Doubles as the demo baseline** — this is literally "what old-school DLP can see." When Spillguard beats it live, we're beating *this* module in the other pane.
- Fast, pure-Python, zero dependencies on the GPU.

### Stage 2 — Semantic scan  (`pipeline/semantic.py`)
- Builds a prompt = **system prompt (the CUI ruleset, in-context)** + the document.
- Calls the model through the **model client** (see §6).
- Uses **vLLM guided decoding** to force output into our JSON schema — no prose to regex out.
- Returns: classification level, CUI categories detected, offending spans (exact sentences), a 1–2 sentence rationale, and a confidence.
- **Reliability:** guided decoding → if the JSON is malformed, one **repair-retry** → if still bad, this stage returns "unavailable" and the pipeline degrades to deterministic-only.

### Stage 3 — Portion-marking checker  (`pipeline/markings.py`)
- Compares markings the document **has** (from Stage 1) against markings the content **requires** (from Stage 2's classification).
- Flags the dangerous case: *content is clearly CUI but the paragraph carries no marking* → that's a spillage waiting to happen.

### Stage 4 — Decision engine  (`pipeline/decision.py`)
Deterministic rules fuse everything into the final verdict:

| Condition | Verdict |
|---|---|
| Explicit classified banner found (Stage 1) | 🔴 **BLOCK** |
| Model finds CUI content **and** required marking missing | 🔴 **BLOCK** |
| Model finds CUI content, markings present but mismatched | 🟡 **FLAG** |
| Only weak/low-confidence signals | 🟡 **FLAG** |
| No sensitive signals from any stage | 🟢 **ALLOW** |
| Model unavailable → deterministic signals only | verdict + `degraded: true` |

*The AI informs the verdict; the rules own it.*

---

## 5. The data contract (verdict schema)

Every scan returns this object (Pydantic-validated). This is the stable interface between the pipeline, the UI, the audit log, and the eval harness.

```jsonc
{
  "verdict": "ALLOW | FLAG | BLOCK",
  "classification_level": "UNCLASSIFIED | CUI | CUI//SP",
  "cui_categories": ["CTI", "PRVCY", "EXPT", "PROCURE", "LEI"],
  "portion_markings_found": ["CUI//SP-CTI"],
  "portion_markings_expected": ["CUI//SP-CTI"],
  "marking_mismatch": true,
  "spillage_flag": true,
  "offending_spans": [
    { "text": "…the exact sentence…", "category": "CTI", "reason": "why" }
  ],
  "rationale": "One or two plain-English sentences.",
  "confidence": 0.0,
  "engine": "vllm-local | fireworks | mock",
  "degraded": false,
  "latency_ms": 812,
  "signals": { "deterministic": { }, "model": { } }
}
```

---

## 6. Model backend abstraction (`app/model/`)

One interface, three implementations — selected by the `MODEL_BACKEND` env var.

| Backend | Purpose | Talks to |
|---|---|---|
| `vllm-local` | **The real product.** The live demo + the AMD self-hosted story. | Internal vLLM container on the MI300X |
| `fireworks` | So a judge with **no GPU** can still `docker compose up` and see it work. Clearly documented as a convenience fallback. | Fireworks API (Gemma) |
| `mock` | Deterministic canned outputs. Powers unit tests + CI with no GPU and no network. | nothing |

All three return the **same schema**, so the pipeline, UI, and tests never know or care which is running.

> **Why this matters:** it lets us develop and test *today* (mock / Fireworks) while the GPU is being provisioned, then flip one env var to `vllm-local` for the real demo. It de-risks the whole timeline.

---

## 7. The air-gap — how we make it real (and provable)

This is the demo's money shot, so it's engineered, not asserted:

- The `gemma-vllm` container is attached **only** to a Docker network declared `internal: true`. Docker gives that network **no gateway to the host/internet**. The model literally cannot open an outbound connection.
- `spillguard-app` sits on **two** networks: the external one (so your browser reaches it) and the internal one (so it can reach the model). It is the only bridge, and it only ever *reads* verdicts.
- **`GET /egress-status`** runs a live check: it attempts an outbound connection *from the model network* and shows it failing, plus the outbound byte counter pinned at **0**. That widget is what we point the camera at.

---

## 8. Deployment topology (`docker/docker-compose.yml`)

```yaml
services:
  spillguard-app:      # FastAPI + pipeline + UI + audit
    networks: [external, model_internal]
    ports: ["8000:8000"]
    environment: [MODEL_BACKEND, MODEL_URL, MODEL_NAME]

  gemma-vllm:          # rocm/vllm serving Gemma 3 on the MI300X
    networks: [model_internal]      # <-- internet-less
    # GPU device access (ROCm), HF token for the gated model

networks:
  external:            # browser ↔ app
  model_internal:
    internal: true     # <-- the air-gap, enforced by Docker
```

Runs on an **AMD Developer Cloud MI300X** instance for the live URL. A clean clone with no GPU runs with `MODEL_BACKEND=fireworks` or `mock`.

---

## 9. Technology stack

| Layer | Choice | Why |
|---|---|---|
| API / backend | **Python 3.11 + FastAPI + Pydantic v2 + Uvicorn** | Team's strength; async; schema validation for free |
| Model serving | **vLLM on ROCm** (`rocm/vllm` image), **Gemma 3 12B** (27B optional) | Officially documented on MI300X; OpenAI-compatible; 12B = snappier demo |
| Structured output | **vLLM guided decoding (xgrammar)** + Pydantic + JSON-repair retry | Reliable JSON, not regex-on-prose |
| Deterministic layer | Python `re` + curated keyword/pattern lists | Fast, explainable, GPU-free |
| Storage | **SQLite** (one file, in a volume) | No external DB service; audit log only |
| Frontend | **[DECISION — see §12]** lightweight Jinja2 + HTMX *or* a small React page | Demo-grade UI, minimal build overhead |
| Eval | pytest + a standalone `run_eval.py`, hand-rolled precision/recall | The Completeness artifact |
| Packaging | **Docker + docker-compose** (2 services, internal network) | One-command up; submission requirement |
| Deploy | AMD Developer Cloud (MI300X, ROCm, Docker preinstalled) | The "Use of AMD" requirement |

---

## 10. Repository structure

```
spillguard/
├── app/
│   ├── main.py               # FastAPI app, routes, serves UI
│   ├── config.py             # settings: MODEL_BACKEND, model name, thresholds
│   ├── schemas.py            # Pydantic: ScanRequest, Verdict, Span, Signals
│   ├── pipeline/
│   │   ├── orchestrator.py   # runs the 4 stages, calls the decision engine
│   │   ├── deterministic.py  # Stage 1 — regex/keyword baseline (+ demo baseline)
│   │   ├── semantic.py       # Stage 2 — Gemma call + guided decoding
│   │   ├── markings.py       # Stage 3 — portion-marking checker
│   │   └── decision.py       # Stage 4 — verdict fusion rules
│   ├── model/
│   │   ├── client.py         # ModelClient interface
│   │   ├── vllm_client.py    # local vLLM (AMD)  ← the real one
│   │   ├── fireworks_client.py
│   │   └── mock_client.py
│   ├── rules/
│   │   ├── cui_categories.py # the 5–6 CUI category definitions
│   │   ├── patterns.py       # regex/keyword patterns
│   │   └── system_prompt.md  # rules-in-context prompt for Gemma
│   ├── storage/audit.py      # SQLite append-only log (hash, not content)
│   ├── egress/monitor.py     # proves the model network is internet-less
│   └── ui/                   # templates/ + static/
├── eval/
│   ├── dataset/              # 25–30 synthetic labelled docs (jsonl)
│   ├── run_eval.py           # runs the set, computes precision/recall/FPR
│   └── report.md             # generated metrics (the "accuracy tile")
├── tests/                    # unit tests (use mock backend, no GPU)
├── scripts/
│   ├── gen_synthetic_data.py # builds the eval dataset
│   └── warmup.py             # warms the model on boot
├── docker/
│   ├── Dockerfile.app
│   └── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

---

## 11. What we are deliberately NOT building (scope guardrails)

To protect the 5-day timeline, these are explicitly **out**:
- ❌ Real classified-level classification (legally fraught) — we do **CUI + literal banners** only.
- ❌ The full CUI Registry — **5–6 categories** only.
- ❌ Vision / scanned-document support — **text-only** for the core; a single image clip is a *stretch* goal, not a dependency.
- ❌ Real email/gateway integration — we **simulate** the "outbound door" in the UI.
- ❌ User accounts, multi-tenant, RBAC — irrelevant to the demo.
- ❌ A vector DB / RAG — the ruleset fits in-context.

---

## 12. Locked decisions (confirmed)

1. **AMD GPU access — PENDING.** Access/credits not active yet. → **Strategy:** all GPU-independent work is front-loaded and built against the `mock` + `fireworks` backends. The `vllm-local` (AMD) integration is a *flip-one-env-var* step slotted for when access lands. No idle waiting.
2. **Team — SOLO (1 dev).** → Tasks are strictly sequenced; the critical demo path (scan → verdict → UI) is protected first, polish second.
3. **Frontend — POLISHED REACT.** → A single, clean React (Vite) single-page app, built to static assets and served by the FastAPI container (no separate server, no impact on the air-gap). Scoped to one page to stay safe on the timeline.
4. **Model — GEMMA 3 12B** (`google/gemma-3-12b-it`) for the demo; 27B remains a one-line swap if we want the "big model on one card" framing.

### Frontend note (updates §9)
React + Vite → `npm run build` → static bundle served by FastAPI at `/`. The app talks to the same `/scan`, `/egress-status`, `/audit` endpoints. Because it's built to static files served by the app container, it adds **no** new runtime service and does **not** touch the internal model network.
```
