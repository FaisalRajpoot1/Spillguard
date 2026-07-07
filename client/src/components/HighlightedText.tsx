import type { ReactNode } from "react";
import type { Span } from "../types";

interface Props {
  text: string;
  spans: Span[];
}

interface Range {
  start: number;
  end: number;
  reason: string | null;
  category: string | null;
}

// Resolve each span to a character range, falling back to a substring search
// when the server didn't supply offsets. Overlaps are merged so the render is
// always well-formed.
function resolveRanges(text: string, spans: Span[]): Range[] {
  const raw: Range[] = [];
  for (const s of spans) {
    let start = s.start ?? -1;
    let end = s.end ?? -1;
    if ((start < 0 || end < 0 || end > text.length) && s.text) {
      const idx = text.indexOf(s.text);
      if (idx >= 0) {
        start = idx;
        end = idx + s.text.length;
      }
    }
    if (start >= 0 && end > start && end <= text.length) {
      raw.push({ start, end, reason: s.reason, category: s.category });
    }
  }
  raw.sort((a, b) => a.start - b.start);

  const merged: Range[] = [];
  for (const r of raw) {
    const last = merged[merged.length - 1];
    if (last && r.start <= last.end) {
      last.end = Math.max(last.end, r.end);
      last.reason = last.reason ?? r.reason;
      last.category = last.category ?? r.category;
    } else {
      merged.push({ ...r });
    }
  }
  return merged;
}

export function HighlightedText({ text, spans }: Props) {
  const ranges = resolveRanges(text, spans);

  if (ranges.length === 0) {
    return (
      <pre className="whitespace-pre-wrap break-words font-mono text-[13px] leading-relaxed text-slate-300">
        {text}
      </pre>
    );
  }

  const nodes: ReactNode[] = [];
  let cursor = 0;
  ranges.forEach((r, i) => {
    if (cursor < r.start) nodes.push(<span key={`t${i}`}>{text.slice(cursor, r.start)}</span>);
    nodes.push(
      <mark
        key={`m${i}`}
        title={r.reason ?? undefined}
        className="rounded-sm bg-block/20 px-0.5 text-block underline decoration-block/60 decoration-wavy underline-offset-4 ring-1 ring-block/40"
      >
        {text.slice(r.start, r.end)}
      </mark>,
    );
    cursor = r.end;
  });
  if (cursor < text.length) nodes.push(<span key="tail">{text.slice(cursor)}</span>);

  return (
    <pre className="whitespace-pre-wrap break-words font-mono text-[13px] leading-relaxed text-slate-300">
      {nodes}
    </pre>
  );
}
