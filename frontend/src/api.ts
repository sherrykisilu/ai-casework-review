export type Evidence = { quote: string; rationale: string };
export type Finding = {
  category: "customer_risk" | "compliance" | "support_quality" | "urgency";
  severity: "low" | "medium" | "high";
  summary: string;
  evidence: Evidence[];
};
export type AnalysisResult = {
  summary: string;
  findings: Finding[];
  recommended_actions: string[];
  limitations: string[];
  confidence: number;
};
export type CaseRecord = {
  id: string;
  title: string;
  source_text: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  result: AnalysisResult | null;
  error_code: string;
  error_message: string;
  trace_id: string;
  deduplicated: boolean;
};

type ApiError = { error?: { detail?: unknown } };

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Token ${token}` } : {}),
      ...init?.headers
    }
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiError;
    throw new Error(JSON.stringify(body.error?.detail ?? "Request failed"));
  }
  return response.json() as Promise<T>;
}

export const api = {
  register(username: string, password: string) {
    return request<{ token: string }>("/api/v1/auth/register/", "", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
  },
  login(username: string, password: string) {
    return request<{ token: string }>("/api/v1/auth/token/", "", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
  },
  submit(token: string, title: string, sourceText: string) {
    return request<CaseRecord>("/api/v1/cases/", token, {
      method: "POST",
      body: JSON.stringify({ title, source_text: sourceText })
    });
  },
  getCase(token: string, id: string) {
    return request<CaseRecord>(`/api/v1/cases/${id}/`, token);
  }
};
