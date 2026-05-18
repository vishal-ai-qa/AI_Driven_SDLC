import Link from "next/link";
import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  sub?: string;
  accent?: "red" | "green" | "yellow";
  href?: string;
}

export function StatCard({ label, value, icon, sub, accent, href }: Props) {
  const content = (
    <div className={cn(
      "rounded-xl border bg-card p-5 hover:border-primary/50 transition-colors",
      accent === "red" ? "border-red-800/60" : "border-border"
    )}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-muted-foreground text-xs font-medium uppercase tracking-wide">{label}</span>
        <div className={cn("p-1.5 rounded-lg", accent === "red" ? "bg-red-900/30 text-red-400" : "bg-primary/10 text-primary")}>
          {icon}
        </div>
      </div>
      <p className={cn("text-3xl font-bold", accent === "red" ? "text-red-400" : "")}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}
