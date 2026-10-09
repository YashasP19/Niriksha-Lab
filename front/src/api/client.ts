import type {
  AnalysisResult,
  DemoCaseResponse,
  ModelsResponse,
  OrchestrationRequest,
  OrchestrationResponse,
  TemplateStatus,
  UploadedOrchestrationRequest,
} from '../types/api';

const BASE = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  models: () => request<ModelsResponse>('/models'),

  demoCase: () => request<DemoCaseResponse>('/demo-case'),

  orchestrate: (req: OrchestrationRequest) =>
    request<OrchestrationResponse>('/orchestrate', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  orchestrateUploaded: (req: UploadedOrchestrationRequest) =>
    request<OrchestrationResponse>('/orchestrate/uploaded', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  orchestrateDemo: (model?: string) =>
    request<OrchestrationResponse>('/orchestrate/demo', {
      method: 'POST',
      body: JSON.stringify({ model, include_raw_agent_payloads: true }),
    }),

  analysisTemplate: () => request<TemplateStatus>('/analysis/template'),

  analyze: async (file: File): Promise<AnalysisResult> => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/analysis/analyze`, { method: 'POST', body: form });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`${res.status}: ${body}`);
    }
    return res.json();
  },
};
