/**
 * Zustand global store — auth, project context, agent status.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: string;
}

interface AgentStatus {
  agent: string;
  phase: string;
  status: "idle" | "running" | "completed" | "error";
  message?: string;
  tokens?: number;
  timestamp?: string;
}

interface Store {
  // Auth
  user: User | null;
  accessToken: string | null;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;

  // Active project
  activeProjectId: string | null;
  setActiveProject: (id: string) => void;

  // Agent status (real-time)
  agentStatuses: AgentStatus[];
  updateAgentStatus: (status: AgentStatus) => void;
  clearAgentStatuses: () => void;

  // UI state
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useStore = create<Store>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      setAuth: (user, accessToken) => {
        localStorage.setItem("access_token", accessToken);
        set({ user, accessToken });
      },
      clearAuth: () => {
        localStorage.removeItem("access_token");
        set({ user: null, accessToken: null });
      },

      activeProjectId: null,
      setActiveProject: (id) => set({ activeProjectId: id }),

      agentStatuses: [],
      updateAgentStatus: (status) =>
        set((state) => ({
          agentStatuses: [
            ...state.agentStatuses.filter((s) => s.agent !== status.agent),
            status,
          ].slice(-20),
        })),
      clearAgentStatuses: () => set({ agentStatuses: [] }),

      sidebarOpen: true,
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
    }),
    {
      name: "qagent-store",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        activeProjectId: state.activeProjectId,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);
