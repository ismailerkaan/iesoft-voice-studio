const TZ = "Europe/Istanbul";

const dateTime = new Intl.DateTimeFormat("tr-TR", {
  timeZone: TZ,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const integer = new Intl.NumberFormat("tr-TR");

export const formatDateTime = (iso: string) => dateTime.format(new Date(iso));

export const formatInt = (n: number) => integer.format(n);

export const formatDecimal = (n: number, digits = 2) =>
  new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 0, maximumFractionDigits: digits }).format(n);

/** 75.4 -> "1:15" */
export function formatClock(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const s = Math.floor(seconds);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** 12.3 -> "12,3 sn", 95 -> "1 dk 35 sn" */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${formatDecimal(seconds, 1)} sn`;
  const m = Math.floor(seconds / 60);
  return `${m} dk ${Math.round(seconds - m * 60)} sn`;
}
