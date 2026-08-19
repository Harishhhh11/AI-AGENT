import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            email,
            password,
          }),
        }
      );

      const result = await response.json();

      console.log("LOGIN RESPONSE:", result);

      if (!response.ok) {
        throw new Error(
          result?.detail ||
            result?.message ||
            "Login failed."
        );
      }

      /*
       * Backend response:
       *
       * {
       *   success: true,
       *   message: "Login successful.",
       *   data: {
       *     access_token: "...",
       *     token_type: "bearer"
       *   }
       * }
       */

      const accessToken =
        result?.data?.access_token;

      if (!accessToken) {
        throw new Error(
          "Login succeeded, but no access token was returned."
        );
      }

      // Store JWT
      localStorage.setItem(
        "access_token",
        accessToken
      );

      // Store token type
      localStorage.setItem(
        "token_type",
        result?.data?.token_type || "bearer"
      );

      console.log(
        "Login successful. Token saved."
      );

      // Go to dashboard
      navigate("/", {
        replace: true,
      });

    } catch (err) {
      console.error(
        "LOGIN ERROR:",
        err
      );

      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(
          "Unable to connect to the server."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top_right,#e0e7ff,transparent_35%),#f5f7fb] px-4 py-8 sm:px-6">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-3xl border border-white/80 bg-white shadow-[0_24px_80px_rgba(15,23,42,0.12)] lg:grid-cols-[1.05fr_0.95fr]">
        <div className="hidden bg-slate-950 p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div>
            <div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500 font-bold">AI</span><span className="font-semibold">AI Receptionist</span></div>
            <h2 className="mt-20 text-4xl font-bold leading-tight">Turn every customer conversation into momentum.</h2>
            <p className="mt-5 max-w-sm text-sm leading-7 text-slate-300">Manage knowledge, conversations, and qualified leads from one calm, focused workspace.</p>
          </div>
          <p className="text-xs text-slate-400">Secure workspace access</p>
        </div>
        <div className="p-6 sm:p-10 lg:p-14">
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Welcome back</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Sign in to your workspace</h1>
          <p className="mt-2 text-sm text-slate-500">Access your AI receptionist dashboard.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-5">
            <label htmlFor="email" className="mb-2 block text-sm font-semibold text-slate-700">
              Email
            </label>

            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="admin@example.com"
              required
              autoComplete="email"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-500/10"
            />
          </div>

          <div className="mb-5">
            <label htmlFor="password" className="mb-2 block text-sm font-semibold text-slate-700">
              Password
            </label>

            <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Enter your password"
              required
              autoComplete="current-password"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 pr-20 text-sm outline-none transition focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-500/10"
            />
            <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-slate-500 hover:text-indigo-600">{showPassword ? "Hide" : "Show"}</button>
            </div>
          </div>

          {error && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-indigo-600 px-4 py-3.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading
              ? "Signing in..."
              : "Sign In"}
          </button>
        </form>
        </div>
      </div>
    </div>
  );
}

export default Login;
