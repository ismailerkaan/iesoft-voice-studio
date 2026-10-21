import { useCallback, useEffect, useState } from "react";
import { AudioWaveform, Cpu, Loader2 } from "lucide-react";
import { api } from "./lib/api";
import { useJob } from "./hooks/useJob";
import type { AppStatus, Generation, GenerationSettings, Profile, ReferenceVoice } from "./types";
import { TextEditor } from "./components/TextEditor";
import { SettingsPanel } from "./components/SettingsPanel";
import { ProfilesPanel } from "./components/ProfilesPanel";
import { HistoryPanel } from "./components/HistoryPanel";
import { PlayerBar } from "./components/PlayerBar";
import { Toasts, type Toast } from "./components/Toasts";
import { cn } from "./components/ui";

const FALLBACK_SETTINGS: GenerationSettings = {
  exaggeration: 0.5, cfg_weight: 0.5, temperature: 0.8, repetition_penalty: 1.2, seed: 42, pause_ms: 400,
};

let toastSeq = 0;

export default function App() {
  const [status, setStatus] = useState<AppStatus | null>(null);
  const [text, setText] = useState("");
  const [settings, setSettings] = useState<GenerationSettings>(FALLBACK_SETTINGS);
  const [referenceId, setReferenceId] = useState<string | null>(null);
  const [activeProfileId, setActiveProfileId] = useState<string | null>(null);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [references, setReferences] = useState<ReferenceVoice[]>([]);
  const [history, setHistory] = useState<Generation[]>([]);
  const [current, setCurrent] = useState<Generation | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const notify = useCallback((kind: Toast["kind"], message: string) => {
    const id = ++toastSeq;
    setToasts((t) => [...t.slice(-3), { id, kind, message }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), kind === "error" ? 9000 : 4000);
  }, []);
  const showError = useCallback((m: string) => notify("error", m), [notify]);

  const { job, running, start, cancel } = useJob(
    (gen) => {
      setHistory((h) => [gen, ...h.filter((x) => x.id !== gen.id)]);
      setCurrent(gen);
      notify("success", "Seslendirme hazır.");
    },
    showError,
  );

  // Initial data + model status polling until the model is ready or failed.
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const s = await api.status();
        setStatus(s);
        if (s.model.status === "loading" || s.model.status === "idle") timer = setTimeout(poll, 2000);
      } catch (e) {
        showError((e as Error).message);
        timer = setTimeout(poll, 4000);
      }
    };
    poll();
    Promise.all([api.profiles(), api.references(), api.generations()])
      .then(([p, r, g]) => {
        setProfiles(p);
        setReferences(r);
        setHistory(g);
      })
      .catch((e) => showError((e as Error).message));
    return () => clearTimeout(timer);
  }, [showError]);

  useEffect(() => {
    if (status) setSettings((s) => (s === FALLBACK_SETTINGS ? status.default_settings : s));
  }, [status]);

  const model = status?.model;
  const maxChars = status?.max_text_chars ?? 5000;
  const disabledReason = !model
    ? "Sunucuya bağlanılıyor…"
    : model.status === "error"
      ? "Model yüklenemedi"
      : model.status !== "ready"
        ? "Model yükleniyor…"
        : !text.trim()
          ? "Metin girin"
          : text.length > maxChars
            ? "Metin çok uzun"
            : null;

  const generate = () => {
    if (disabledReason || running) return;
    start({ text, reference_id: referenceId, profile_id: activeProfileId, settings });
  };

  const applyProfile = (p: Profile) => {
    setActiveProfileId(p.id);
    setSettings(p.settings);
    setReferenceId(p.reference_id);
  };

  const profilePayload = (name: string) => ({ name, reference_id: referenceId, settings });

  const createProfile = async (name: string) => {
    try {
      const p = await api.createProfile(profilePayload(name));
      setProfiles((list) => [...list, p].sort((a, b) => a.name.localeCompare(b.name, "tr")));
      setActiveProfileId(p.id);
      notify("success", `“${p.name}” profili kaydedildi.`);
      return true;
    } catch (e) {
      showError((e as Error).message);
      return false;
    }
  };

  const updateProfile = async (p: Profile) => {
    try {
      const updated = await api.updateProfile(p.id, profilePayload(p.name));
      setProfiles((list) => list.map((x) => (x.id === p.id ? updated : x)));
      notify("success", `“${p.name}” profili güncellendi.`);
    } catch (e) {
      showError((e as Error).message);
    }
  };

  const deleteProfile = async (p: Profile) => {
    try {
      await api.deleteProfile(p.id);
      setProfiles((list) => list.filter((x) => x.id !== p.id));
      if (activeProfileId === p.id) setActiveProfileId(null);
    } catch (e) {
      showError((e as Error).message);
    }
  };

  const restore = (g: Generation) => {
    setText(g.text);
    setSettings(g.settings);
    setReferenceId(g.reference_id && references.some((r) => r.id === g.reference_id) ? g.reference_id : null);
    setActiveProfileId(g.profile_id && profiles.some((p) => p.id === g.profile_id) ? g.profile_id : null);
    notify("success", "Metin ve ayarlar yüklendi. Aynı seed ile tekrar üretebilirsiniz.");
  };

  // Manual changes detach the settings from the selected profile.
  const changeSettings = (s: GenerationSettings) => {
    setSettings(s);
    setActiveProfileId(null);
  };
  const changeReference = (id: string | null) => {
    setReferenceId(id);
    setActiveProfileId(null);
  };

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-line px-4 py-3 sm:px-6">
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-violet-400 to-fuchsia-500 text-white shadow-lg shadow-violet-500/20">
          <AudioWaveform className="h-4 w-4" />
        </div>
        <h1 className="text-[15px] font-semibold tracking-tight text-zinc-50">
          IESOFT <span className="font-normal text-zinc-400">Voice Studio</span>
        </h1>
        <ModelPill model={model} />
      </header>

      <main className="mx-auto grid w-full max-w-[1600px] min-h-0 flex-1 grid-cols-1 content-start gap-4 overflow-y-auto p-4 lg:grid-cols-[280px_minmax(0,1fr)_340px] lg:content-stretch lg:overflow-hidden">
        <aside className="order-3 flex flex-col gap-4 lg:order-1 lg:min-h-0">
          <ProfilesPanel
            profiles={profiles}
            activeId={activeProfileId}
            onSelect={applyProfile}
            onCreate={createProfile}
            onUpdate={updateProfile}
            onDelete={deleteProfile}
            disabled={running}
          />
          <HistoryPanel items={history} playingId={current?.id ?? null} onPlay={setCurrent} onRestore={restore} disabled={running} />
        </aside>

        <div className="order-1 flex flex-col lg:order-2 lg:min-h-0">
          <TextEditor
            text={text}
            onChange={setText}
            maxChars={maxChars}
            job={job}
            running={running}
            canGenerate={!disabledReason && !running}
            disabledReason={disabledReason}
            onGenerate={generate}
            onCancel={cancel}
          />
        </div>

        <div className="order-2 lg:order-3 lg:min-h-0">
          <SettingsPanel
            settings={settings}
            defaults={status?.default_settings ?? FALLBACK_SETTINGS}
            onChange={changeSettings}
            references={references}
            referenceId={referenceId}
            onReferenceChange={changeReference}
            onReferenceUploaded={(r) => {
              setReferences((list) => [r, ...list]);
              changeReference(r.id);
              notify("success", "Referans ses yüklendi ve seçildi.");
            }}
            onError={showError}
            disabled={running}
            modelLabel={model?.name ?? "Chatterbox Multilingual V3"}
          />
        </div>
      </main>

      <PlayerBar generation={current} />
      <Toasts toasts={toasts} onDismiss={(id) => setToasts((t) => t.filter((x) => x.id !== id))} />
    </div>
  );
}

function ModelPill({ model }: { model: AppStatus["model"] | undefined }) {
  const state = model?.status ?? "idle";
  const label =
    state === "ready" ? `Hazır · ${model?.device?.toUpperCase()}` : state === "error" ? "Model hatası" : "Model yükleniyor";
  return (
    <span
      title={model?.error ?? undefined}
      className={cn(
        "ml-auto inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs",
        state === "ready" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
        state === "error" && "border-red-500/30 bg-red-500/10 text-red-300",
        (state === "loading" || state === "idle") && "border-amber-500/30 bg-amber-500/10 text-amber-200",
      )}
    >
      {state === "ready" ? <Cpu className="h-3 w-3" /> : state === "error" ? null : <Loader2 className="h-3 w-3 animate-spin" />}
      {label}
    </span>
  );
}
