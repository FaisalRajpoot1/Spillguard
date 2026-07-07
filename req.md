Architected comprehensive PR quality system with components and implementation timelineArchitected comprehensive PR quality system with components and implementation timelinePicking back up on the AI PR Quality Gatekeeper.
Repo structure for Claude Code to scaffold
pr-gatekeeper/
├── ingest/              # GitHub App webhook receiver + diff fetcher
│   ├── webhook.py       # FastAPI endpoint, verifies GitHub signature
│   ├── github_client.py # fetches PR diff, files changed, PR metadata
│   └── models.py        # PR event schema
├── context/             # repo indexing for RAG
│   ├── indexer.py       # chunks CONTRIBUTING.md, README, key source files
│   ├── embeddings.py    # builds/updates a local vector store per repo
│   └── retriever.py     # pulls relevant context for a given diff
├── analysis/            # static, deterministic signals (cheap, fast, run first)
│   ├── static_checks.py # linter output, test pass/fail, diff size, churn
│   └── heuristics.py     # boilerplate detection, duplicate-PR detection, AI-pattern heuristics
├── scoring/             # the actual agent
│   ├── agent.py         # builds the prompt, calls Gemma via Fireworks
│   ├── prompts/          # prompt templates for scoring + explanation
│   └── schema.py         # structured JSON output: score, reasons, recommendation
├── output/
│   ├── commenter.py      # posts formatted PR comment via GitHub API
│   └── dashboard/        # lightweight web dashboard (repo-level PR quality trends)
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/
├── .env.example
└── README.md
How each piece works
Ingest. A GitHub App (not a personal access token — judges will check this is production-shaped) subscribes to pull_request.opened and pull_request.synchronize webhooks. On event, fetch the diff, changed files, and PR description via the GitHub REST API.
Analysis (runs first, cheap). Before ever calling an LLM, run fast deterministic checks: does it pass existing linters/tests, how large is the diff, is it touching files unrelated to its stated purpose, does the PR description match the actual code change. This matters for judging — it shows engineering discipline, not just "wrap everything in a prompt."
Context (RAG). Index each connected repo's CONTRIBUTING.md, README, and a sample of existing code style once (cache it), so the scoring agent judges a PR against that repo's actual standards, not generic best practices. This is the differentiator versus a naive "ask an LLM if this PR looks good" approach.
Scoring agent. This is where Gemma comes in via Fireworks — feed it the diff, the static-analysis results, and the retrieved repo context, and have it return structured JSON: a quality score, specific concerns (hallucinated APIs, unaddressed edge cases, redundant code vs. existing utils), and a recommendation (approve / needs-human-review / likely-noise). Use Fireworks' function-calling/structured-output mode so you get reliable JSON, not prose you have to regex out.
Output. Post a single, well-formatted PR comment with the score and reasoning (this is your demo moment — show a real PR from a real open-source repo getting scored live). Also keep a tiny dashboard showing score trends across a repo's PRs over time, since that visual is good for the pitch/demo video.
Where AMD infra actually shows up (don't skip this — it's a judging criterion)

Containerize the whole ingest → analysis → scoring pipeline and deploy it on AMD Developer Cloud, so it's not just calling Fireworks from a laptop.
Run the embeddings/retrieval step (the RAG index) locally on the AMD GPU via ROCm instead of an external embeddings API — this is a legitimate, demonstrable "we're using AMD hardware for something real" story beyond just being a pass-through to Fireworks.
Use Fireworks AI credits specifically for the Gemma scoring calls — this is what qualifies you for the $1,000 "Best Use of Gemma via Fireworks" bonus prize on top of the Track 3 prize.

Containerization for submission
Submission requires everything containerized and a public repo with a working README. Keep it to one docker-compose.yml with two services: the app (FastAPI ingest + scoring pipeline) and a small local vector DB (Chroma or similar) for the embeddings — no external DB dependency, so a judge can docker-compose up and it just runs.
5-day build plan (kickoff July 6, deadline July 11, 9pm PKT)

Day 1 (today/tomorrow): Claude Code scaffolds the repo structure above, GitHub App registration, webhook receiver working end-to-end against a test repo (even just logging the payload).
Day 2: Static analysis module + repo indexer/RAG working. Get a real diff in, real context out.
Day 3: Wire up Fireworks + Gemma scoring call with structured output. This is the riskiest integration — do it early, not last.
Day 4: PR comment posting + dashboard. Deploy the container to AMD Developer Cloud. Start recording demo footage against a real repo (yours or a popular OSS one, with permission/a fork).
Day 5: Polish README, cover image, slide deck, video presentation. Buffer day for whatever broke.