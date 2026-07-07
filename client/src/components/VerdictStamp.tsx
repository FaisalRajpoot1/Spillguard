import { motion } from "framer-motion";
import type { ScanResult } from "../types";
import { verdictMeta } from "../lib/verdict";

export function VerdictStamp({ result }: { result: ScanResult }) {
  const m = verdictMeta(result.verdict);
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, rotate: -1.5 }}
      animate={{ opacity: 1, scale: 1, rotate: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 18 }}
      className={`relative flex items-center gap-4 rounded-xl border ${m.border} ${m.glow} bg-ink-900/60 px-5 py-4`}
    >
      <div
        className={`grid h-14 w-14 shrink-0 place-items-center rounded-lg border ${m.border} font-mono text-2xl font-bold ${m.text}`}
      >
        {m.glyph}
      </div>
      <div className="min-w-0">
        <div className={`font-mono text-2xl font-bold tracking-wide ${m.text}`}>
          {m.label}
        </div>
        <div className="text-sm text-slate-400">{m.tagline}</div>
      </div>
      <div className="ml-auto text-right">
        <div className="label">Classification</div>
        <div className="font-mono text-sm text-slate-200">
          {result.classification_level}
        </div>
        {result.degraded && (
          <div className="mt-1 font-mono text-[10px] uppercase tracking-wider text-flag">
            degraded scan
          </div>
        )}
      </div>
    </motion.div>
  );
}
