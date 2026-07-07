import type { AuditEntry } from "../types";
import { verdictMeta } from "../lib/verdict";

function relTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const secs = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  return `${Math.round(mins / 60)}h ago`;
}

export function AuditStrip({ entries }: { entries: AuditEntry[] }) {
  return (
    <section className="panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="label">Audit trail</span>
        <span className="font-mono text-[10px] text-muted">hash · not content</span>
      </div>

      {entries.length === 0 ? (
        <p className="py-3 text-center text-xs text-muted">No scans yet.</p>
      ) : (
        <ul className="space-y-1.5">
          {entries.map((e) => {
            const m = verdictMeta(e.verdict);
            return (
              <li
                key={e.id}
                className="flex items-center gap-2.5 rounded-md border border-line/50 bg-ink-900/40 px-2.5 py-1.5 font-mono text-[11px]"
              >
                <span className={`h-2 w-2 shrink-0 rounded-full ${m.dot}`} />
                <span className={`w-12 shrink-0 font-semibold ${m.text}`}>{e.verdict}</span>
                <span className="flex-1 truncate text-muted" title={e.doc_hash}>
                  {e.doc_hash.slice(0, 10)}…
                </span>
                <span className="shrink-0 text-slate-500">{e.engine}</span>
                <span className="w-14 shrink-0 text-right text-slate-500">{relTime(e.ts)}</span>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
