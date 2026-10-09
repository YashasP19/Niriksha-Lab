import type { AnalysisResult, TemplateStatus } from "../types";

const BASE = "/api";

export async function uploadTemplate(
  file: File
): Promise<{ status: string; message: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/template`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Template upload failed: ${res.statusText}`);
  return res.json();
}

export async function getTemplateStatus(): Promise<TemplateStatus> {
  const res = await fetch(`${BASE}/template`);
  if (!res.ok) throw new Error(`Failed to get template status: ${res.statusText}`);
  return res.json();
}

export async function analyzeImage(file: File): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/analyze`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Analysis failed: ${res.statusText}`);
  return res.json();
}
