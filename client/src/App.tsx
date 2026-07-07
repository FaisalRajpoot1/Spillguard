import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ApiError, getAudit, getEgress, getEvalReport, getHealth, scanText } from "./api";
import type {
  AuditEntry,
  EgressStatus,
  EvalReport,
  HealthResponse,
  ScanResult,
} from "./types";
import { Header } from "./components/Header";
import { InputConsole } from "./components/InputConsole";
import { ResultPanel } from "./components/ResultPanel";
import { EgressWidget } from "./components/EgressWidget";
import { AccuracyTile } from "./components/AccuracyTile";
import { AuditStrip } from "./components/AuditStrip";
import { SAMPLES } from "./lib/samples";

export default function App() {
  const [text, setText] = useState<string>(SAMPLES[0].text);
  const [inspected, setInspected] = useState<string>("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [egress, setEgress] = useState<EgressStatus | null>(null);
  const [evalReport, setEvalReport] = useState<EvalReport | null>(null);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  function refreshAudit() {
    getAudit(8).then(setAuditEntries).catch(() => {});
  }

  useEffect(() => {
    // Best-effort telemetry; the console still works if these fail.
    getHealth().then(setHealth).catch(() => {});
    getEgress().then(setEgress).catch(() => {});
    getEvalReport().then(setEvalReport).catch(() => {});
    refreshAudit();
  }, []);

  async function handleScan() {
    const payload = text.trim();
    if (!payload || loading) return;

    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setLoading(true);
    setError(null);
    try {
      const res = await scanText(payload, ctrl.signal);
      setResult(res);
      setInspected(payload);
      refreshAudit();
    } catch (e) {
      if ((e as Error).name === "AbortError") return;
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-[1240px] flex-col">
      <Header health={health} egress={egress} />

      <main className="grid flex-1 grid-cols-1 gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
        {/* Left: input + telemetry */}
        <div className="flex flex-col gap-5">
          <div className="min-h-[420px]">
            <InputConsole
              text={text}
              onChange={setText}
              onScan={handleScan}
              loading={loading}
              disabled={loading || !text.trim()}
            />
          </div>
          <EgressWidget egress={egress} />
          <AccuracyTile report={evalReport} />
          <AuditStrip entries={auditEntries} />
        </div>

        {/* Right: results */}
        <div className="min-h-[420px]">
          <AnimatePresence mode="wait">
            {error ? (
              <ErrorState key="err" message={error} />
            ) : result ? (
              <motion.div
                key="res"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <ResultPanel result={result} inspectedText={inspected} />
              </motion.div>
            ) : (
              <EmptyState key="empty" loading={loading} />
            )}
          </AnimatePresence>
        </div>
      </main>

      <footer className="border-t border-line/70 px-6 py-4 text-center text-xs text-muted">
        An AI DLP that phones home to the cloud has already leaked.{" "}
        <span className="text-slate-400">Spillguard has no wire to phone home on.</span>
      </footer>
    </div>
  );
}

function EmptyState({ loading }: { loading: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="panel flex h-full min-h-[420px] flex-col items-center justify-center gap-4 p-8 text-center"
    >
      <ScanIcon active={loading} />
      <div>
        <p className="font-mono text-sm text-slate-300">
          {loading ? "Inspecting document…" : "Awaiting document"}
        </p>
        <p className="mt-1 max-w-xs text-xs text-muted">
          Load a sample or paste text, then hit{" "}
          <span className="text-signal">INSPECT</span> to see the verdict and the
          exact sentences that trigger it.
        </p>
      </div>
    </motion.div>
  );
}

function ScanIcon({ active }: { active: boolean }) {
  return (
    <div className="relative h-16 w-16 overflow-hidden rounded-xl border border-line bg-ink-900/60">
      <div className="absolute inset-0 grid place-items-center font-mono text-2xl text-signal/40">
        ⛨
      </div>
      {active && (
        <div className="absolute inset-x-0 top-0 h-0.5 bg-signal/80 shadow-[0_0_12px_2px_#38e1c4] animate-scan" />
      )}
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="panel flex h-full min-h-[420px] flex-col items-center justify-center gap-3 border-block/30 p-8 text-center"
    >
      <div className="grid h-12 w-12 place-items-center rounded-lg border border-block/40 font-mono text-xl text-block">
        ✕
      </div>
      <p className="font-mono text-sm text-block">Scan failed</p>
      <p className="max-w-xs text-xs text-muted">{message}</p>
    </motion.div>
  );
}
