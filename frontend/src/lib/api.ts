import type { AppStatus, Generation, GenerationSettings, Job, Profile, ReferenceVoice } from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, init);
  } catch {
    throw new Error("Sunucuya ulaşılamıyor. Backend'in çalıştığından emin olun.");
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = typeof body?.detail === "string" ? body.detail : `İstek başarısız (HTTP ${res.status}).`;
    throw new Error(detail);
  }
  return body as T;
}

const json = (method: string, data: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

export interface GeneratePayload {
  text: string;
  reference_id: string | null;
  profile_id: string | null;
  settings: GenerationSettings;
}

export interface ProfilePayload {
  name: string;
  reference_id: string | null;
  settings: GenerationSettings;
}

export const api = {
  status: () => request<AppStatus>("/api/status"),
  split: (text: string) => request<{ chunks: string[] }>("/api/text/split", json("POST", { text })),

  references: () => request<ReferenceVoice[]>("/api/references"),
  uploadReference: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    form.append("consent", "true");
    return request<ReferenceVoice>("/api/references", { method: "POST", body: form });
  },
  referenceAudioUrl: (id: string) => `/api/references/${id}/audio`,

  profiles: () => request<Profile[]>("/api/profiles"),
  createProfile: (p: ProfilePayload) => request<Profile>("/api/profiles", json("POST", p)),
  updateProfile: (id: string, p: ProfilePayload) => request<Profile>(`/api/profiles/${id}`, json("PUT", p)),
  deleteProfile: (id: string) => request<void>(`/api/profiles/${id}`, { method: "DELETE" }),

  generate: (p: GeneratePayload) => request<Job>("/api/generate", json("POST", p)),
  job: (id: string) => request<Job>(`/api/jobs/${id}`),
  currentJob: () => request<Job | null>("/api/jobs/current"),
  cancelJob: (id: string) => request<Job>(`/api/jobs/${id}/cancel`, { method: "POST" }),

  generations: () => request<Generation[]>("/api/generations"),
  audioUrl: (id: string, format: "wav" | "mp3" = "wav", download = false) =>
    `/api/generations/${id}/audio?format=${format}${download ? "&download=true" : ""}`,
};
