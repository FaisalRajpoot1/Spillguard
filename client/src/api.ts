// Thin API client. Uses same-origin relative paths (proxied in dev by Vite,
// served by FastAPI in prod). Every failure surfaces a human-readable message.

import type {
  AuditEntry,
  EgressStatus,
  EvalReport,
  HealthResponse,
  ScanResult,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseError(res: Response): Promise<never> {
  let message = `Request failed (${res.status})`;
  let code: string | undefined;
  try {
    const body = await res.json();
    if (body?.message) message = body.message;
    if (body?.error) code = body.error;
  } catch {
    /* non-JSON error body — keep the default message */
  }
  throw new ApiError(message, res.status, code);
}

async function requestJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(input, init);
  } catch {
    // Network-level failure (server down, connection refused, etc.)
    throw new ApiError(
      "Cannot reach the Spillguard service. Is the server running?",
      0,
    );
  }
  if (!res.ok) await parseError(res);
  return (await res.json()) as T;
}

export function scanText(text: string, signal?: AbortSignal): Promise<ScanResult> {
  return requestJson<ScanResult>("/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal,
  });
}

export function scanFile(file: File, signal?: AbortSignal): Promise<ScanResult> {
  const form = new FormData();
  form.append("file", file);
  return requestJson<ScanResult>("/scan/file", {
    method: "POST",
    body: form,
    signal,
  });
}

export function getEgress(): Promise<EgressStatus> {
  return requestJson<EgressStatus>("/egress-status");
}

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

export function getAudit(limit = 8): Promise<AuditEntry[]> {
  return requestJson<AuditEntry[]>(`/audit?limit=${limit}`);
}

export async function getEvalReport(): Promise<EvalReport | null> {
  try {
    return await requestJson<EvalReport>("/eval-report");
  } catch {
    return null; // tile simply won't render
  }
}
