# AI PR Quality Gatekeeper — Build Specification

**Hackathon:** AMD Developer Hackathon: ACT II — Track 3 (Unicorn Track)
**Kickoff:** July 6, 2026, 9:00 PM PKT
**Submission deadline:** July 11, 2026, 9:00 PM PKT
**Judging criteria:** Creativity & originality, product/market potential, completeness, use of AMD platforms
**Bonus target:** Best Use of Gemma via Fireworks ($1,000)

---

## 1. The problem (why this, why now)

GitHub's own infrastructure is buckling under a flood of AI-agent-generated pull requests:

- AI-authored PRs jumped from ~4 million/month (Sept 2025) to ~17 million/month (March 2026) — a 325% increase in six months.
- A prominent open-source infrastructure lead stated publicly: **"only 1 out of 10 PRs created with AI is legitimate."** The other 90% is noise that still consumes maintainer review time.
- GitHub shipped emergency measures in February 2026 (disable PRs entirely, restrict PRs to collaborators only) just to cope with volume.
- GitHub's own roadmap lists **"AI triage tools to filter low-quality submissions before they reach humans"** as a feature still **under evaluation** — i.e., not yet shipped by anyone at scale.

**The gap:** no widely-available tool sits in front of a repo's PR queue and tells a maintainer, before they open the diff, whether a given AI-generated PR is worth their time — scored against *that specific repo's* actual standards, not generic best practices.

**Who pays:** any company or open-source project running high PR volume — GitHub Enterprise orgs, OSS foundations, and any team using agentic coding tools (Claude Code, Devin, Copilot) that now has to review its own agents' output at scale.

---

## 2. Product concept

A GitHub App that watches a repository's pull requests and, within seconds of a PR being opened, posts a structured quality assessment as a PR comment: a score, specific concerns, and a recommendation (approve / needs human review / likely noise) — grounded in that repo's own `CONTRIBUTING.md`, code style, and existing utilities, not a generic LLM opinion.

**The demo moment:** open a real (or forked) public repo, submit a deliberately low-effort AI-generated PR and a genuinely good one side by side, and show the Gatekeeper correctly triaging both in real time.

---

## 3. Architecture overview

```
GitHub PR opened/updated
        │
        ▼
Webhook receiver (FastAPI, containerized, deployed on AMD Developer Cloud)
        │
        ├──────────────┬──────────────────────┐
        ▼              ▼                      │
Static analysis   Repo context RAG            │
(lint, tests,     (CONTRIBUTING.md +          │
diff stats)       code embeddings,            │
                  built/run locally           │
                  on AMD GPU via ROCm)         │
        │              │                      │
        └──────┬───────┘                      │
               ▼                              │
      Scoring agent (Gemma via Fireworks AI)   │
               │                               │
               ▼                               │
   PR comment + score dashboard  ◄──────────────┘
```

**Design principle for judges:** deterministic/cheap checks run first and are never skipped even if the LLM call fails — this shows engineering discipline, not "wrap everything in a single prompt."

---

## 4. Repository structure

```
pr-gatekeeper/
├── ingest/
│   ├── webhook.py         # FastAPI endpoint, verifies GitHub webhook signature
│   ├── github_client.py   # fetches PR diff, files changed, PR metadata, posts comments
│   └── models.py          # Pydantic schemas for PR event payloads
├── context/
│   ├── indexer.py         # chunks CONTRIBUTING.md, README, sampled source files
│   ├── embeddings.py      # builds/updates a local vector store per connected repo
│   └── retriever.py       # retrieves relevant repo context for a given diff
├── analysis/
│   ├── static_checks.py   # runs linters/tests, computes diff size & churn
│   └── heuristics.py      # boilerplate/duplicate-PR detection, AI-pattern signals
├── scoring/
│   ├── agent.py           # builds prompt, calls Gemma via Fireworks, parses structured output
│   ├── prompts/
│   │   ├── system_prompt.md
│   │   └── scoring_schema.json
│   └── schema.py           # Pydantic model for the agent's structured JSON output
├── output/
│   ├── commenter.py        # formats and posts the PR comment via GitHub API
│   └── dashboard/          # lightweight web UI: per-repo PR quality trends over time
│       ├── app.py
│       └── templates/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/
│   ├── test_static_checks.py
│   ├── test_scoring_agent.py
│   └── fixtures/            # sample PR diffs (good + noisy) for demo and testing
├── .env.example
├── requirements.txt
└── README.md
```

---

## 5. Component specifications

### 5.1 Ingest layer (`ingest/`)

- Register a **GitHub App** (not a personal access token — this matters for the "completeness" judging criterion and for real installability).
- Subscribe to webhook events: `pull_request.opened`, `pull_request.synchronize`, `pull_request.reopened`.
- On event: verify the GitHub webhook signature (HMAC), then fetch via GitHub REST/GraphQL API:
  - Full diff (patch format)
  - List of changed files
  - PR title + description
  - Base repo's default branch reference (for context indexing)
- Emit a normalized `PREvent` object downstream to both `analysis/` and `context/` in parallel.

### 5.2 Static analysis (`analysis/`)

Runs first, always, regardless of LLM availability:

- Run the repo's existing linter/test suite against the PR branch if configured (or a safe subset — don't assume arbitrary code execution is safe in a hackathon demo; sandbox or mock this for repos you don't control).
- Compute diff size, number of files touched, churn ratio (lines added vs. removed).
- Heuristic AI-pattern signals: unusually generic commit messages, PR description that doesn't match the actual diff, boilerplate scaffolding with no functional change, duplicate logic vs. existing utilities in the repo.
- Output a `StaticSignals` object: `{ tests_pass, diff_size, churn_ratio, ai_pattern_flags: [...] }`.

### 5.3 Repo context RAG (`context/`)

- On first connection to a repo (and periodically thereafter), chunk and embed:
  - `CONTRIBUTING.md` (contribution rules — the source of truth for "what this repo actually wants")
  - `README.md`
  - A sample of existing source files (for code-style conventions)
- Store embeddings in a **local vector store** (e.g. Chroma), with the embedding model run **locally on the AMD GPU via ROCm** — this is the concrete, demonstrable "use of AMD platforms" beyond just calling Fireworks.
- On each PR event, retrieve the top-k most relevant chunks given the diff (e.g., "what does this repo's CONTRIBUTING.md say about test coverage requirements?").

### 5.4 Scoring agent (`scoring/`)

- Constructs a single structured prompt containing: the diff, `StaticSignals`, and retrieved repo context.
- Calls **Gemma via the Fireworks AI API** (use Fireworks' structured-output / function-calling mode so the response is reliable JSON, not prose to regex).
- Expected output schema:

```json
{
  "score": 0-100,
  "recommendation": "approve | needs_human_review | likely_noise",
  "concerns": ["string", "..."],
  "strengths": ["string", "..."],
  "reasoning_summary": "1-2 sentence explanation"
}
```

- Prompt design principle: explicitly instruct the model to judge the PR against the *retrieved repo context*, not generic software best practices — this is what differentiates the tool from a naive "ask an LLM if this is good code" wrapper.

### 5.5 Output layer (`output/`)

- **Commenter:** posts one formatted comment on the PR with the score, recommendation, concerns, and strengths. Keep the format skimmable — maintainers should be able to triage in under 5 seconds.
- **Dashboard:** a small web page per connected repo showing score trends over time (useful for the demo video and for showing "completeness" — a working product, not just a script).

---

## 6. Data flow contracts

| Stage | Input | Output |
|---|---|---|
| Ingest | GitHub webhook payload | `PREvent { repo, pr_number, diff, files, title, description }` |
| Static analysis | `PREvent` | `StaticSignals { tests_pass, diff_size, churn_ratio, ai_pattern_flags }` |
| Context RAG | `PREvent` | `RepoContext { relevant_chunks: [...] }` |
| Scoring agent | `PREvent + StaticSignals + RepoContext` | `ScoreResult { score, recommendation, concerns, strengths, reasoning_summary }` |
| Output | `ScoreResult` | Posted PR comment + dashboard entry |

---

## 7. AMD / Fireworks / Gemma integration checklist

- [ ] Entire pipeline containerized and deployed on **AMD Developer Cloud** (not run locally on a laptop for the demo).
- [ ] Embedding generation for the RAG layer runs **locally on the AMD GPU via ROCm** — a genuine, non-trivial use of the hardware.
- [ ] Scoring calls go to **Gemma via Fireworks AI API** — required for the $1,000 "Best Use of Gemma via Fireworks" bonus prize.
- [ ] README explicitly documents which components run where (AMD GPU vs. Fireworks-hosted) — judges score "use of AMD platforms" directly, so this must be legible, not buried.

---

## 8. Containerization requirements (submission mandates all-containerized)

`docker/docker-compose.yml` should define exactly two services:

1. **app** — FastAPI ingest + analysis + scoring + output, single container.
2. **vectordb** — local Chroma (or similar) instance for the RAG embeddings, no external DB dependency.

Goal: a judge should be able to clone the repo and run `docker-compose up` with a `.env` file (API keys) and have the whole system come up without additional setup steps. This directly serves the "completeness" judging criterion.

---

## 9. 5-day build plan

| Day | Focus | Deliverable |
|---|---|---|
| **Day 1** | Scaffolding + ingest | Repo structure created, GitHub App registered, webhook receiver logs real PR events end-to-end against a test repo |
| **Day 2** | Static analysis + RAG | Static checks running on a real diff; repo indexer producing embeddings from a real `CONTRIBUTING.md` |
| **Day 3** | Scoring agent | Fireworks + Gemma call wired up with structured JSON output — do this early, it's the riskiest integration |
| **Day 4** | Output + deployment | PR comment posting works; dashboard shows at least one repo's history; container deployed to AMD Developer Cloud; begin recording demo footage |
| **Day 5** | Polish + submission | README finalized, cover image, slide deck, video presentation recorded, submission fields completed on lablab.ai |

---

## 10. Demo script (for the video presentation)

1. Show a real (or forked) public GitHub repo with the Gatekeeper installed.
2. Open PR A: a low-effort, clearly AI-generated PR (boilerplate, doesn't match description, ignores existing utils).
3. Open PR B: a genuinely good, well-scoped PR.
4. Show the Gatekeeper's comment appearing on both within seconds — correctly flagging A as `likely_noise` and B as `approve`, each with specific, repo-grounded reasoning.
5. Show the dashboard view: PR quality trend for the repo over time.
6. Close with the market framing: cite GitHub's own confirmed 17M/month AI PR volume and the "1 in 10 legitimate" statistic to establish real, current, large-scale demand.

---

## 11. Submission checklist (per lablab.ai requirements)

- [ ] Project title, short description, long description, technology/category tags
- [ ] Cover image
- [ ] Video presentation
- [ ] Slide presentation
- [ ] Public GitHub repository with a README containing setup + usage instructions
- [ ] Application must be runnable using the provided instructions (test this from a clean clone before submitting)
- [ ] All submissions must be containerized — verify `docker-compose up` works from scratch

---

## 12. Stretch goals (only if core loop is solid by Day 4)

- Configurable scoring strictness per repo (some maintainers want stricter gates than others).
- Slack/Discord notification integration for maintainer teams.
- Support for scoring PR **descriptions vs. actual diff** mismatch as a distinct, separately-flagged signal (a common tell for low-effort AI PRs).
- A "why was this flagged" expandable section in the PR comment, linking back to the specific `CONTRIBUTING.md` clause that was violated.
