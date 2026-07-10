import { motion } from "framer-motion";
import type { EgressStatus, HealthResponse } from "../types";

interface Props {
  health: HealthResponse | null;
  egress: EgressStatus | null;
}

export function Header({ health, egress }: Props) {
  // Recording toggle: localhost:8000/?clean=1 hides the backend badge
  // (so the "mock" dev label isn't on camera). The egress pill stays.
  const clean =
    typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("clean") === "1";

  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-line/70 px-6 py-4">
      <div className="flex items-center gap-3">
        <ShieldMark />
        <div className="leading-tight">
          <div className="font-mono text-lg font-semibold tracking-[0.22em] text-slate-100">
            SPILL<span className="text-signal">GUARD</span>
          </div>
          <div className="label -mt-0.5">Data-Spillage Guard</div>
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        {!clean && <BackendBadge health={health} />}
        <EgressPill egress={egress} />
      </div>
    </header>
  );
}

function ShieldMark() {
  return (
    <div className="relative grid h-10 w-10 place-items-center">
      <motion.span
        className="absolute inset-0 rounded-lg border border-signal/40"
        animate={{ opacity: [0.35, 0.9, 0.35] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
      />
      <svg viewBox="0 0 24 24" className="h-6 w-6 text-signal" fill="none">
        <path
          d="M12 2 4 5v6c0 4.5 3.2 8.4 8 11 4.8-2.6 8-6.5 8-11V5l-8-3Z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path d="m8.5 12 2.4 2.4L15.8 9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

function BackendBadge({ health }: { health: HealthResponse | null }) {
  const backend = health?.model_backend ?? "…";
  const isLocal = backend === "vllm-local";
  const isMock = backend === "mock";
  const tone = isLocal
    ? "border-allow/40 text-allow"
    : isMock
      ? "border-line text-muted"
      : "border-flag/40 text-flag";
  const label = isLocal ? "AMD · self-hosted" : isMock ? "mock" : backend;
  return (
    <span className={`chip ${tone}`} title={health?.model_name ?? ""}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}

function EgressPill({ egress }: { egress: EgressStatus | null }) {
  if (!egress) return <span className="chip">egress …</span>;
  const safe = egress.air_gapped;
  return (
    <span
      className={`chip ${safe ? "border-allow/40 text-allow" : "border-flag/40 text-flag"}`}
      title={egress.message}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${safe ? "bg-allow animate-pulse-ring" : "bg-flag"}`} />
      {safe ? "AIR-GAPPED · 0 B out" : "CLOUD FALLBACK"}
    </span>
  );
}
