# Track 3 (Unicorn Track) — Idea Shortlist & Winner

**Hackathon:** AMD Developer Hackathon ACT II · Track 3 (Unicorn Track) · deadline **July 11 2026, 9pm PKT**
**Judged on:** Creativity & Originality · Product/Market Potential · Completeness (5-day) · Use of AMD Platforms
**Bonus target:** $2,000 "Best AMD-Hosted Gemma Project" (favors **self-hosting Gemma on AMD Instinct via ROCm/vLLM**, not a Fireworks pass-through)

**How this list was produced:** an 87-agent "idea-forge" workflow generated 21 ideas across 7 strategic lenses → a 3-judge panel scored each on all four criteria + 5-day feasibility + Gemma-bonus fit → 2 adversarial skeptics (completeness + originality) stress-tested the top 8 → a synthesizer ranked them by **expected value of actually winning** (will the demo work, is the AMD hook load-bearing, is it memorable, is the market real). A parallel deep-research pass independently verified the market facts (AI-code-review market is crowded with 8+ incumbents; full-codebase-RAG PR review is already commoditized; AMD-hosted Gemma via ROCm/vLLM is officially documented and turnkey).

**The reordering insight:** Gemma-3's single weakest documented skill is VLM *grounding* (pixel bounding boxes). Ideas whose killer demo needs the model to emit reliable pixel coordinates (Safe Harbor, RedactRadar, RedactionRoom, Sunshine, Inkout) are traps unless they pivot to **OCR-for-geometry + Gemma-for-classification**. Ideas that avoid geometry entirely (Spillguard, Percept, MindMixer) are safer on stage.

---

# 🏆 WINNER — Spillguard

> *Single recommended build. Highest expected value of winning Track 3 **and** the $2K Gemma bonus.*

**Panel score: 77.7/100** — Creativity 7 · Market 7.3 · Completeness 7.7 (**highest in pool**) · AMD-depth 8.7 · Gemma-bonus-fit 9

**One-liner:** An inline, air-gapped data-spillage guard that reads a document at save/send time, classifies its CUI sensitivity, catches missing portion markings, and blocks leaks — on your own AMD GPU, because a DLP tool that phones home to a cloud has already leaked.

**Concept:** Defense contractors and agencies must protect Controlled Unclassified Information (CUI) under DFARS 7012 and CMMC 2.0 and prevent "spillage" — CUI or classified content landing where it shouldn't (an outbound email, the wrong enclave, a SaaS upload). Legacy DLP (Microsoft Purview, Forcepoint, Titus/Fortra) is regex + metadata tagging that misses content it wasn't told to look for; the new wave of "AI DLP" inspects via cloud APIs, which is self-defeating — routing the suspect document to OpenAI *is* the spillage event. Spillguard sits at the enclave boundary as a FastAPI guard: before a document/message leaves, it classifies sensitivity (CUI category or classified-indicator), detects portion-marking errors, flags spillage with a rationale, and returns **ALLOW / FLAG / BLOCK**. Gemma 3 vision also inspects screenshots and scanned pages — a common spillage vector text DLP can't see.

**Target user:** Defense primes and subs, DoD program offices, and the Intelligence Community.

**AMD / Gemma hook:** `google/gemma-3-27b-it` on MI300X via the `rocm/vllm` image, served through vLLM's OpenAI-compatible endpoint, sitting inline on save/send so continuous batching + MI300X throughput keep latency low under a document stream. The full CUI Registry categories and banner/portion-marking rules are loaded **into context** — the 192GB HBM3 makes a long rules-in-context, fine-tune-free approach viable — and guided decoding (xgrammar) returns `{classification_level, cui_categories[], portion_markings[], spillage_flag, rationale}`.

**Why self-host beats an API:** The data being inspected is exactly the data that must not egress — sending it to a commercial API is *itself* the spillage and violates DFARS 7012 / IL5+ / air-gap requirements; commercial cloud LLMs aren't authorized in these enclaves. On-prem AMD is the only deployable option, and it runs fully offline. **The irony is the pitch:** any AI DLP that calls a cloud has already defeated its own purpose, so self-hosting isn't a feature — it's a logical necessity.

**Tightened 5-day plan:**
- **Day 0 (pre-kickoff):** accept the HF Gemma gate, pull `rocm/vllm`, verify **text-only** `gemma-3-27b-it` on the MI300X. Enter Day 1 green.
- **Day 1:** FastAPI guard endpoint; lock the JSON schema; guided decoding **with a JSON-parse-retry fallback** so a ROCm structured-output hiccup can't break the live path. Scope to **5–6 high-signal CUI categories** (CTI, PRVCY, EXPT/ITAR, PROCURE, LEI), not the full Registry.
- **Day 2:** portion-marking checker + rationale generation. **Drop semantic "classified-indicator" detection** — detect literal banners with an honest string match and say so (removes the biggest credibility kill-shot from a clearance-holding judge).
- **Day 3:** build a **25–30 doc hand-labeled synthetic CUI eval set**; compute precision/recall/false-positive rate. This artifact *is* your Completeness score.
- **Day 4:** demo UI (paste/upload → ALLOW/FLAG/BLOCK + rationale + suggested marking), audit log, and a **side-by-side open-source regex/keyword DLP baseline** in the same pane.
- **Day 5:** `docker-compose up`, README/cover/deck, and **pre-record the full demo from the live system** as insurance against a torn-down MI300X during judging.

**Sharpened demo moment:** Paste a paragraph whose sensitive content has **no acronym, no marking, no keyword** — plain prose describing a named program's test failure. The regex/Purview-style baseline pane returns **ALLOW (clean)**. Spillguard returns **FLAG: CUI//SP-CTI**, quotes the exact offending sentence, auto-suggests the portion marking. Then flip to the egress panel: the model container is on an internal-only docker network, packet counter frozen at **zero**. Close: *"Regex said send it. We caught it. And a cloud AI-DLP would have had to transmit this paragraph to OpenAI to read it — that transmission is the spillage. Ours has no wire to phone home on."* End on the accuracy tile: *"94% recall on our synthetic set — here's the confusion matrix."*

**#1 risk + mitigation:** *Unvalidated accuracy on a recall-critical task.* → Ship the labeled eval set with real numbers; reposition from "the boundary control" (Everfox/Owl's accredited turf) to **"pre-flight advisory copilot — the human decides,"** sidestepping CDS accreditation and classification-authority liability.

**Why it beats the PR Gatekeeper:** intrinsic self-host (wins AMD-depth + the bonus), a sharper market insight, a less-crowded lane, the highest completeness score in the pool, and a more legible, un-fakeable demo.

---

# Ranked finalists (stress-tested top 8)

## #2 — Safe Harbor  ·  score 78 (highest raw panel score)
*Creativity 7 · Market 7.3 · Completeness 6.3 · AMD-depth 9 · Gemma-bonus 9.3*

**One-liner:** A one-command, air-gapped clean room that de-identifies scanned medical faxes/PDFs to the HIPAA Safe Harbor standard on the hospital's own AMD GPU — so PHI never touches a cloud API.

**Concept:** US healthcare runs on faxes and scanned PDFs; the PHI inside them is legally radioactive — to reuse it for research/training you must first strip all 18 HIPAA Safe Harbor identifiers. Cloud tools (Amazon Comprehend Medical, Google Cloud DLP) are disqualified by the very privacy requirement; enterprise platforms (John Snow Labs) are license-gated and mostly text. Safe Harbor ingests a scanned doc, uses Gemma 3 vision to read typed **and handwritten** PHI directly (no separate OCR), returns structured redaction spans tagged by identifier category, renders a truly redacted output, and writes an audit trail with reviewer sign-off. **The wedge:** it unlocks the secondary-use data hospitals currently leave frozen.

**Target user:** Hospital data/research teams, health-tech vendors, clinical registries.

**AMD / Gemma hook:** `gemma-3-27b-it` on one MI300X via `rocm/vllm`, OpenAI-compatible endpoint; 192GB HBM3 holds the 27B multimodal weights (~54GB bf16) + big KV cache so a whole fax queue batches via continuous batching; guided decoding forces `{text, identifier_category(1-18), bbox, confidence}`. **Critical architecture fix: do NOT ask Gemma for bboxes** — run PaddleOCR/Tesseract for pixel-accurate word geometry, use Gemma *only* to classify OCR text into the 18 categories, map spans back to OCR boxes; reserve Gemma-vision for the one handwriting clip OCR can't read.

**Why self-host beats an API:** For PHI the cloud API call *is* the breach you're preventing; de-identification is precisely the step that must happen before data can egress. On-prem = no BAA gymnastics, deterministic per-page cost at hospital backlog scale, full air-gap.

**5-day plan:** Day 0 provision+gate. Day 1 OCR→Gemma-classify on born-digital + clean scans. Day 2 redaction renderer (PyMuPDF `apply_redactions` burns the text layer) + audit log. Day 3 **labeled eval set, per-identifier recall/precision**. Day 4 split-screen review UI + accept/override + zero-egress monitor. Day 5 package + record. Cut pseudonymization and fax-queue batching.

**Demo moment:** Drag a scanned referral fax. Boxes snap on pixel-perfectly (**from OCR, not the model**), color-coded to the 18 categories, egress monitor at 0 bytes. Bonus beat: a second doc with a handwritten note — *"no text layer, no OCR can read this"* — and Gemma-vision reads and redacts the handwritten name. Close on the scoreboard (recall 0.9x, reviewer sign-off required): *"This document could not legally have touched OpenAI — and it never left this box."*

**#1 risk + mitigation:** HIPAA is all-or-nothing; one missed MRN is a reportable breach and LLM recall isn't 100%. → Reframe as **"research-grade PHI pre-screen with mandatory human sign-off"** (never "automated Safe Harbor certification"); add a recall-safe over-redaction mode; **name Presidio + Private AI in the deck**.

## #3 — Percept  ·  score 77.7 (most legible, geometry-safe demo)
*Creativity 7.7 · Market 6.3 · Completeness 7 · AMD-depth 8.3 · Gemma-bonus 9*

**One-liner:** Percept looks at your app the way a human does — from the rendered pixels — and catches the accessibility failures axe-core and Lighthouse are structurally blind to.

**Concept:** DOM-based a11y tools audit the HTML tree, so they're provably blind to everything that only exists in the rendered image: text baked into images/canvas, true contrast after CSS gradients/overlays, invisible-but-focusable elements, illogical visual reading order, unlabeled icon-only buttons, clipped text. Percept renders a page with Playwright (screenshot + a11y tree) and has Gemma 3 vision reason over the pixels: each finding boxed on the screenshot, mapped to a WCAG criterion, with a suggested fix. Slots into CI to gate PRs on *rendered* accessibility.

**Target user:** Frontend/design-system teams + accessibility/compliance engineers under ADA, Section 508, or EN 301 549 pressure.

**AMD / Gemma hook:** `gemma-3-27b-it` on MI300X via `rocm/vllm`; a CI run streams dozens–hundreds of screenshots through continuous batching — a genuine throughput story. **Boxes come from Playwright's real element geometry (`getBoundingClientRect`), not the model; contrast computed deterministically from sampled pixels, never from the VLM** — the bbox landmine is engineered out. Ship a `MODEL_BACKEND` switch so a clean clone boots against a hosted endpoint while the MI300X powers the live URL.

**Why self-host beats an API:** CI fires on every push → huge bursty image volume where per-image API pricing + rate limits hurt; many teams' pre-release UI screenshots legally can't ship to a third party. Self-host = flat-cost internal service, zero egress, no rate ceiling.

**5-day plan:** Day 0-1 GPU up + Playwright screenshot/a11y-tree/computed-styles. Day 2 hybrid pipeline (Gemma names failing element, you box it from geometry). Day 3 axe-core dedup → surface the **delta**. Day 4 CLI + hosted UI. Day 5 curate demo sites + record. Cut the GitHub Action and multi-image focus/hover to future work.

**Demo moment:** Split-screen on one slick landing page. Left: axe-core → **"0 issues."** Right: Percept pixel-perfect boxes on genuinely pixel-only failures — pricing/CTA baked into a hero JPG (OCR'd out), a countdown on `<canvas>`, 2.9:1 body copy after a gradient overlay. Money line: *"Deque can see some of this — but you'd ship screenshots of your unreleased pricing page to their cloud. Percept ran 140 UI states this build on one MI300X in your own VPC for $0.02 — nothing left the box."*

**#1 risk + mitigation:** The "DOM-blind competitors" framing is factually wrong (Deque axe DevTools and Evinced already do vision a11y). → Re-anchor originality on **self-hosted + private + open-weight**, not "we see what axe can't." Name Deque/Evinced; position on privacy/self-hosting/price.

## #4 — MindMixer  ·  score 77.7 (highest creativity 8.3; the wildcard)
*Creativity 8.3 · Market 5.3 · Completeness 7.3 · AMD-depth 9 · Gemma-bonus 9*

**One-liner:** Real-time sliders that dial an AI's honesty, warmth, mischief, and confidence up and down mid-sentence — by writing steering vectors directly into Gemma's hidden states, something no hosted API can do.

**Concept:** A chat UI with a mixing board of trait faders (Honesty, Warmth, Verbosity, Formality, Confidence, Mischief). Each fader adds a precomputed steering vector to Gemma's residual stream at inference, so the SAME model on the SAME prompt visibly shifts personality as you drag. This is representation engineering (RepE / contrastive activation addition) turned into a product — controllability that lives *below* the prompt layer. Users: writers building consistent characters, game devs tuning NPCs, researchers probing behavior, safety folks demoing "what a dishonest model looks like."

**Target user:** Fiction writers/game devs tuning NPCs, AI-safety educators, ML researchers wanting RepE without writing hook code.

**AMD / Gemma hook:** Serve Gemma-3 (12B→27B) on MI300X via ROCm PyTorch + transformers, forward hooks on a mid decoder layer's residual stream. Vectors extracted offline from ~50 contrastive prompt pairs per trait. **To make AMD load-bearing:** exploit 192GB HBM3 for a **"persona farm"** — one base model + dozens of steering-vector sets serving many differently-steered personas concurrently in one batch ("N personalities from one model on one card — only economical with AMD's memory"). Add **live on-demand vector extraction** (type a novel trait → extract on the GPU in seconds).

**Why self-host beats an API:** No commercial API exposes *write* access to a model's residual stream — the whole product IS the forward hook adding vectors to hidden states, which requires the weights in your own process. The purest "definitionally impossible via API" story.

**Why it's not #1:** panel flagged `survivesBoth: false`. (a) **AMD is token by the judges' own definition** — forward hooks run identically on any GPU, which *weakens the $2K bonus you're optimizing for*; (b) originality is stale — EasySteer (Sept 2025), EasyEdit2, Persona Vectors already ship the core. Wins *Creativity* outright but weakest fit for the combined objective.

**5-day plan:** Cut the vLLM baseline A/B (baseline = alpha=0 on the same path). Reduce to 3-4 *validated* clean traits. Hard-clamp per-fader and total alpha so the live drag *physically cannot* enter the gibberish zone. Pre-bake locked presets. 2nd dev on UI from Day 1 (must look like a product).

**Demo moment:** Lead with the **bulletproof single fader** — drag Honesty max→0 on a running answer, watch it morph earnest→evasive token-by-token (one clamped vector, cannot break). Then type a brand-new trait — *"passive-aggressive Victorian butler"* — and the GPU extracts a fresh fader live in seconds. Encore: eight custom personas answering concurrently on the one card.

**#1 risk + mitigation:** token AMD + already-shipped originality. → Persona-farm memory story makes AMD load-bearing; cite EasySteer/Persona Vectors and state exactly what you add (live extraction + multimodal steering + AMD multi-persona serving).

## #5 — Sunshine  ·  score 77.3
*Creativity 7.3 · Market 6.7 · Completeness 6.3 · AMD-depth 8.3 · Gemma-bonus 9*

**One-liner:** An air-gapped FOIA copilot that reads government records and proposes each redaction tagged with the specific statutory exemption and a cited rationale — running on the agency's own AMD GPU because pre-release records can't go to a commercial cloud.

**Concept:** Agencies drown in FOIA/public-records backlogs; every release requires a human to redact the nine FOIA exemptions and cite which one justifies each redaction. The docs under review aren't yet cleared for release, so sending them to OpenAI is the exact disclosure the review exists to prevent. Sunshine reads records (often scanned), proposes redactions each tagged with exemption + subsection + a one-line justification grounded in a local copy of the DOJ FOIA Guide, and exports the reviewer-ready redaction index. Decision-support — a human approves every call.

**Target user:** Agency FOIA offices, state/municipal clerks, records-review contractors.

**AMD / Gemma hook:** `gemma-3-12b-it` or `27b-it` on MI300X via `rocm/vllm`; 192GB HBM3 fits full document context + a local RAG of the DOJ FOIA exemption manual + big KV cache; guided decoding emits `{span, exemption_code, subsection, rationale, confidence}`; Gemma-3 vision handles scanned records. The distinguishing move — telling b(6) personal privacy from b(7)(C) with a cited reason — is legal reasoning, not regex.

**Why self-host beats an API:** pre-release government docs whose entire sensitivity is that they're uncleared; commercial cloud LLMs generally aren't authorized inside the agency boundary. On-prem is the only lawful path.

**5-day plan:** Day 1 rocm/vllm + Gemma + exemption JSON schema. Day 2 Chroma RAG over DOJ FOIA Guide so rationales cite real criteria. Day 3 true PDF redaction (remove the underlying text layer) + exemption-coded export. Day 4 accept/reject/re-tag reviewer UI. Day 5 compose + synthetic memos + egress-blocked demo.

**Demo moment:** Upload an internal memo with names, an SSN, an informant reference, a law-enforcement technique. Sunshine highlights each redaction color-coded by exemption, shows 'b(6) — personal privacy' vs 'b(7)(D) — confidential source', exports the standard index. The beat: it **correctly distinguishes b(6) from b(7)(C) on two similar-looking names** — a judgment call, not a pattern match.

**#1 risk + mitigation:** legal nuance → over/under-redaction. Frame strictly as decision-support with mandatory human approval; budget explicit time for true text-layer removal and verify no recoverable text. *Distinct edge worth stealing: auto-draft a Vaughn index / annual FOIA exemption tally — a deliverable incumbents don't ship.*

## #6 — PriorAuthPilot  ·  score 77.3 (highest market pull, 8.0)
*Creativity 6.7 · Market 8 · Completeness 6 · AMD-depth 8.7 · Gemma-bonus 9*

**One-liner:** Drop in a scanned patient chart and a payer policy; it predicts the denial, tells you which coverage criterion is missing, and drafts the appeal — all on hardware inside the hospital, because PHI can never touch a cloud API.

**Concept:** US providers lose billions to prior-auth denials almost always caused by one undocumented coverage criterion. PriorAuthPilot ingests a chart (usually a scanned fax) + the payer's medical-necessity policy, returns a structured verdict `APPROVE_LIKELY | DENIAL_LIKELY | MISSING_DOCUMENTATION` with each criterion checked against the chart and cited to the exact policy sentence + chart page; on predicted denial it drafts the appeal. Provider-side, pre-submission prediction — the opposite of insurer-side EDI rules engines.

**Target user:** Hospital revenue-cycle and utilization-review nurses.

**AMD / Gemma hook:** `gemma-3-27b-it` on MI300X via `rocm/vllm`. **Decouple the two calls:** (1) plain vision transcription of the fax; (2) a *separate text-only* guided-JSON verdict with per-criterion `found/partial/not_found` + cited chart span + policy span (removes vision+xgrammar composition risk). **Cut Qdrant/RAG** — 3-4 policies fit in context; retrieval becomes a dropdown. Logprobs let it abstain on low-confidence criteria instead of hallucinating.

**Why self-host beats an API:** PHI + payer-contract data is the hardest data-sovereignty wall; the vision step means the raw chart image (maximal PHI) would otherwise leave the building. Easier to run inside the hospital VPC than to drag a cloud LLM vendor into the compliance boundary.

**5-day plan:** Day 0 gate/provision. Day 1-2 serve + vision-transcribe + JSON verdict on ONE golden scenario (lumbar-MRI conservative-therapy). Day 3 citation side-by-side + extractive grounding ("no span located → MISSING_DOCUMENTATION, never a guess"). Day 4 appeal-letter + drag-a-fax UI. Day 5 record (front the live URL with a cheap CPU frontend that warms the GPU).

**Demo moment:** Drag a messy fax → *"DO NOT SUBMIT — 1 of 6 criteria unmet."* Split screen: criterion 3 red ("NO GROUNDING SPAN FOUND — not inferring approval"), met criteria green with quoted chart sentences. Feed a second chart where therapy *is* documented → criterion turns green. Close: *"PHI never left this box — open-source, self-hosted on AMD."*

**#1 risk + mitigation:** crowded (Waystar AltitudeAI, Tennr, Anterior, Cohere Health) + hallucination liability. → Re-target the **under-resourced provider** (independent practices, rural/FQHCs), pivot headline to **pre-submission prevention**, make **extractive grounding** the credibility centerpiece — quote an exact span or abstain.

## #7 — RedactRadar  ·  score 76
*Creativity 7 · Market 7.3 · Completeness 6 · AMD-depth 8.3 · Gemma-bonus 9*

**One-liner:** Feed it a batch of records for public release and the screen fills with color-coded redaction boxes, each labeled with the exact statutory exemption — reasoning-based, confidence-scored, fully offline.

**Concept:** Agencies/universities/litigants must redact records before release under FOIA/state law, citing the specific exemption for every redaction. RedactRadar proposes redactions with the statutory basis for each, scores confidence per span (low-confidence routes to a human), and exports both the redacted PDF and a defensible release memo listing every exemption applied. Reasoning-based, citation-carrying — not regex/PII pattern matching. *(Note: overlaps heavily with Sunshine; pick one FOIA-redaction play, not both.)*

**Target user:** Agency FOIA officers, records/legal-ops teams, litigation support.

**AMD / Gemma hook:** `gemma-3-27b-it` on MI300X via `rocm/vllm`; two self-host-only levers: constrained decoding for exact spans + exemption codes, and **per-token logprobs** for calibrated per-redaction confidence (the audit trail that makes a redaction defensible). Continuous batching pushes thousands of pages per run; Gemma-3 vision reads photocopied records.

**Why self-host beats an API:** the records are precisely the sensitive material agencies are forbidden from shipping to a commercial cloud; many operate air-gapped. Logprob confidence + constrained output give documented human-in-the-loop defensibility a black-box API can't.

**5-day plan:** Day 1 rocm/vllm + Gemma (chat+vision+guided). Day 2 PDF/scan → vision transcription with character offsets. Day 3 exemption chain → `{span, exemption_code, rationale, confidence}` + threshold routing. Day 4 color-coded annotation UI + redacted-PDF + release-memo export. Day 5 seed public samples with a planted SSN, record. Ship b(6)/b(7)(C)/b(5) well rather than all nine.

**Demo moment:** Load a batch; the viewer fills with color-coded boxes; hover shows the statute; a planted SSN is caught and boxed automatically; one click exports the redacted PDF + release memo — 'air-gapped' indicator lit.

**#1 risk + mitigation:** false negatives on sensitive spans. → conservative thresholds + mandatory review of low-confidence + a PII-regex safety net *under* the model; verify vision offset alignment for accurate boxes.

## #8 — RedactionRoom  ·  score 76
*Creativity 6 · Market 7.7 · Completeness 6.3 · AMD-depth 8.7 · Gemma-bonus 9*

**One-liner:** Drag a folder of scanned medical/legal documents onto an on-prem box and get them fully redacted without a single byte leaving the building — the one thing a cloud API is legally forbidden to do.

**Concept:** A one-command, air-gapped document de-identification appliance for regulated industries. Ingests scanned PDFs/images, uses Gemma 3 vision to read typed/semi-structured layouts, extracts structured PHI/PII spans (name, MRN, DOB, address, account numbers), renders redacted copies + an audit log. **The wedge:** hospitals/law firms/health-tech need to de-identify data to build/share datasets, but sending raw PHI to a hosted API is a compliance non-starter. *(Note: near-duplicate of Safe Harbor + Inkout; Safe Harbor is the stronger representative of this cluster.)*

**Target user:** Hospital IT/compliance, legal e-discovery, insurers, health-tech startups.

**AMD / Gemma hook:** `gemma-3-27b-it` via `rocm/vllm` on one MI300X; 192GB HBM3 holds the multimodal model + a large continuous-batch of page images with zero tensor-parallel sharding; ~5.3TB/s bandwidth makes million-page batch jobs finish in hours on one node. Hybrid OCR (Tesseract/pdfplumber) maps spans back to pixel coordinates for reliable boxing (don't trust the model for geometry).

**Why self-host beats an API:** legal impossibility, not cost — HIPAA/GDPR/BAAs prohibit shipping raw PHI to a third-party endpoint, and de-identification is the step that must happen *before* data can move. Air-gapped AMD is compliant by construction + gives an auditable redaction trail.

**5-day plan:** Day 1 MI300X + rocm/vllm vision confirmed + FastAPI. Day 2 ingestion + strict-JSON PHI spans + OCR pixel-mapping. Day 3 redaction renderer + batch queue + audit log. Day 4 drop-a-folder UI + egress monitor + cost/compliance panel. Day 5 compose + README + video.

**Demo moment:** Drag 500 scanned records; a throughput counter redacts them live; then show the box's egress firewall at zero external requests during the whole run: *"This is not the cheaper way to do it. It's the only legal way."*

**#1 risk + mitigation:** PHI recall (false negatives) — tune for high recall + human-in-the-loop + audit log; VLM-to-pixel accuracy → OCR-span-mapping hybrid; scope demo to typed/printed records, handwriting = roadmap.

---

# Other generated ideas (not in scored top-8)

*Strong concepts that lost on completeness risk, crowding, or a weaker AMD hook — kept for reference and idea-mining.*

## Vigil — Multimodal On-Call Root-Cause Copilot  *(lens: devtools)*
**One-liner:** An air-gapped SRE copilot where an on-call engineer pastes a screenshot of a spiking dashboard/flame graph and Gemma 3 vision names the exact git commit that caused the regression, plus a fix, in under 10 seconds.
**Hook:** `gemma-3-27b-it` multimodal on MI300X (`rocm/vllm`, `--limit-mm-per-prompt image=4`); base64 image inline; `guided_json` forces `{hypothesis, culprit_commit, confidence, fix}`; correlates chart inflection vs a RAG index of recent git log + deploy timeline + runbooks.
**Self-host:** incident telemetry (internal metric screenshots, traces with customer PII, proprietary source in the git RAG) is the most sensitive data an enterprise owns; an outage is the worst time to depend on a rate-limited external endpoint.
**Demo:** drag a Grafana latency-cliff screenshot → ~8s later it highlights the knee, prints "caused by commit a3f21b — unbounded retry loop deployed 4 min earlier," deep-links the diff.
**Judges' knock:** the vision path may not be load-bearing — if you pass the alert's numeric time window as text, the real correlation is timestamp-diffing that needs no VLM. Panel scored ~73-78; "screenshot paste" reads as a gimmick vs querying Prometheus directly.

## Overhaul — Whole-Repo Migration Agent  *(lens: devtools)*
**One-liner:** Point it at a private monorepo and a migration goal (Pydantic v1→v2, Py2→3, deprecated SDK→new) and it batch-transforms every affected file, runs the tests, and self-repairs failures until the suite is green — on your own GPU.
**Hook:** `gemma-3-27b-it` on `rocm/vllm` tuned for throughput (high `--max-num-seqs`), guided grammar decoding forcing a strict unified-patch schema; the live throughput meter (thousands of tok/s) is literally an AMD showcase.
**Self-host:** a 200k-LOC repo migration is tens of millions of tokens across a generate→run→repair loop (expensive + throttled on a metered API); the whole proprietary codebase would have to stream to a third party.
**Demo:** dashboard climbs "0/214 files → 214/214, 100% green" in a couple minutes while a throughput gauge pins at thousands of tok/s.
**Judges' knock:** the self-repair loop **converging to 100%-green live is the exact part most likely to break on stage**, and gemma-3-27b-it is a mid-tier code editor (lags Qwen-Coder/DeepSeek-Coder). Cap retries, scope to one deterministic migration, mark unresolved files for human review.

## Blastradius — Air-Gapped CVE Reachability Triage  *(lens: devtools)*
**One-liner:** When a new CVE drops in a dependency, it reasons over your actual usage sites to decide whether it's genuinely reachable in your code — turning a 40-alert wall of red into the 1 that matters, entirely on-prem.
**Hook:** `gemma-3-27b-it` on `rocm/vllm` as an always-on internal service; one `guided_json` call per (CVE × call-site cluster) → `{reachable, rationale, severity_in_context}`; long context fits advisory + all call sites in one prompt.
**Self-host:** your source + which CVEs you're exposed to and haven't patched is the highest-value target an attacker could ask for; air-gapped is a hard procurement gate for defense/fintech/healthcare.
**Demo:** 40 CVEs all "critical"; inject a new advisory → the board re-sorts within seconds to surface exactly 1 as "reachable in your code," greying out 39.
**Judges' knock:** true reachability needs call-graph analysis; grep+AST misses indirect paths and a false negative in AppSec is catastrophic. Frame as **triage/prioritization signal, not a soundness guarantee**; pin the demo to Python/PyPI where OSV data is clean.

## Inkout — visual-native scanned-doc redactor  *(lens: multimodal)*
**One-liner:** Drag in a crumpled scanned PDF and it paints redaction boxes over every handwritten SSN, signature, face, and stamp, then hands back clean structured JSON — on a GPU that never phones home.
**Hook:** `gemma-3-27b-it` under vLLM (`rocm/vllm`, `--limit-mm-per-prompt image=N`); reasons over pixels rather than an OCR text dump, so it survives skew, handwriting, and non-digital marks; pair Gemma's typed region labels with a Tesseract word-box grid for pixel-accurate boxes.
**Self-host:** HIPAA/GDPR/attorney-client privilege make sending raw PHI/PII to an API a non-starter; unlimited pages with zero per-image fee for bulk backfills.
**Demo:** drag a crumpled skewed handwritten intake form → red boxes snap over the handwritten SSN, signature, face photo, one table cell; counter reads "7 PHI entities redacted, 0 bytes sent to cloud."
**Note:** covers non-textual PII (faces, signatures) text redactors structurally can't — but shares Safe Harbor's bbox risk; grade on recall over box tightness.

## Frameguard — zero-shot job-site safety monitor  *(lens: realtime-cost)*
**One-liner:** Point it at a camera feed and it flags missing hard hats, blocked fire exits, and spills in plain language — zero training data, and not a single frame leaves the building.
**Hook:** `gemma-3-27b-it` on MI300X via `rocm/vllm`; video is a firehose of frames and continuous batching on 192GB HBM3 pushes many fps through one GPU — **the strongest raw AMD-utilization narrative in the pool**; RAG over the site's own safety SOP.
**Self-host:** streaming continuous video to a cloud API is a bandwidth/cost nightmare + a worker-surveillance privacy problem; edge sites have unreliable internet.
**Demo:** play a 30s warehouse clip → a live timeline lights up ("0:07 worker in forklift lane without hi-vis (SOP 4.2)", "0:19 fire exit blocked (SOP 7.1)"); then **edit the rulebook live to add "no phone use on the floor," rerun, new alert appears — no retraining**.
**Note:** near-duplicate of SiteSense; sample at 1-2 fps, curate clear scenarios, accept region-level boxes.

## SiteSense — on-prem visual compliance for physical sites  *(lens: privacy-vertical)*
**One-liner:** Write a safety rule in plain English ("anyone in this zone must wear a hard hat"), point it at your camera feeds, and get instant alerts — on a box on the factory floor, because you can't stream 24/7 workplace video to a cloud API.
**Hook:** Gemma 3 12B/27B vision via `rocm/vllm` on an MI300X edge node; continuous batching fans sampled frames across many concurrent camera streams; policy-as-prompt only works because Gemma reasons over images with no per-class trained model.
**Self-host:** edge necessity on three fronts at once — bandwidth (dozens of feeds), latency (safety alerts can't wait on a round-trip), privacy (factory footage/trade secrets).
**Demo:** live webcam; presenter walks in without a hard hat → instant red alert + one-line reasoning; puts hat on, clears; switch to a 12-camera grid on the one GPU with an fps counter, egress at zero.
**Note:** same family as Frameguard — pick one. Zero-shot "add a rule in English" beat is the originality proof.

## Qualm — the Uncertainty Firewall  *(lens: agentic-infra)*
**One-liner:** A drop-in inference gateway that reads a self-hosted model's own token-level probabilities and cross-sample semantic entropy to block confident hallucinations before they reach users.
**Hook:** `gemma-3-4b-it` (fast sampler) + `gemma-3-27b-it` via `rocm/vllm`; calls vLLM's `logprobs`/`prompt_logprobs` for true per-token distributions; runs all K=10 semantic-entropy samples in ONE batched forward pass — near-free on owned silicon, 10× spend on a metered API.
**Self-host:** hosted APIs expose at most truncated top-k logprobs and never guarantee stable per-token entropy — **the core signal simply isn't available through Fireworks/OpenAI**; K fresh samples per query is 5-10× metered cost but free via batching.
**Demo:** ask a trick question the model answers fluently but wrongly → smooth answer next to a red meter "Doubt 0.87 — BLOCKED" (the 10 internal samples disagreed); then a solid question → identical confident tone, meter flips green "0.05 — PASS."
**Note:** strong intrinsic self-host story (internals-native). Nearest match Cleanlab TLM is a closed hosted API; this is the open, self-hostable version.

## Siege — Adversarial Robustness Gym  *(lens: agentic-infra)*
**One-liner:** A self-hosted red-team gym that runs gradient-based attacks against your own model and guardrails to auto-discover jailbreaks, then exports each break as a regression test.
**Hook:** on one MI300X, `gemma-3-4b-it` as target-under-test in vLLM AND the same 4B loaded in torch/HF for nanoGCG (needs `.backward()` through input embeddings); `gemma-3-27b-it` concurrently as the attack-success judge.
**Self-host:** gradient-based attacks are **mathematically impossible through any API** — GCG needs logits AND backprop to input tokens; a real campaign is thousands of rollouts on your private fine-tuned weights.
**Demo:** point at a chatbot guarded by "never reveal your system prompt"; hit Start → a live counter ticks GCG iterations, loss drops, ~3 min later an auto-discovered gibberish suffix makes the model spill its system prompt live, then drops that string into a "new regression test" card.
**Note:** gradient attacks make the AMD tie-in structural. GCG is slow/tokenizer-sensitive — keep a known-good pre-optimized attack in reserve so the demo never depends on live convergence.

## Tribunal — Always-On Eval Reactor  *(lens: agentic-infra)*
**One-liner:** An observability + eval platform whose LLM-judge is a frozen, self-hosted Gemma, giving reproducible, PII-safe, batch-cheap scoring of every production trace instead of sampling a handful through a drifting API judge.
**Hook:** `gemma-3-27b-it` judge via `rocm/vllm`; continuous batching scores tens of thousands of trace-judgments in minutes; the pinned model directory IS the eval baseline (a frozen, hashable judge artifact); multimodal judge also scores vision traces.
**Self-host:** reproducibility (a hosted judge silently changes versions and invalidates your baseline) + full-volume economics + PII privacy — each independently forces self-hosting.
**Demo:** replay last night's traces; the dashboard flags a silent regression (faithfulness 0.90→0.61) with the 3 offending traces one click away; cost ticker reads "$0.14 self-hosted vs ~$340 via API judge" for 50k judgments; judge version hash stamped on every score.
**Note:** highest crowding risk (Langfuse, Braintrust, Arize Phoenix) — must foreground the frozen-judge/cost/privacy wedge relentlessly.

## Quorum — a 12-expert council on one GPU  *(lens: knowledge-rag)*
**One-liner:** Ask a hard decision and watch a panel of genuinely different fine-tuned Gemma experts debate and dissent — all served as hot-swapped LoRA adapters on a single MI300X, so 12 distinct "brains" cost about the same as one.
**Hook:** vLLM `--enable-lora` multi-LoRA serving — one base Gemma-3 + 6-12 LoRA adapters hot-swapped per request; adapters trained in-house with PEFT on the same MI300X; 192GB HBM3 holds base + all adapters + a large concurrent batch.
**Self-host:** multi-LoRA co-serving has no API equivalent — hosted endpoints won't host your dozen custom adapters cheaply; calling a hosted model N times gives N copies of the SAME weights, not N specialists.
**Demo:** type one gnarly decision; eight named experts (Skeptic, Optimist, Regulator, Customer, domain experts) stream simultaneously in a grid, throw rebuttals, resolve into a one-page brief with a red-highlighted dissent — side panel shows all eight are LoRAs sharing one card.
**Note:** showcases a headline AMD/vLLM capability. Risk: LoRA training quality inside 5 days — keep 4-6 truly-trained adapters, don't fake with prompts.

## InHouse — self-host-first LLM offload gateway  *(lens: privacy-vertical)*
**One-liner:** Change one base_url and 85% of your LLM traffic quietly moves off the metered API onto your own AMD GPU, with a live dashboard ticking up the dollars saved — the frontier API becomes the exception, not the default.
**Hook:** run TWO Gemma 3 on one MI300X under `rocm/vllm` — 4B-it as a sub-100ms difficulty router/judge + 27B-it as the workhorse — sharing the GPU via continuous batching; vLLM's OpenAI-compatible endpoint makes the local path a true drop-in.
**Self-host:** pure cost-arbitrage ownership — marginal cost trends toward electricity instead of a per-token toll that grows with success; prompts stay in-VPC; immune to provider rate limits/outages. The most literal "the AMD GPU is the pitch."
**Demo:** point a real unmodified chatbot at the gateway, fire 1,000 mixed requests → dashboard climbs "$412 saved · 87% served on your AMD GPU · 0 requests leaked" while latency stays flat; flip the threshold slider and watch the mix + savings move live.
**Note:** competitors (RouteLLM, Martian, OpenRouter, LiteLLM) route BETWEEN clouds; InHouse's default backend is YOUR GPU. Core risk: a trustworthy difficulty classifier in 5 days + honest quality parity.

## DataRoom Diligence Copilot — air-gapped M&A due-diligence  *(lens: knowledge-rag)*
**One-liner:** Point it at a virtual data room and ask "where's our change-of-control exposure?" — it synthesizes a cited answer across 300 confidential contracts in seconds, on a box that data never leaves.
**Hook:** MI300X's 192GB HBM3 is intrinsic — vLLM holds `gemma-3-27b-it` + a very large KV cache so you can stuff 100K+ tokens into Gemma 3's 128K context and reason **across** documents in one shot instead of chaining tiny API calls; Gemma-3 vision handles scanned exhibit/signature pages.
**Self-host:** a data room is legally defined by confidentiality (NDAs, clean-team protocols, MNPI/insider-trading rules); counsel won't pipe the target's crown-jewel contracts through a third-party cloud LLM.
**Demo:** point at a 300-doc folder, ask "What is our change-of-control exposure?" → one answer citing specific clauses across a dozen contracts with clickable page links; counter shows "2.1M tokens, 300 docs, 0 left this machine"; the red-flag radar lights up an anti-assignment clause nobody flagged.
**Note:** cross-document synthesis (vs per-document clause extraction from Kira/Luminance/Evisort) is the wedge. Risk: retrieval quality on large heterogeneous corpora + long-context latency tuning.

## Ref — the AI that watches your game and calls it live  *(lens: wildcard)*
**One-liner:** Point a webcam at a real card/board game and Gemma referees in real time — reading the table, catching illegal moves, keeping score, and trash-talking — powered by continuous vision that only makes economic sense when self-hosted.
**Hook:** Gemma-3 vision (12B for latency) on MI300X via vLLM multimodal; FastAPI ingests webcam frames over websocket/WebRTC, samples keyframes, guided decoding forces board-state JSON; 192GB HBM3 enables **3-5× redundant frame sampling per decision + majority-vote** — reliability bought with volume that only self-hosting affords.
**Self-host:** continuous vision means thousands of frames — per-image API pricing makes always-on watching absurd and round-trips break real-time; the multi-frame majority-vote (the reliability trick) is only free on owned silicon.
**Demo:** a real hand is played; someone sneaks an illegal move → Ref buzzes within a beat ("Illegal: red 7 can't take a +2"), updates the scoreboard, quips — with a "sampled 5 frames, voted" badge proving it runs on one on-device MI300X.
**Note:** pure playful-but-viable novelty, worlds from the code-review space; the engine generalizes to sports officiating, retail shelf/lab-safety monitoring, eldercare. Risk: vision reliability under real lighting/motion/occlusion — constrain to a discrete-state game, controlled lighting.

---

## Bottom line

- **Build Spillguard.** It's the only high-scoring idea that is simultaneously most-likely-to-work-on-stage (text classification, no pixel geometry), load-bearing on AMD (self-host is a legal necessity + 192GB HBM3 earns its keep), and anchored by an un-fakeable one-screen demo.
- **Fallback if you want the bigger, more sympathetic market:** Safe Harbor — but only if you commit to the OCR-for-geometry pivot and accept healthcare's all-or-nothing failure mode.
- **Do NOT build the PR Gatekeeper.** Verified crowded (8+ incumbents) and its core mechanism (full-codebase-RAG PR review) is already commoditized by Greptile; it has no intrinsic reason to self-host, structurally capping AMD-depth and the $2K bonus.
