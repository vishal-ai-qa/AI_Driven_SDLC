"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { useStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useWebSocket } from "@/hooks/use-websocket";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, activeProjectId, updateAgentStatus } = useStore();
  const router = useRouter();

  useEffect(() => {
    if (!user) router.push("/login");
  }, [user, router]);

  // Subscribe to agent events for active project
  useWebSocket<{
    event: string; agent: string; phase: string; status: string;
    summary: string; tokens: number; timestamp: string;
  }>(
    activeProjectId ? `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/ws/project/${activeProjectId}` : null,
    (data) => {
      if (data.event === "agent_log") {
        updateAgentStatus({
          agent: data.agent,
          phase: data.phase,
          status: data.status === "completed" ? "completed" : "running",
          message: data.summary,
          tokens: data.tokens,
          timestamp: data.timestamp,
        });
      }
    }
  );

  if (!user) return null;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
