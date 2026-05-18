import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

export const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-900/40 text-red-400 border-red-800",
  high: "bg-orange-900/40 text-orange-400 border-orange-800",
  medium: "bg-yellow-900/40 text-yellow-400 border-yellow-800",
  low: "bg-green-900/40 text-green-400 border-green-800",
  info: "bg-blue-900/40 text-blue-400 border-blue-800",
};

export const STATUS_COLORS: Record<string, string> = {
  passed: "bg-green-900/40 text-green-400 border-green-800",
  failed: "bg-red-900/40 text-red-400 border-red-800",
  blocked: "bg-yellow-900/40 text-yellow-400 border-yellow-800",
  pending: "bg-slate-800 text-slate-400 border-slate-700",
  running: "bg-blue-900/40 text-blue-400 border-blue-800",
  approved: "bg-green-900/40 text-green-400 border-green-800",
  draft: "bg-slate-800 text-slate-400 border-slate-700",
  open: "bg-red-900/40 text-red-400 border-red-800",
  fixed: "bg-green-900/40 text-green-400 border-green-800",
  in_progress: "bg-blue-900/40 text-blue-400 border-blue-800",
};
