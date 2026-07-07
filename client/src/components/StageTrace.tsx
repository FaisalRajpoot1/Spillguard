import { motion } from "framer-motion";
import type { ScanResult } from "../types";

// Visualises the four pipeline stages for a scan, making the engineering
// discipline legible: deterministic checks run first and always; the model
// informs but the decision engine — not the LLM — owns the verdict.

interface StageView {
  index: number;
  name: string;
  summary: string;
  chips: string[];
  tone: "ok" | "warn" | "info";
}

function buildStages(r: ScanResult): StageView[] {
  const det = r.signals?.deterministic;
  const model = r.signals?.model;
  const unmarked = r.cui_categories.length > 0 && r.portion_markings_found.length === 0;

  return [
    {
      index: 1,
      name: "Deterministic pre-check",
      summary: det?.matched_rules.length
        ? `${det.matched_rules.length} literal signal(s)`
        : "no literal markers",
      chips: [
        det?.classified_banner ? `banner: ${det.classified_banner}` : "",
        det?.ssn_hits ? `SSN ×${det.ssn_hits}` : "",
        ...(det?.keyword_categories ?? []).map((c) => `kw:${c}`),
      ].filter(Boolean),
      tone: det?.classified_banner ? "warn" : "info",
    },
    {
      index: 2,
      name: `Semantic scan · ${r.engine}`,
      summary: model?.available
        ? `${r.cui_categories.length} categor${r.cui_categories.length === 1 ? "y" : "ies"}, conf ${(r.confidence * 100).toFixed(0)}%`
        : "unavailable — running degraded",
      chips: r.cui_categories.map((c) => c),
      tone: model?.available ? (r.cui_categories.length ? "warn" : "ok") : "warn",
    },
    {
      index: 3,
      name: "Portion-marking check",
      summary: unmarked
        ? "unmarked CUI — spillage"
        : r.marking_mismatch
          ? "marking mismatch"
          : r.portion_markings_found.length
            ? "correctly marked"
            : "n/a",
      chips: [
        ...r.portion_markings_found.map((m) => `found:${m}`),
        ...(unmarked ? r.portion_markings_expected.map((m) => `need:${m}`) : []),
      ],
      tone: unmarked ? "warn" : r.marking_mismatch ? "warn" : "ok",
    },
    {
      index: 4,
      name: "Decision engine",
      summary: `verdict ${r.verdict}${r.spillage_flag ? " · spillage" : ""} — rules, not the model`,
      chips: [],
      tone: r.verdict === "BLOCK" ? "warn" : r.verdict === "FLAG" ? "info" : "ok",
    },
  ];
}

const TONE: Record<StageView["tone"], string> = {
  ok: "border-allow/40 text-allow",
  warn: "border-block/40 text-block",
  info: "border-signal/40 text-signal",
};

export function StageTrace({ result }: { result: ScanResult }) {
  const stages = buildStages(result);
  return (
    <section className="panel p-5">
      <span className="label">Pipeline trace</span>
      <ol className="mt-3 space-y-0">
        {stages.map((s, i) => (
          <motion.li
            key={s.index}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * i }}
            className="relative flex gap-3 pb-4 last:pb-0"
          >
            {/* connector */}
            {i < stages.length - 1 && (
              <span className="absolute left-[13px] top-7 h-full w-px bg-line" />
            )}
            <span
              className={`z-10 grid h-7 w-7 shrink-0 place-items-center rounded-full border bg-ink-900 font-mono text-xs ${TONE[s.tone]}`}
            >
              {s.index}
            </span>
            <div className="min-w-0 pt-0.5">
              <div className="text-sm text-slate-200">{s.name}</div>
              <div className="text-xs text-muted">{s.summary}</div>
              {s.chips.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {s.chips.map((c, j) => (
                    <code
                      key={j}
                      className="rounded bg-ink-700/70 px-1.5 py-0.5 font-mono text-[10px] text-slate-400"
                    >
                      {c}
                    </code>
                  ))}
                </div>
              )}
            </div>
          </motion.li>
        ))}
      </ol>
    </section>
  );
}
