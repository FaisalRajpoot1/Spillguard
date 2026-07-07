import { motion } from "framer-motion";
import type { RemediationResponse, Verdict } from "../types";
import { verdictMeta } from "../lib/verdict";

interface Props {
  originalVerdict: Verdict;
  data: RemediationResponse;
}

export function RemediationPanel({ originalVerdict, data }: Props) {
  if (!data.fixable) {
    return (
      <motion.section
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="panel border-block/30 p-5"
      >
        <span className="label">Remediation</span>
        <div className="mt-2 flex items-start gap-2 text-sm text-block">
          <span className="mt-0.5">⛔</span>
          <p className="text-slate-300">{data.note}</p>
        </div>
      </motion.section>
    );
  }

  const before = verdictMeta(originalVerdict);
  const after = verdictMeta(data.result?.verdict ?? originalVerdict);

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="panel border-allow/25 p-5"
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="label">Remediated</span>
        {/* before → after */}
        <div className="flex items-center gap-2 font-mono text-sm font-bold">
          <span className={before.text}>{before.label}</span>
          <span className="text-muted">→</span>
          <span className={after.text}>{after.label}</span>
        </div>
      </div>

      {/* what changed */}
      <div className="mb-3 flex flex-wrap gap-1.5">
        {data.changes.map((c, i) => (
          <span key={i} className="chip border-allow/30 text-allow">
            <span>✓</span> {c}
          </span>
        ))}
      </div>

      {/* the compliant version */}
      <div className="rounded-lg border border-line/60 bg-ink-900/60 p-4">
        <FixedText text={data.remediated_text} />
      </div>

      <p className="mt-2 text-xs text-muted">
        Spillguard produced a compliant version — sensitive values redacted and
        the required marking applied. Verify the destination is authorised before
        sending.
      </p>
    </motion.section>
  );
}

/** Render the remediated text with added markings and redactions highlighted. */
function FixedText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <pre className="whitespace-pre-wrap break-words font-mono text-[13px] leading-relaxed text-slate-300">
      {lines.map((line, i) => {
        const isMarking = /^CUI\/\//.test(line.trim());
        if (isMarking) {
          return (
            <span key={i} className="rounded-sm bg-allow/15 px-1 font-semibold text-allow ring-1 ring-allow/30">
              {line}
              {i < lines.length - 1 ? "\n" : ""}
            </span>
          );
        }
        return <RedactedLine key={i} line={line + (i < lines.length - 1 ? "\n" : "")} />;
      })}
    </pre>
  );
}

function RedactedLine({ line }: { line: string }) {
  const parts = line.split(/(\[SSN REDACTED\]|\[[A-Z ]+REDACTED\])/g);
  return (
    <>
      {parts.map((p, i) =>
        /REDACTED\]/.test(p) ? (
          <span key={i} className="rounded-sm bg-allow/15 px-1 font-semibold text-allow ring-1 ring-allow/30">
            {p}
          </span>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  );
}
