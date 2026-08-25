import type { AnalysisResult } from "../types/analysis";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

class APIError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function handleResponse(res: Response) {
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // ignore json parse failure
    }
    throw new APIError(detail, res.status);
  }
  return res.json();
}

export async function analyzeText(text: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/api/analyze/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return handleResponse(res);
}

export async function analyzeURL(url: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/api/analyze/url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return handleResponse(res);
}

export async function analyzeCombined(text: string, url: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/api/analyze/combined`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text || undefined, url: url || undefined }),
  });
  return handleResponse(res);
}

export async function analyzeImage(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/analyze/image`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return handleResponse(res);
}

export { APIError };
