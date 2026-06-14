import type { QueryResponse, IngestResponse, KnowledgeGap } from './types';

// Get API URL from runtime config or environment or fallback to vite env
const getApiBase = () => {
  if (window.RAMPUP_CONFIG?.VITE_API_URL) {
    return window.RAMPUP_CONFIG.VITE_API_URL;
  }
  return import.meta.env.VITE_API_URL || '';
};

const API_BASE = getApiBase();
const BASE = `${API_BASE}/api`;

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export async function queryKnowledge(question: string): Promise<QueryResponse> {
  const res = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? `API error ${res.status}`);
  }
  return res.json();
}

export async function ingestDocument(
  sourceUrl?: string,
  title?: string,
  text?: string,
  sourceType?: string,
  siteId?: string,
): Promise<IngestResponse> {
  const body: any = {};
  if (text) {
    body.text = text;
    if (sourceUrl) body.source_url = sourceUrl;
    if (title) body.title = title;
  } else if (sourceType && siteId) {
    body.source_type = sourceType;
    body.site_id = siteId;
  } else {
    throw new Error("Either text or source_type and site_id must be provided.");
  }

  const res = await fetch(`${BASE}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? `Ingest failed: ${res.status}`);
  }
  return res.json();
}

export async function listKnowledgeGaps(resolved = false): Promise<KnowledgeGap[]> {
  const res = await fetch(`${BASE}/gaps?resolved=${resolved}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch knowledge gaps: ${res.status}`);
  }
  return res.json();
}
