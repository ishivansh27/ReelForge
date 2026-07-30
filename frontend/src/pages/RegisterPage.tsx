import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Lock, User as UserIcon, AlertCircle } from "lucide-react";
import { Logo } from "@/components/nav/Logo";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/context/AuthContext";
import { isAxiosError } from "axios";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(email, password, fullName);
      navigate("/import", { replace: true });
    } catch (err) {
      const detail = isAxiosError(err) ? err.response?.data?.detail : null;
      setError(detail || "Could not create your account.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-[400px]">
        <div className="mb-8 flex justify-center">
          <Logo />
        </div>
        <div className="rounded-2xl border border-border bg-surface p-8">
          <h1 className="text-xl font-bold text-text-primary">Create your account</h1>
          <p className="mt-1 text-sm text-text-secondary">No credit card required.</p>

          <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-4">
            <Input
              type="text"
              placeholder="Full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              leadingIcon={<UserIcon size={16} />}
              autoComplete="name"
            />
            <Input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              leadingIcon={<Mail size={16} />}
              required
              autoComplete="email"
            />
            <Input
              type="password"
              placeholder="Password (min. 8 characters)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              leadingIcon={<Lock size={16} />}
              required
              minLength={8}
              autoComplete="new-password"
            />

            {error && (
              <div className="flex items-center gap-2 rounded-xl border border-error/30 bg-error/10 px-3 py-2 text-sm text-error">
                <AlertCircle size={16} className="shrink-0" />
                {error}
              </div>
            )}

            <Button type="submit" fullWidth disabled={submitting}>
              {submitting ? "Creating account..." : "Create Account"}
            </Button>
          </form>
        </div>
        <p className="mt-6 text-center text-sm text-text-secondary">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-text-primary hover:text-accent">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
