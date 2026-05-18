"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, FileText, BookOpen, FlaskConical,
  Play, Bug, Code2, GitBranch, BarChart3, Settings,
  ChevronLeft, Zap,
} from "lucide-react";
import { useStore } from "@/lib/store";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/requirements", label: "Requirements", icon: FileText },
  { href: "/dashboard/stories", label: "User Stories", icon: BookOpen },
  { href: "/dashboard/test-cases", label: "Test Cases", icon: FlaskConical },
  { href: "/dashboard/execution", label: "Execution", icon: Play },
  { href: "/dashboard/bugs", label: "Bugs", icon: Bug },
  { href: "/dashboard/automation", label: "Automation", icon: Code2 },
  { href: "/dashboard/traceability", label: "Traceability", icon: GitBranch },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useStore();

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-card border-r border-border transition-all duration-300",
        sidebarOpen ? "w-60" : "w-16"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 p-4 border-b border-border">
        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
          <Zap className="w-4 h-4 text-primary" />
        </div>
        {sidebarOpen && (
          <div className="overflow-hidden">
            <p className="font-bold text-sm truncate">QAgent</p>
            <p className="text-xs text-muted-foreground truncate">AI SDLC Platform</p>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className={cn("ml-auto p-1 rounded hover:bg-secondary transition-colors flex-shrink-0", !sidebarOpen && "mx-auto")}
        >
          <ChevronLeft className={cn("w-4 h-4 transition-transform", !sidebarOpen && "rotate-180")} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2">
        <ul className="space-y-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    active
                      ? "bg-primary/20 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary",
                    !sidebarOpen && "justify-center px-2"
                  )}
                  title={!sidebarOpen ? label : undefined}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  {sidebarOpen && <span className="truncate">{label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Settings */}
      <div className="p-2 border-t border-border">
        <Link
          href="/dashboard/settings"
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors",
            !sidebarOpen && "justify-center px-2"
          )}
        >
          <Settings className="w-4 h-4 flex-shrink-0" />
          {sidebarOpen && <span>Settings</span>}
        </Link>
      </div>
    </aside>
  );
}
