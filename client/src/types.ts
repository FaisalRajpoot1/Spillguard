// Mirror of the server's data contract (app/schemas.py).

export type Verdict = "ALLOW" | "FLAG" | "BLOCK";

export type ClassificationLevel =
  | "UNCLASSIFIED"
  | "CUI"
  | "CUI//SP"
  | "CLASSIFIED";

export type CUICategory = "CTI" | "PRVCY" | "EXPT" | "PROCURE" | "LEI";

export interface Span {
  text: string;
  category: CUICategory | null;
  reason: string | null;
  start: number | null;
  end: number | null;
}

export interface BaselineResult {
  verdict: Verdict;
  matched_rules: string[];
  note: string;
}

export interface DeterministicSignals {
  banner_markings: string[];
  classified_banner: string | null;
  keyword_categories: CUICategory[];
  ssn_hits: number;
  matched_rules: string[];
}

export interface ModelSignals {
  available: boolean;
  classification_level: ClassificationLevel;
  cui_categories: CUICategory[];
  spillage_flag: boolean;
  offending_spans: Span[];
  rationale: string;
  confidence: number;
}

export interface Signals {
  deterministic: DeterministicSignals;
  model: ModelSignals;
}

export interface ScanResult {
  verdict: Verdict;
  classification_level: ClassificationLevel;
  cui_categories: CUICategory[];
  portion_markings_found: string[];
  portion_markings_expected: string[];
  marking_mismatch: boolean;
  spillage_flag: boolean;
  offending_spans: Span[];
  rationale: string;
  confidence: number;
  engine: string;
  degraded: boolean;
  latency_ms: number;
  baseline: BaselineResult;
  signals: Signals | null;
}

export interface RemediationResponse {
  fixable: boolean;
  note: string;
  remediated_text: string;
  changes: string[];
  result: ScanResult | null; // re-scan of the fixed text
}

export interface AuditEntry {
  id: number;
  ts: string;
  doc_hash: string;
  verdict: Verdict;
  classification_level: ClassificationLevel;
  cui_categories: CUICategory[];
  engine: string;
  degraded: boolean;
  latency_ms: number;
}

export interface EgressStatus {
  backend: string;
  air_gapped: boolean;
  external_bytes: number;
  model_host: string | null;
  message: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  model_backend: string;
  model_name: string;
  degraded_ready: boolean;
}

export interface EvalMetrics {
  accuracy: number;
  recall: number;
  precision: number;
  false_positive_rate: number;
  tp: number;
  fp: number;
  tn: number;
  fn: number;
}

export interface EvalReport {
  available: boolean;
  generated_at?: string;
  backend?: string;
  model?: string;
  n?: number;
  spillguard?: EvalMetrics;
  baseline?: EvalMetrics;
}
