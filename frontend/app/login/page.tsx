"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { useStore } from "@/lib/store";
import { toast } from "sonner";
import { Zap } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useStore();
  const [form, setForm] = useState({ email: "", password: "" });

  const mutation = useMutation({
    mutationFn: () => authApi.login(form.email, form.password),
    onSuccess: (data) => {
      setAuth(data.user, data.access_token);
      toast.success("Welcome back!");
      router.push("/dashboard");
    },
    onError: () => toast.error("Invalid credentials"),
  });

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo */}
        <div className="text-center">
          <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center mx-auto mb-4">
            <Zap className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">QAgent</h1>
          <p className="text-muted-foreground text-sm mt-1">AI-Native SDLC Platform</p>
        </div>

        {/* Form */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <div>
            <label className="block text-xs text-muted-foreground mb-1.5">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="you@company.com"
              className="w-full bg-secondary border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1.5">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              onKeyDown={(e) => e.key === "Enter" && mutation.mutate()}
              className="w-full bg-secondary border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button
            onClick={() => mutation.mutate()}
            disabled={!form.email || !form.password || mutation.isPending}
            className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {mutation.isPending ? "Signing in..." : "Sign In"}
          </button>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          Don&apos;t have an account?{" "}
          <a href="/register" className="text-primary hover:underline">Register</a>
        </p>
      </div>
    </div>
  );
}
