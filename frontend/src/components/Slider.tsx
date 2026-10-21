import { useId } from "react";
import { formatDecimal } from "../lib/format";

interface Props {
  label: string;
  hint: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  disabled?: boolean;
  format?: (v: number) => string;
}

export function Slider({ label, hint, value, min, max, step, onChange, disabled, format = (v) => formatDecimal(v) }: Props) {
  const id = useId();
  const fill = ((value - min) / (max - min)) * 100;
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <label htmlFor={id} className="text-sm font-medium text-zinc-200">
          {label}
        </label>
        <span className="font-mono text-xs text-zinc-400 tabular-nums">{format(value)}</span>
      </div>
      <input
        id={id}
        type="range"
        className="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ ["--fill" as string]: `${fill}%` }}
        aria-describedby={`${id}-hint`}
      />
      <p id={`${id}-hint`} className="text-xs leading-relaxed text-zinc-500">
        {hint}
      </p>
    </div>
  );
}
