import type {
  Agent,
  AgentDetail,
  TestResultsResponse,
  AgentStatusResponse,
  Report,
  Certificate,
} from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Agents
  uploadAgent: async (file: File): Promise<Agent> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_URL}/api/agents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Upload failed: ${res.status}`);
    }
    return res.json() as Promise<Agent>;
  },

  listAgents: (): Promise<Agent[]> => fetchJson<Agent[]>('/api/agents'),

  getAgent: (id: string): Promise<AgentDetail> =>
    fetchJson<AgentDetail>(`/api/agents/${id}`),

  deleteAgent: (id: string): Promise<{ message: string }> =>
    fetchJson(`/api/agents/${id}`, { method: 'DELETE' }),

  // Tests
  runTests: (id: string): Promise<{ message: string; agent_id: string; status: string }> =>
    fetchJson(`/api/agents/${id}/run`, { method: 'POST' }),

  getStatus: (id: string): Promise<AgentStatusResponse> =>
    fetchJson<AgentStatusResponse>(`/api/agents/${id}/status`),

  getResults: (id: string): Promise<TestResultsResponse> =>
    fetchJson<TestResultsResponse>(`/api/agents/${id}/results`),

  // Reports
  getReport: (id: string): Promise<Report> =>
    fetchJson<Report>(`/api/agents/${id}/report`),

  getCertificate: (id: string): Promise<Certificate> =>
    fetchJson<Certificate>(`/api/agents/${id}/certificate`),
};
