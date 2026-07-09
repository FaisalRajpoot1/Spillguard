# 🛡️ Spillguard

**An inline, air-gapped data-spillage guard.** Before a document leaves the building, Spillguard reads it, classifies its CUI (Controlled Unclassified Information) sensitivity, catches missing portion-markings, and returns a verdict — **🟢 ALLOW / 🟡 FLAG / 🔴 BLOCK** — with the exact offending sentences and a plain-English rationale.

The AI brain is **Google's Gemma, self-hosted on an AMD Instinct GPU** via vLLM/ROCm, running on a network with **no route to the internet**. The document being inspected never leaves the box.

> **An AI DLP that phones home to the cloud has already leaked. Spillguard has no wire to phone home on.**

Built for the **AMD Developer Hackathon: ACT II — Track 3 (Unicorn Track)**.

---

## Why it matters

Defense contractors and agencies must protect CUI under **DFARS 7012 / CMMC 2.0** — a mandate now reaching ~300,000 organizations. Legacy DLP (Purview, Forcepoint, Titus) is regex + metadata tagging that misses sensitive content it wasn't told to look for. The new wave of "AI DLP" inspects via cloud APIs — which is self-defeating: routing the suspect document to a cloud LLM *is* the spillage. Spillguard does semantic inspection **entirely on your own AMD hardware**, so it is the only architecture that is compliant by construction.

## How it works

```
Browser ──► spillguard-app (FastAPI) ──► 4-stage pipeline ──► ALLOW / FLAG / BLOCK
                                              │
                            (internal, internet-less Docker network)
                                              ▼
                                   gemma-vllm on AMD MI300X
```

The pipeline runs **deterministic checks first** (regex/keyword — also our "legacy DLP" baseline), then a **semantic Gemma scan**, a **portion-marking check**, and a **deterministic decision engine that owns the final verdict** — the LLM informs, but never has final authority. If the model is unavailable the scan **degrades** to the deterministic verdict rather than failing.

Full design: **[docs/system-architecture.md](docs/system-architecture.md)** · Build plan: **[docs/project-plan.md](docs/project-plan.md)** · Plain-English overview: **[docs/project-info.md](docs/project-info.md)**

## Where AMD runs (Use of AMD Platforms)

| Component | Runs on | Notes |
|---|---|---|
| **Gemma 3 12B inference** | **AMD Instinct MI300X · ROCm · vLLM** | Self-hosted; the whole reason the product can exist in an enclave |
| CUI ruleset | in Gemma's context window | 192 GB HBM3 makes rules-in-context viable — no fine-tuning |
| Air-gap | Docker `internal: true` network | The model container has **no gateway to the internet** |
| App + pipeline + UI | any container host | Deployed alongside the model on AMD Developer Cloud |

## Model backends (swappable — one env var)

| `MODEL_BACKEND` | Use | Needs |
|---|---|---|
| `mock` | Offline dev / tests | nothing |
| `fireworks` | Real Gemma before the GPU is provisioned | `FIREWORKS_API_KEY` |
| `vllm-local` | **The real product** — Gemma self-hosted on AMD | MI300X + `HF_TOKEN` |

All three return the identical schema, so the app never knows which is running.

## Quick start

```bash
cp .env.example .env          # default MODEL_BACKEND=mock (no GPU/keys needed)
docker compose up --build     # → http://localhost:8000
```

For the real product on an AMD MI300X: set `MODEL_BACKEND=vllm-local` + `HF_TOKEN`, uncomment the `gemma-vllm` service in `docker-compose.yml`, and run `python scripts/warmup.py --retries 30` after boot.

### Local dev (no Docker)

```bash
# Server
cd server && python -m venv .venv && source .venv/Scripts/activate   # Git Bash on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Client (separate terminal)
cd client && npm install && npm run dev        # → http://localhost:5173
```

## Try it

```bash
curl -s http://localhost:8000/scan -H 'Content-Type: application/json' \
  -d '{"text":"The propulsion test on the Vanguard program failed at 14:32."}' | python -m json.tool
```

The UI ships with six one-click demo documents — the first, **"Unmarked CTI,"** is the centerpiece: legacy DLP says 🟢 ALLOW, Spillguard says 🔴 BLOCK, and the egress monitor stays pinned at **0 bytes out**.

## Evaluation

A labelled dataset of 31 synthetic CUI documents (`server/eval/dataset/`) is scored against the live pipeline:

```bash
cd server && python eval/run_eval.py           # writes eval/report.md + report.json
```

Result on **self-hosted Gemma 3 12B (AMD GPU · ROCm + vLLM)**:

| Metric | Spillguard | Legacy DLP |
|---|---|---|
| Verdict accuracy | **100 %** | 48 % |
| Spillage recall | **100 %** | 54 % |
| False-positive rate | **0 %** | 0 % |
| Missed spillage | **0** | 11 |

Real self-hosted Gemma caught **every** spillage across all 31 documents — including the colloquial-prose cases that keyword DLP can't see — with zero false alarms. (The offline `mock` fallback backend, for CI without a GPU, scores 87%.) The report feeds the UI's live accuracy tile.

## API

| Endpoint | Purpose |
|---|---|
| `POST /scan` | Inspect text → `ScanResult` |
| `POST /scan/file` | Inspect an uploaded `.txt`/`.pdf` |
| `GET /egress-status` | Air-gap / egress state |
| `GET /audit` | Recent verdicts (hash-only, never content) |
| `GET /eval-report` | Latest evaluation metrics |
| `GET /health` | Liveness + active backend |

## Project layout

```
spillguard/
├── server/        # FastAPI backend + 4-stage pipeline + eval harness
│   ├── app/       #   pipeline · model backends · rules · storage · egress
│   ├── eval/      #   labelled dataset + scoring harness + report
│   └── scripts/   #   warmup / readiness probe
├── client/        # React (Vite) SOC-console UI
├── docs/          # architecture · plan · deploy runbook · demo script · deck
├── docker-compose.yml
└── README.md · LICENSE · .env.example
```

## Tech stack

FastAPI · Pydantic v2 · vLLM on ROCm · Gemma 3 12B · SQLite (audit) · React + TypeScript + Tailwind + Framer Motion · Docker Compose. Runs on **AMD Developer Cloud (Instinct MI300X)**.

## Status

Backend pipeline, swappable model backends, evaluation harness, and the SOC-console UI (verdict, legacy-vs-Spillguard comparison, pipeline trace, egress monitor, accuracy tile, audit trail, file upload) are complete and verified. Remaining: flip to `vllm-local` on the provisioned MI300X for the live self-hosted demo.

## License

[MIT](LICENSE).
