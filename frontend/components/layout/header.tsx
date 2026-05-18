"use client";

import { useStore } from "@/lib/store";
import { Bell, LogOut, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { AgentStatusBar } from "@/components/agent-status-bar";
import { ProjectSelector } from "@/components/project-selector";

export function Header({ title }: { title?: string }) {
  const { user, clearAuth } = useStore();
  const { theme, setTheme } = useTheme();

  return (
    <header className="h-14 border-b border-border flex items-center px-6 gap-4 bg-background/80 backdrop-blur sticky top-0 z-10">
      {/* Project selector — primary navigation anchor */}
      <ProjectSelector />

      {title && <h1 className="text-sm font-semibold flex-shrink-0 text-muted-foreground">{title}</h1>}

      {/* Agent streaming status */}
      <div className="flex-1">
        <AgentStatusBar />
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="p-2 rounded-lg hover:bg-secondary transition-colors"
        >
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
        <button className="p-2 rounded-lg hover:bg-secondary transition-colors relative">
          <Bell className="w-4 h-4" />
        </button>
        <div className="flex items-center gap-2 ml-2 pl-2 border-l border-border">
          <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
            {user?.full_name?.[0] || "U"}
          </div>
          <span className="text-sm text-muted-foreground hidden sm:inline">{user?.email}</span>
          <button
            onClick={clearAuth}
            className="p-1.5 rounded hover:bg-secondary transition-colors text-muted-foreground"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
}
