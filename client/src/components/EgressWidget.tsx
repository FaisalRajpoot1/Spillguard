import { motion } from "framer-motion";
import type { EgressStatus } from "../types";

export function EgressWidget({ egress }: { egress: EgressStatus | null }) {
  const safe = egress?.air_gapped ?? true;
  return (
    <section className="panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="label">Egress monitor</span>
        <span
          className={`inline-flex items-center gap-1.5 font-mono text-[11px] ${
            safe ? "text-allow" : "text-flag"
          }`}
        >
          <motion.span
            className={`h-1.5 w-1.5 rounded-full ${safe ? "bg-allow" : "bg-flag"}`}
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 1.8, repeat: Infinity }}
          />
          {safe ? "SEALED" : "OPEN"}
        </span>
      </div>

      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="font-mono text-3xl font-bold text-slate-100">
            0<span className="ml-1 text-sm font-normal text-muted">bytes out</span>
          </div>
          <div className="mt-0.5 font-mono text-[11px] text-muted">
            model host: {egress?.model_host ?? (safe ? "internal-only" : "…")}
          </div>
        </div>
        <NetGlyph safe={safe} />
      </div>

      <p className="mt-3 border-t border-line/60 pt-2.5 text-[11px] leading-relaxed text-muted">
        {egress?.message ??
          "The model runs on an internal-only network with no route to the internet."}
      </p>
    </section>
  );
}

function NetGlyph({ safe }: { safe: boolean }) {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12">
      <circle cx="24" cy="24" r="6" className={safe ? "fill-allow/20" : "fill-flag/20"} />
      <circle cx="24" cy="24" r="6" fill="none" strokeWidth="1.5" className={safe ? "stroke-allow" : "stroke-flag"} />
      {/* the severed wire to the outside */}
      <line x1="30" y1="24" x2="44" y2="24" strokeWidth="1.5" strokeDasharray="3 3" className="stroke-muted" />
      {safe && (
        <line x1="35" y1="19" x2="39" y2="29" strokeWidth="2" strokeLinecap="round" className="stroke-block" />
      )}
    </svg>
  );
}
