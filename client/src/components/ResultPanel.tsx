import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ApiError, remediate } from "../api";
import type { RemediationResponse, ScanResult } from "../types";
import { CATEGORY_META, verdictMeta } from "../lib/verdict";
import { HighlightedText } from "./HighlightedText";
import { VerdictStamp } from "./VerdictStamp";
import { StageTrace } from "./StageTrace";
import { RemediationPanel } from "./RemediationPanel";

interface Props {
  result: ScanResult;
  inspectedText: string;
}

export function ResultPanel({ result, inspectedText }: Props) {
  const [rem, setRem] = useState<RemediationResponse | null>(null);
  const [fixing, setFixing] = useState(false);
  const [fixErr, setFixErr] = useState<string | null>(null);

  // Reset remediation whenever a new scan arrives.
  useEffect(() => {
    setRem(null);
    setFixErr(null);
  }, [result]);

  async function onFix() {
    setFixing(true);
    setFixErr(null);
    try {
      setRem(await remediate(inspectedText, result.cui_categories, result.classification_level));
    } catch (e) {
      setFixErr(e instanceof ApiError ? e.message : "Remediation failed.");
    } finally {
      setFixing(false);
    }
  }

  const canFix = result.verdict !== "ALLOW";

  return (
    <div className="flex flex-col gap-4">
      <VerdictStamp result={result} />
      <Comparison result={result} />

      {canFix && !rem && <FixItBar onFix={onFix} fixing={fixing} error={fixErr} />}
      {rem && <RemediationPanel originalVerdict={result.verdict} data={rem} />}

      <StageTrace result={result} />

      <section className="panel p-5">
        <div className="mb-2 flex items-center justify-between">
          <span className="label">Rationale</span>
          <Stats result={result} />
        </div>
        <p className="text-sm leading-relaxed text-slate-300">{result.rationale}</p>
      </section>

      {result.cui_categories.length > 0 && (
        <section className="panel p-5">
          <span className="label">Detected categories</span>
          <div className="mt-2 flex flex-wrap gap-2">
            {result.cui_categories.map((c) => (
              <span key={c} className="chip border-block/30 text-slate-200" title={CATEGORY_META[c].name}>
                <span className="text-block">◆</span> {c}
                <span className="text-muted">· {CATEGORY_META[c].name}</span>
              </span>
            ))}
          </div>
          {(result.portion_markings_found.length > 0 ||
            result.portion_markings_expected.length > 0) && (
            <div className="mt-4 grid grid-cols-2 gap-3 border-t border-line/60 pt-3">
              <Markings label="Markings found" items={result.portion_markings_found} tone="text-slate-300" empty="none" />
              <Markings label="Markings expected" items={result.portion_markings_expected} tone="text-signal" empty="—" />
            </div>
          )}
        </section>
      )}

      <section className="panel p-5">
        <span className="label">Inspected text · offending spans highlighted</span>
        <div className="mt-3 max-h-64 overflow-auto rounded-lg border border-line/60 bg-ink-900/60 p-4">
          <HighlightedText text={inspectedText} spans={result.offending_spans} />
        </div>
      </section>
    </div>
  );
}

/** The demo centrepiece: legacy DLP vs Spillguard, side by side. */
function Comparison({ result }: { result: ScanResult }) {
  const fooled =
    result.baseline.verdict === "ALLOW" && result.verdict !== "ALLOW";
  return (
    <section className="panel overflow-hidden">
      <div className="grid grid-cols-2 divide-x divide-line/60">
        <Lane title="Legacy DLP" verdict={result.baseline.verdict} sub={result.baseline.note} dim />
        <Lane title="Spillguard" verdict={result.verdict} sub={`${result.engine}${result.degraded ? " · degraded" : ""}`} />
      </div>
      {fooled && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.35 }}
          className="border-t border-block/30 bg-block/10 px-4 py-2 text-center font-mono text-xs text-block"
        >
          Legacy DLP was fooled — Spillguard caught the spillage.
        </motion.div>
      )}
    </section>
  );
}

function Lane({
  title,
  verdict,
  sub,
  dim,
}: {
  title: string;
  verdict: ScanResult["verdict"];
  sub: string;
  dim?: boolean;
}) {
  const m = verdictMeta(verdict);
  return (
    <div className={`px-4 py-4 ${dim ? "opacity-80" : ""}`}>
      <div className="label mb-2">{title}</div>
      <div className="flex items-center gap-2">
        <span className={`h-2.5 w-2.5 rounded-full ${m.dot}`} />
        <span className={`font-mono text-lg font-bold ${m.text}`}>{m.label}</span>
      </div>
      <div className="mt-1 truncate text-xs text-muted" title={sub}>
        {sub}
      </div>
    </div>
  );
}

function Markings({
  label,
  items,
  tone,
  empty,
}: {
  label: string;
  items: string[];
  tone: string;
  empty: string;
}) {
  return (
    <div>
      <div className="label mb-1.5">{label}</div>
      <div className="flex flex-wrap gap-1.5">
        {items.length ? (
          items.map((m) => (
            <code key={m} className={`rounded bg-ink-700/70 px-1.5 py-0.5 font-mono text-xs ${tone}`}>
              {m}
            </code>
          ))
        ) : (
          <span className="font-mono text-xs text-muted">{empty}</span>
        )}
      </div>
    </div>
  );
}

function Stats({ result }: { result: ScanResult }) {
  return (
    <div className="flex items-center gap-3 font-mono text-[11px] text-muted">
      <span title="model confidence">conf {(result.confidence * 100).toFixed(0)}%</span>
      <span className="text-line">|</span>
      <span title="latency">{result.latency_ms} ms</span>
    </div>
  );
}

function FixItBar({
  onFix,
  fixing,
  error,
}: {
  onFix: () => void;
  fixing: boolean;
  error: string | null;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-signal/25 bg-signal/5 px-4 py-3">
      <div className="min-w-0">
        <div className="text-sm font-medium text-slate-200">Spillguard can fix this</div>
        <div className="text-xs text-muted">
          Redact PII, apply the required marking, and re-scan the compliant version.
        </div>
        {error && <div className="mt-1 text-xs text-block">{error}</div>}
      </div>
      <button
        onClick={onFix}
        disabled={fixing}
        className="focus-signal inline-flex shrink-0 items-center gap-2 rounded-lg border border-signal/50 bg-signal/10 px-4 py-2 font-mono text-sm font-semibold text-signal transition hover:bg-signal/20 disabled:opacity-50"
      >
        {fixing ? (
          <>
            <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-signal/30 border-t-signal" />
            FIXING…
          </>
        ) : (
          <>⚙ FIX IT</>
        )}
      </button>
    </div>
  );
}
