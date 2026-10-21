import { Dices, RotateCcw } from "lucide-react";
import { formatDecimal } from "../lib/format";
import type { GenerationSettings, ReferenceVoice } from "../types";
import { ReferencePicker } from "./ReferencePicker";
import { Slider } from "./Slider";
import { Panel } from "./ui";

interface Props {
  settings: GenerationSettings;
  defaults: GenerationSettings;
  onChange: (s: GenerationSettings) => void;
  references: ReferenceVoice[];
  referenceId: string | null;
  onReferenceChange: (id: string | null) => void;
  onReferenceUploaded: (ref: ReferenceVoice) => void;
  onError: (message: string) => void;
  disabled: boolean;
  modelLabel: string;
}

export function SettingsPanel(p: Props) {
  const set = <K extends keyof GenerationSettings>(key: K, value: GenerationSettings[K]) =>
    p.onChange({ ...p.settings, [key]: value });
  const s = p.settings;

  return (
    <Panel
      title="Ses ve model ayarları"
      className="lg:h-full"
      action={
        <button
          type="button"
          onClick={() => p.onChange(p.defaults)}
          disabled={p.disabled}
          className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-100 disabled:opacity-40"
        >
          <RotateCcw className="h-3.5 w-3.5" /> Varsayılan
        </button>
      }
    >
      <div className="space-y-6 p-4">
        <div className="space-y-2">
          <p className="text-sm font-medium text-zinc-200">Model</p>
          <div className="rounded-lg border border-line bg-raised px-3 py-2 text-sm text-zinc-300">
            {p.modelLabel} <span className="text-zinc-500">· Türkçe</span>
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-zinc-200">Referans ses</p>
          <ReferencePicker
            references={p.references}
            value={p.referenceId}
            onChange={p.onReferenceChange}
            onUploaded={p.onReferenceUploaded}
            onError={p.onError}
            disabled={p.disabled}
          />
        </div>

        <hr className="border-line" />

        <Slider
          label="Duygu yoğunluğu (Exaggeration)"
          hint="0,5 nötr. Yüksek değerler daha dramatik anlatım verir ama konuşmayı hızlandırabilir."
          value={s.exaggeration} min={0.25} max={2} step={0.05}
          onChange={(v) => set("exaggeration", v)} disabled={p.disabled}
        />
        <Slider
          label="CFG Weight"
          hint="Düşük değer (≈0,3) daha yavaş ve sakin bir tempo verir. Yüksek duygu yoğunluğunda düşürmek önerilir."
          value={s.cfg_weight} min={0} max={1} step={0.05}
          onChange={(v) => set("cfg_weight", v)} disabled={p.disabled}
        />
        <Slider
          label="Temperature"
          hint="Yüksek değer daha canlı ama daha az tutarlı; düşük değer daha düz ve öngörülebilir."
          value={s.temperature} min={0.05} max={2} step={0.05}
          onChange={(v) => set("temperature", v)} disabled={p.disabled}
        />
        <Slider
          label="Repetition Penalty"
          hint="Kelime tekrarı ve takılmaları azaltır. Model varsayılanı 1,2."
          value={s.repetition_penalty} min={1} max={2} step={0.05}
          onChange={(v) => set("repetition_penalty", v)} disabled={p.disabled}
        />
        <Slider
          label="Cümle arası duraklama"
          hint="Parçalar birleştirilirken eklenen sessizlik."
          value={s.pause_ms} min={0} max={2000} step={50}
          format={(v) => `${formatDecimal(v / 1000, 2)} sn`}
          onChange={(v) => set("pause_ms", v)} disabled={p.disabled}
        />

        <div className="space-y-2">
          <label htmlFor="seed" className="text-sm font-medium text-zinc-200">
            Seed
          </label>
          <div className="flex gap-2">
            <input
              id="seed"
              type="number"
              min={0}
              max={2147483647}
              value={s.seed}
              disabled={p.disabled}
              onChange={(e) => set("seed", Math.max(0, Math.min(2147483647, Math.floor(Number(e.target.value) || 0))))}
              className="min-w-0 flex-1 rounded-lg border border-line bg-raised px-3 py-2 font-mono text-sm text-zinc-100 focus:ring-2 focus:ring-accent/50 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => set("seed", Math.floor(Math.random() * 2147483647))}
              disabled={p.disabled}
              aria-label="Rastgele seed"
              className="rounded-lg border border-line bg-raised px-2.5 text-zinc-300 hover:bg-zinc-800 disabled:opacity-40"
            >
              <Dices className="h-4 w-4" />
            </button>
          </div>
          <p className="text-xs text-zinc-500">
            Aynı metin, ayar ve seed aynı cihazda aynı sesi üretir.
          </p>
        </div>
      </div>
    </Panel>
  );
}
