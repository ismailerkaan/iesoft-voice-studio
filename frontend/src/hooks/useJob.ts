import { useCallback, useEffect, useRef, useState } from "react";
import { api, type GeneratePayload } from "../lib/api";
import type { Generation, Job } from "../types";

const POLL_MS = 1000;

/** Starts a generation and polls its real progress (chunk n / total) until it ends. */
export function useJob(onDone: (generation: Generation) => void, onError: (message: string) => void) {
  const [job, setJob] = useState<Job | null>(null);
  const handlers = useRef({ onDone, onError });
  handlers.current = { onDone, onError };

  const running = job?.status === "running";
  const jobId = job?.id;

  useEffect(() => {
    api.currentJob().then((j) => j?.status === "running" && setJob(j)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!running || !jobId) return;
    let stopped = false;
    const timer = setInterval(async () => {
      try {
        const next = await api.job(jobId);
        if (stopped) return;
        setJob(next);
        if (next.status === "done" && next.generation) handlers.current.onDone(next.generation);
        if (next.status === "error") handlers.current.onError(next.error ?? "Bilinmeyen hata.");
      } catch (e) {
        if (!stopped) handlers.current.onError((e as Error).message);
      }
    }, POLL_MS);
    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [running, jobId]);

  const start = useCallback(async (payload: GeneratePayload) => {
    try {
      setJob(await api.generate(payload));
    } catch (e) {
      handlers.current.onError((e as Error).message);
    }
  }, []);

  const cancel = useCallback(async () => {
    if (!jobId) return;
    try {
      setJob(await api.cancelJob(jobId));
    } catch (e) {
      handlers.current.onError((e as Error).message);
    }
  }, [jobId]);

  return { job, running, start, cancel };
}
