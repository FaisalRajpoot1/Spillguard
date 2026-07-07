import { motion } from "framer-motion";
import type { EvalReport } from "../types";

const pct = (v: number | undefined) => `${Math.round((v ?? 0) * 100)}%`;

export function AccuracyTile({ report }: { report: EvalReport | null }) {
  if (!report?.available || !report.spillguard || !report.baseline) return null;

  const sg = report.spillguard;
  const bl = report.baseline;
  const multiple =
    bl.recall > 0 ? (sg.recall / bl.recall).toFixed(1) : null;

  return (
    <section className="panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="label">Field evaluation</span>
        <span className="font-mono text-[11px] text-muted">
          {report.n} docs · {report.backend}
        </span>
      </div>

      {/* Headline: spillage recall, Spillguard vs legacy */}
      <div className="mb-4">
        <div className="mb-1 flex items-baseline justify-between">
          <span className="text-xs text-muted">Spillage caught</span>
          {multiple && (
            <span className="font-mono text-[11px] text-signal">
              {multiple}× legacy
            </span>
          )}
        </div>
        <RecallBar label="Spillguard" value={sg.recall} tone="bg-signal" strong />
        <RecallBar label="Legacy DLP" value={bl.recall} tone="bg-muted/50" />
      </div>

      {/* Three headline stats */}
      <div className="grid grid-cols-3 gap-2 border-t border-line/60 pt-3">
        <Stat label="Accuracy" value={pct(sg.accuracy)} good />
        <Stat label="False alarms" value={pct(sg.false_positive_rate)} good={sg.false_positive_rate === 0} />
        <Stat label="Missed" value={String(sg.fn)} good={sg.fn === 0} />
      </div>
    </section>
  );
}

function RecallBar({
  label,
  value,
  tone,
  strong,
}: {
  label: string;
  value: number;
  tone: string;
  strong?: boolean;
}) {
  return (
    <div className="mb-1.5 flex items-center gap-2">
      <span className={`w-20 shrink-0 text-[11px] ${strong ? "text-slate-200" : "text-muted"}`}>
        {label}
      </span>
      <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-ink-700">
        <motion.div
          className={`h-full rounded-full ${tone}`}
          initial={{ width: 0 }}
          animate={{ width: `${Math.round(value * 100)}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
      <span className={`w-9 shrink-0 text-right font-mono text-[11px] ${strong ? "text-signal" : "text-muted"}`}>
        {pct(value)}
      </span>
    </div>
  );
}

function Stat({ label, value, good }: { label: string; value: string; good?: boolean }) {
  return (
    <div className="text-center">
      <div className={`font-mono text-lg font-bold ${good ? "text-allow" : "text-slate-200"}`}>
        {value}
      </div>
      <div className="text-[10px] uppercase tracking-wider text-muted">{label}</div>
    </div>
  );
}
