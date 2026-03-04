"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { useAuth } from "@/contexts/AuthContext";

type Props = { open: boolean; onOpenChange: (open: boolean) => void };

export function SignUpDialog({ open, onOpenChange }: Props) {
  const { register, error, clearError } = useAuth();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [name, setName] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setSubmitting(true);
    try {
      await register(email, password, name || undefined);
      onOpenChange(false);
      setEmail("");
      setPassword("");
      setName("");
    } catch {
      // error set in context
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  const modal = (
    <div className="auth-modal-overlay fixed inset-0 z-[9999] flex items-center justify-center bg-black/60" style={{ position: "fixed", zIndex: 9999 }} role="dialog" aria-modal="true" aria-labelledby="signup-title">
      <div className="w-full max-w-md rounded-2xl border border-[rgba(255,255,255,0.12)] bg-[#111118] px-6 py-6 shadow-[0_0_40px_rgba(0,0,0,0.8)]">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 id="signup-title" className="text-lg font-semibold text-[#f5f5f7]">Create account</h2>
            <p className="mt-1 text-sm text-[#a5a5aa]">
              Create your Elysium Health account.
            </p>
          </div>
          <button
            type="button"
            onClick={() => { clearError(); onOpenChange(false); }}
            className="inline-flex size-8 items-center justify-center rounded-full border border-white/10 text-[#f5f5f7]/80 hover:bg-white/10"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="grid gap-4">
          {error && (
            <p className="rounded-md border border-[#ff3b30]/40 bg-[#2b1413] px-3 py-2 text-sm text-[#ffb3aa]" role="alert">
              {error}
            </p>
          )}

          <div className="grid gap-2">
            <Label htmlFor="signup-email">Email</Label>
            <Input
              id="signup-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="bg-[#0a0a0b] border-[rgba(255,255,255,0.16)]"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="signup-name">Name (optional)</Label>
            <Input
              id="signup-name"
              type="text"
              placeholder="Your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              className="bg-[#0a0a0b] border-[rgba(255,255,255,0.16)]"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="signup-password">Password</Label>
            <Input
              id="signup-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              className="bg-[#0a0a0b] border-[rgba(255,255,255,0.16)]"
            />
          </div>

          <div className="mt-4 flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => { clearError(); onOpenChange(false); }}
              className="border-[rgba(255,255,255,0.25)]"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Creating account…" : "Create account"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
