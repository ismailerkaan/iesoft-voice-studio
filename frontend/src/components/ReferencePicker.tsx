import { useEffect, useRef, useState } from "react";
import { Loader2, Pause, Play, Upload, X } from "lucide-react";
import { api } from "../lib/api";
import { formatDuration } from "../lib/format";
import type { ReferenceVoice } from "../types";
import { Button } from "./ui";

interface Props {
  references: ReferenceVoice[];
  value: string | null;
  onChange: (id: string | null) => void;
  onUploaded: (ref: ReferenceVoice) => void;
  onError: (message: string) => void;
  disabled?: boolean;
}

export function ReferencePicker({ references, value, onChange, onUploaded, onError, disabled }: Props) {
  const [uploadOpen, setUploadOpen] = useState(false);
  const [consent, setConsent] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => () => audioRef.current?.pause(), []);
  useEffect(() => {
    audioRef.current?.pause();
    setPreviewing(false);
  }, [value]);

  const togglePreview = () => {
    if (!value) return;
    if (previewing) {
      audioRef.current?.pause();
      setPreviewing(false);
      return;
    }
    const a = new Audio(api.referenceAudioUrl(value));
    a.onended = () => setPreviewing(false);
    a.play().then(() => setPreviewing(true)).catch(() => onError("Referans ses oynatılamadı."));
    audioRef.current = a;
  };

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    setUploading(true);
    try {
      const ref = await api.uploadReference(file);
      onUploaded(ref);
      setUploadOpen(false);
      setConsent(false);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <label htmlFor="reference" className="sr-only">
          Referans ses
        </label>
        <select
          id="reference"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value || null)}
          disabled={disabled}
          className="min-w-0 flex-1 rounded-lg border border-line bg-raised px-3 py-2 text-sm text-zinc-100 focus:ring-2 focus:ring-accent/50 focus:outline-none"
        >
          <option value="">Varsayılan ses (referanssız)</option>
          {references.map((r) => (
            <option key={r.id} value={r.id}>
              {r.original_name} · {formatDuration(r.duration_s)}
            </option>
          ))}
        </select>
        <Button
          variant="secondary"
          onClick={togglePreview}
          disabled={!value}
          aria-label={previewing ? "Önizlemeyi durdur" : "Referans sesi dinle"}
          className="px-2.5"
        >
          {previewing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>
      </div>

      {!value && (
        <p className="rounded-lg border border-accent/20 bg-accent/5 px-3 py-2 text-xs leading-relaxed text-zinc-300">
          Referans ses gerekmez: modelin yerleşik anlatıcı sesi kullanılır. Kendi sesinizi kullanmak için aşağıdan izinli bir WAV yükleyin.
        </p>
      )}

      {!uploadOpen ? (
        <Button variant="ghost" onClick={() => setUploadOpen(true)} disabled={disabled} className="w-full border border-dashed border-line">
          <Upload className="h-4 w-4" /> Referans WAV yükle
        </Button>
      ) : (
        <div className="space-y-3 rounded-xl border border-line bg-raised p-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-xs leading-relaxed text-zinc-400">
              3–60 sn, tek konuşmacılı, temiz kayıt önerilir. Yalnızca WAV.
            </p>
            <button type="button" onClick={() => setUploadOpen(false)} aria-label="Kapat" className="text-zinc-500 hover:text-zinc-200">
              <X className="h-4 w-4" />
            </button>
          </div>
          <label className="flex cursor-pointer items-start gap-2 text-sm text-zinc-200">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-0.5 h-4 w-4 accent-violet-500"
            />
            <span>Bu sesin sahibinden kullanım ve klonlama izni aldım.</span>
          </label>
          <input ref={fileRef} type="file" accept=".wav,audio/wav,audio/x-wav" className="hidden" onChange={(e) => handleFile(e.target.files?.[0])} />
          <Button variant="primary" onClick={() => fileRef.current?.click()} disabled={!consent || uploading} className="w-full">
            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            {uploading ? "Yükleniyor…" : "Dosya seç"}
          </Button>
        </div>
      )}
    </div>
  );
}
