// API client for the FastAPI backend

import type { DocumentSource } from '@/types/chat';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

export interface SuggestResponse {
  suggestions: string[];
}

export interface AnswerResponse {
  answer: string;
  sources: Array<{
    item_uuid?: string | null;
    title: string;
    snippet?: string | null;
  }>;
}

export interface GenerateQueryRequest {
  prompt: string;
}

export interface GenerateQueryResponse {
  results: Record<string, unknown>;
  generated_query: unknown;
}

export interface SearchRequest {
  query: Record<string, unknown>;
}

export interface SearchResponse {
  results: Record<string, unknown>;
}

/** GET /api/suggest?q=...&limit=8 */
export async function fetchSuggestions(query: string, limit = 8): Promise<string[]> {
  const res = await fetch(`${API_BASE}/suggest?q=${encodeURIComponent(query)}&limit=${limit}`);
  if (!res.ok) throw new Error('Suggest failed');
  const data: SuggestResponse = await res.json();
  return data.suggestions || [];
}

/** POST /api/answer { query } */
export async function fetchAnswer(query: string): Promise<{ answer: string; sources: DocumentSource[] }> {
  const res = await fetch(`${API_BASE}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error('Answer failed');
  const data: AnswerResponse = await res.json();

  const mappedSources: DocumentSource[] = (data.sources || []).map((source) => ({
    id: source.item_uuid || crypto.randomUUID(),
    title: source.title,
    snippet: source.snippet || undefined,
  }));

  return { answer: data.answer, sources: mappedSources };
}

/** POST /api/generate-query { prompt } */
export async function generateQuery(prompt: string): Promise<GenerateQueryResponse> {
  const res = await fetch(`${API_BASE}/generate-query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error('Generate query failed');
  return res.json();
}

/** POST /api/search { query } */
export async function searchDocuments(query: Record<string, unknown>): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error('Search failed');
  return res.json();
}
