import { cn, STATUS_COLORS, SEVERITY_COLORS } from "@/lib/utils";

interface Props {
  status: string;
  size?: "sm" | "md";
}

export function StatusBadge({ status, size = "md" }: Props) {
  const color = STATUS_COLORS[status] || SEVERITY_COLORS[status] || "bg-slate-800 text-slate-400 border-slate-700";
  return (
    <span
      className={cn(
        "inline-flex items-center border rounded-full font-medium capitalize",
        color,
        size === "sm" ? "px-1.5 py-0 text-[10px]" : "px-2 py-0.5 text-xs"
      )}
    >
      {status.replace("_", " ")}
    </span>
  );
}
