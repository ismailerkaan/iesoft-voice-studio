import type { ButtonHTMLAttributes, ReactNode } from "react";

export function cn(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export function Panel({
  title,
  action,
  children,
  className,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("flex flex-col rounded-2xl border border-line bg-panel lg:min-h-0", className)}>
      <header className="flex items-center justify-between gap-2 border-b border-line px-4 py-3">
        <h2 className="text-xs font-semibold tracking-wider text-zinc-400 uppercase">{title}</h2>
        {action}
      </header>
      <div className="scroll-thin min-h-0 flex-1 overflow-y-auto">{children}</div>
    </section>
  );
}

type Variant = "primary" | "secondary" | "ghost" | "danger";

const variants: Record<Variant, string> = {
  primary: "bg-white text-zinc-950 hover:bg-zinc-200 disabled:bg-zinc-700 disabled:text-zinc-400",
  secondary: "border border-line bg-raised text-zinc-200 hover:bg-zinc-800 disabled:text-zinc-500",
  ghost: "text-zinc-400 hover:bg-white/5 hover:text-zinc-100 disabled:text-zinc-600",
  danger: "border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20",
};

export function Button({
  variant = "secondary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition",
        "focus-visible:ring-2 focus-visible:ring-accent/60 focus-visible:outline-none disabled:cursor-not-allowed",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="px-4 py-6 text-center text-sm text-zinc-500">{children}</p>;
}
