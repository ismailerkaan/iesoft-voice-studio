import { useState, type FormEvent } from "react";
import { Check, Plus, Save, Trash2, UserRound } from "lucide-react";
import type { Profile } from "../types";
import { Button, EmptyState, Panel, cn } from "./ui";

interface Props {
  profiles: Profile[];
  activeId: string | null;
  onSelect: (p: Profile) => void;
  onCreate: (name: string) => Promise<boolean>;
  onUpdate: (p: Profile) => void;
  onDelete: (p: Profile) => void;
  disabled: boolean;
}

export function ProfilesPanel({ profiles, activeId, onSelect, onCreate, onUpdate, onDelete, disabled }: Props) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const active = profiles.find((p) => p.id === activeId);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    if (await onCreate(name.trim())) {
      setName("");
      setAdding(false);
    }
  };

  return (
    <Panel
      title="Ses profilleri"
      className="lg:max-h-[45%]"
      action={
        <button
          type="button"
          onClick={() => setAdding((a) => !a)}
          disabled={disabled}
          aria-label="Yeni profil"
          className="rounded-md p-1 text-zinc-400 hover:bg-white/5 hover:text-zinc-100 disabled:opacity-40"
        >
          <Plus className="h-4 w-4" />
        </button>
      }
    >
      {adding && (
        <form onSubmit={submit} className="space-y-2 border-b border-line p-3">
          <input
            autoFocus
            value={name}
            maxLength={60}
            onChange={(e) => setName(e.target.value)}
            placeholder="Profil adı (ör. Hikâye Anlatıcısı)"
            className="w-full rounded-lg border border-line bg-raised px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:ring-2 focus:ring-accent/50 focus:outline-none"
          />
          <p className="text-xs text-zinc-500">Mevcut referans ses ve ayarlar kaydedilir.</p>
          <Button type="submit" variant="primary" className="w-full" disabled={!name.trim()}>
            <Save className="h-4 w-4" /> Kaydet
          </Button>
        </form>
      )}

      {profiles.length === 0 && !adding ? (
        <EmptyState>Henüz profil yok. Ayarlarınızı bir isimle kaydedin.</EmptyState>
      ) : (
        <ul className="p-2">
          {profiles.map((p) => (
            <li key={p.id} className="group relative">
              <button
                type="button"
                onClick={() => onSelect(p)}
                disabled={disabled}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left text-sm transition disabled:cursor-not-allowed",
                  p.id === activeId ? "bg-accent/10 text-zinc-50" : "text-zinc-300 hover:bg-white/5",
                )}
              >
                <span
                  className={cn(
                    "grid h-8 w-8 shrink-0 place-items-center rounded-full",
                    p.id === activeId ? "bg-accent text-zinc-950" : "bg-zinc-800 text-zinc-400",
                  )}
                >
                  {p.id === activeId ? <Check className="h-4 w-4" /> : <UserRound className="h-4 w-4" />}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">{p.name}</span>
                  <span className="block truncate text-xs text-zinc-500">
                    {p.reference_id ? "Klon ses" : "Varsayılan ses"}
                  </span>
                </span>
              </button>
              <button
                type="button"
                onClick={() => window.confirm(`“${p.name}” profili silinsin mi?`) && onDelete(p)}
                disabled={disabled}
                aria-label={`${p.name} profilini sil`}
                className="absolute top-1/2 right-2 -translate-y-1/2 rounded-md p-1.5 text-zinc-500 opacity-0 group-hover:opacity-100 hover:bg-red-500/10 hover:text-red-300 focus:opacity-100"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {active && (
        <div className="border-t border-line p-3">
          <Button variant="ghost" className="w-full text-xs" onClick={() => onUpdate(active)} disabled={disabled}>
            <Save className="h-3.5 w-3.5" /> “{active.name}” profilini güncelle
          </Button>
        </div>
      )}
    </Panel>
  );
}
