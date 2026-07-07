import type { CUICategory, Verdict } from "../types";

interface VerdictMeta {
  label: string;
  glyph: string;
  tagline: string;
  text: string;
  border: string;
  glow: string;
  dot: string;
  bar: string;
}

export const VERDICT_META: Record<Verdict, VerdictMeta> = {
  ALLOW: {
    label: "ALLOW",
    glyph: "✓",
    tagline: "Cleared to send",
    text: "text-allow",
    border: "border-allow/40",
    glow: "shadow-glow-allow",
    dot: "bg-allow",
    bar: "bg-allow",
  },
  FLAG: {
    label: "FLAG",
    glyph: "!",
    tagline: "Hold for review",
    text: "text-flag",
    border: "border-flag/40",
    glow: "shadow-glow-flag",
    dot: "bg-flag",
    bar: "bg-flag",
  },
  BLOCK: {
    label: "BLOCK",
    glyph: "✕",
    tagline: "Spillage prevented",
    text: "text-block",
    border: "border-block/40",
    glow: "shadow-glow-block",
    dot: "bg-block",
    bar: "bg-block",
  },
};

export const CATEGORY_META: Record<CUICategory, { name: string; marking: string }> = {
  CTI: { name: "Controlled Technical Information", marking: "CUI//SP-CTI" },
  PRVCY: { name: "Privacy / PII", marking: "CUI//SP-PRVCY" },
  EXPT: { name: "Export Controlled (ITAR/EAR)", marking: "CUI//SP-EXPT" },
  PROCURE: { name: "Procurement Sensitive", marking: "CUI//SP-PROCURE" },
  LEI: { name: "Law Enforcement Info", marking: "CUI//SP-LEI" },
};

export function verdictMeta(v: Verdict): VerdictMeta {
  return VERDICT_META[v];
}
