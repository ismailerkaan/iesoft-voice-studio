import { useEffect, useState } from "react";
import { ChevronDown, Loader2, Sparkles, Square } from "lucide-react";
import { api } from "../lib/api";
import { formatDuration, formatInt } from "../lib/format";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import type { Job } from "../types";
import { Button, cn } from "./ui";

interface Props {
  text: string;
  onChange: (text: string) => void;
  maxChars: number;
  job: Job | null;
  running: boolean;
  canGenerate: boolean;
  disabledReason: string | null;
  onGenerate: () => void;
  onCancel: () => void;
}

export function TextEditor({ text, onChange, maxChars, job, running, canGenerate, disabledReason, onGenerate, onCancel }: Props) {
  const [chunks, setChunks] = useState<string[]>([]);
  const [showChunks, setShowChunks] = useState(false);
  const debounced = useDebouncedValue(text, 400);
  const over = text.length > maxChars;

  useEffect(() => {
    if (!debounced.trim() || debounced.length > maxChars) {
      setChunks([]);
      return;
    }
    let active = true;
    api.split(debounced).then((r) => active && setChunks(r.chunks)).catch(() => active && setChunks([]));
    return () => {
      active = false;
    };
  }, [debounced, maxChars]);

  return (
    <section className="flex min-h-[420px] flex-1 flex-col rounded-2xl border border-line bg-panel lg:min-h-0">
      <div className="relative min-h-0 flex-1">
        <label htmlFor="script" className="sr-only">
          Seslendirilecek metin
        </label>
        <textarea
          id="script"
          value={text}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && canGenerate) onGenerate();
          }}
          placeholder="Seslendirmek istediğiniz Türkçe metni buraya yazın veya yapıştırın…"
          spellCheck
          lang="tr"
          className="scroll-thin h-full min-h-[320px] w-full resize-none bg-transparent px-6 py-5 text-[17px] leading-8 text-zinc-100 placeholder:text-zinc-600 focus:outline-none"
        />
      </div>

      {showChunks && chunks.length > 0 && (
        <ol className="scroll-thin max-h-48 space-y-1.5 overflow-y-auto border-t border-line px-6 py-3 text-sm">
          {chunks.map((c, i) => (
            <li key={i} className="flex gap-3 text-zinc-400">
              <span className="w-6 shrink-0 text-right font-mono text-xs leading-5 text-zinc-600">{i + 1}</span>
              <span className="leading-5">{c}</span>
            </li>
          ))}
        </ol>
      )}

      {job && (running || job.status === "cancelled") && <Progress job={job} onCancel={onCancel} running={running} />}

      <footer className="flex flex-wrap items-center gap-3 border-t border-line px-4 py-3">
        <span className={cn("font-mono text-xs tabular-nums", over ? "text-red-400" : "text-zinc-500")}>
          {formatInt(text.length)} / {formatInt(maxChars)}
        </span>
        <button
          type="button"
          onClick={() => setShowChunks((s) => !s)}
          disabled={chunks.length === 0}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-zinc-400 hover:bg-white/5 disabled:opacity-40"
          aria-expanded={showChunks}
        >
          {chunks.length} parça
          <ChevronDown className={cn("h-3.5 w-3.5 transition", showChunks && "rotate-180")} />
        </button>
        <div className="ml-auto flex items-center gap-3">
          {disabledReason && !running && <span className="text-xs text-zinc-500">{disabledReason}</span>}
          <Button variant="primary" onClick={onGenerate} disabled={!canGenerate} className="px-5" title="⌘ + Enter">
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {running ? "Üretiliyor" : "Seslendir"}
          </Button>
        </div>
      </footer>
    </section>
  );
}

function Progress({ job, running, onCancel }: { job: Job; running: boolean; onCancel: () => void }) {
  // Only completed chunks are shown as progress; inside a chunk the model gives no measurable progress.
  const done = Math.max(0, job.chunk_index - 1);
  const pct = job.chunk_total ? (done / job.chunk_total) * 100 : 0;
  return (
    <div className="border-t border-line bg-raised/60 px-6 py-4" role="status" aria-live="polite">
      <div className="mb-2 flex items-center justify-between gap-3 text-sm">
        <span className="font-medium text-zinc-200">
          {job.stage}
          {job.chunk_total > 0 && running && (
            <span className="ml-2 font-normal whitespace-nowrap text-zinc-400">
              Parça {job.chunk_index || 1} / {job.chunk_total}
            </span>
          )}
        </span>
        <span className="flex items-center gap-3 font-mono text-xs text-zinc-500 tabular-nums">
          {formatDuration(job.elapsed_s)}
          {running && (
            <Button variant="ghost" onClick={onCancel} className="px-2 py-1 text-xs">
              <Square className="h-3 w-3" /> İptal
            </Button>
          )}
        </span>
      </div>
      <div className="relative h-1.5 overflow-hidden rounded-full bg-zinc-800">
        <div className="absolute inset-y-0 left-0 bg-accent transition-all duration-500" style={{ width: `${pct}%` }} />
        {running && (
          <div
            className="animate-indeterminate absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-white/25 to-transparent"
            aria-hidden
          />
        )}
      </div>
      {job.current_text && <p className="mt-2 line-clamp-2 text-xs text-zinc-500 italic">“{job.current_text}”</p>}
    </div>
  );
}
