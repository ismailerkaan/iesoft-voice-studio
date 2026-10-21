export interface GenerationSettings {
  exaggeration: number;
  cfg_weight: number;
  temperature: number;
  repetition_penalty: number;
  seed: number;
  pause_ms: number;
}

export interface ModelStatus {
  status: "idle" | "loading" | "ready" | "error";
  device: string | null;
  error: string | null;
  name: string;
}

export interface AppStatus {
  model: ModelStatus;
  busy: boolean;
  max_text_chars: number;
  default_settings: GenerationSettings;
}

export interface ReferenceVoice {
  id: string;
  original_name: string;
  duration_s: number;
  created_at: string;
}

export interface Profile {
  id: string;
  name: string;
  reference_id: string | null;
  settings: GenerationSettings;
  updated_at: string;
}

export interface Generation {
  id: string;
  text: string;
  profile_id: string | null;
  profile_name: string | null;
  reference_id: string | null;
  settings: GenerationSettings;
  chunks: number;
  duration_s: number;
  gen_seconds: number;
  device: string;
  created_at: string;
}

export interface Job {
  id: string;
  status: "running" | "done" | "error" | "cancelled";
  stage: string;
  chunk_index: number;
  chunk_total: number;
  current_text: string;
  error: string | null;
  generation: Generation | null;
  elapsed_s: number;
}
