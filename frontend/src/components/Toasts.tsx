import { AlertCircle, CheckCircle2, X } from "lucide-react";
import { cn } from "./ui";

export interface Toast {
  id: number;
  kind: "error" | "success";
  message: string;
}

export function Toasts({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div className="pointer-events-none fixed top-4 right-4 z-50 flex w-[min(420px,calc(100vw-2rem))] flex-col gap-2" aria-live="assertive">
      {toasts.map((t) => (
        <div
          key={t.id}
          role={t.kind === "error" ? "alert" : "status"}
          className={cn(
            "pointer-events-auto flex items-start gap-3 rounded-xl border p-3 text-sm shadow-2xl backdrop-blur",
            t.kind === "error" ? "border-red-500/30 bg-red-950/80 text-red-100" : "border-emerald-500/30 bg-emerald-950/80 text-emerald-100",
          )}
        >
          {t.kind === "error" ? <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> : <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />}
          <p className="flex-1 leading-5 break-words">{t.message}</p>
          <button type="button" onClick={() => onDismiss(t.id)} aria-label="Kapat" className="opacity-60 hover:opacity-100">
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
