import { useEffect, useRef, useState } from "react";
import { Download, Pause, Play } from "lucide-react";
import { api } from "../lib/api";
import { formatClock, formatDateTime } from "../lib/format";
import type { Generation } from "../types";
import { cn } from "./ui";

/** Bottom player. A newly selected generation starts playing automatically (always a user action). */
export function PlayerBar({ generation }: { generation: Generation | null }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    setTime(0);
    setPlaying(false);
    setDuration(generation?.duration_s ?? 0);
    if (generation) audioRef.current?.play().catch(() => {});
  }, [generation]);

  const toggle = () => {
    const a = audioRef.current;
    if (!a) return;
    if (a.paused) a.play().catch(() => {});
    else a.pause();
  };

  const fill = duration ? (time / duration) * 100 : 0;

  return (
    <footer className="border-t border-line bg-panel/95 backdrop-blur">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:flex-nowrap">
        {generation && (
          <audio
            ref={audioRef}
            src={api.audioUrl(generation.id)}
            preload="metadata"
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onEnded={() => setPlaying(false)}
            onTimeUpdate={(e) => setTime(e.currentTarget.currentTime)}
            onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
          />
        )}
        <button
          type="button"
          onClick={toggle}
          disabled={!generation}
          aria-label={playing ? "Duraklat" : "Oynat"}
          className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-white text-zinc-950 transition hover:scale-105 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:hover:scale-100"
        >
          {playing ? <Pause className="h-4 w-4" fill="currentColor" /> : <Play className="ml-0.5 h-4 w-4" fill="currentColor" />}
        </button>

        <div className="min-w-0 basis-40 sm:w-56 sm:flex-none">
          <p className="truncate text-sm font-medium text-zinc-100">{generation ? generation.text : "Henüz ses seçilmedi"}</p>
          <p className="truncate text-xs text-zinc-500">
            {generation ? `${formatDateTime(generation.created_at)} · ${generation.profile_name ?? "Profilsiz"}` : "Seslendirme yapın veya geçmişten seçin"}
          </p>
        </div>

        <div className="order-last flex w-full min-w-0 items-center gap-3 sm:order-none sm:flex-1">
          <span className="w-10 text-right font-mono text-xs text-zinc-500 tabular-nums">{formatClock(time)}</span>
          <input
            type="range"
            className="range"
            min={0}
            max={duration || 0}
            step={0.01}
            value={time}
            disabled={!generation}
            aria-label="Oynatma konumu"
            onChange={(e) => {
              const t = Number(e.target.value);
              if (audioRef.current) audioRef.current.currentTime = t;
              setTime(t);
            }}
            style={{ ["--fill" as string]: `${fill}%` }}
          />
          <span className="w-10 font-mono text-xs text-zinc-500 tabular-nums">{formatClock(duration)}</span>
        </div>

        <div className="ml-auto flex shrink-0 gap-2 sm:ml-0">
          {(["wav", "mp3"] as const).map((fmt) => (
            <a
              key={fmt}
              href={generation ? api.audioUrl(generation.id, fmt, true) : undefined}
              aria-disabled={!generation}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-2 text-xs font-medium uppercase transition",
                generation ? "bg-raised text-zinc-200 hover:bg-zinc-800" : "pointer-events-none text-zinc-600",
              )}
            >
              <Download className="h-3.5 w-3.5" /> {fmt}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
