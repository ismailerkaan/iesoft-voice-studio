import { AudioLines, RotateCw } from "lucide-react";
import { formatClock, formatDateTime } from "../lib/format";
import type { Generation } from "../types";
import { EmptyState, Panel, cn } from "./ui";

interface Props {
  items: Generation[];
  playingId: string | null;
  onPlay: (g: Generation) => void;
  onRestore: (g: Generation) => void;
  disabled: boolean;
}

export function HistoryPanel({ items, playingId, onPlay, onRestore, disabled }: Props) {
  return (
    <Panel title="Geçmiş" className="flex-1">
      {items.length === 0 ? (
        <EmptyState>Ürettiğiniz seslendirmeler burada listelenir.</EmptyState>
      ) : (
        <ul className="space-y-1 p-2">
          {items.map((g) => (
            <li
              key={g.id}
              className={cn(
                "rounded-lg border border-transparent p-2 transition",
                g.id === playingId ? "border-accent/30 bg-accent/5" : "hover:bg-white/5",
              )}
            >
              <button type="button" onClick={() => onPlay(g)} className="block w-full text-left">
                <p className="line-clamp-2 text-sm leading-5 text-zinc-200">{g.text}</p>
                <p className="mt-1 flex items-center gap-1.5 text-xs text-zinc-500">
                  <AudioLines className="h-3 w-3" />
                  {formatClock(g.duration_s)}
                  <span aria-hidden>·</span>
                  {formatDateTime(g.created_at)}
                  {g.profile_name && (
                    <>
                      <span aria-hidden>·</span>
                      <span className="truncate">{g.profile_name}</span>
                    </>
                  )}
                </p>
              </button>
              <button
                type="button"
                onClick={() => onRestore(g)}
                disabled={disabled}
                className="mt-1.5 inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs text-zinc-400 hover:bg-white/5 hover:text-zinc-100 disabled:opacity-40"
              >
                <RotateCw className="h-3 w-3" /> Metni ve ayarları yükle
              </button>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
