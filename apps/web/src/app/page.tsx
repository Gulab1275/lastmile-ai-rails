"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { login, type ApiError } from "@/lib/api";
import { getSession, saveSession } from "@/lib/session";

const DEMO = [
  { user: "citizen_parveen", label: "Widow · بیوہ" },
  { user: "citizen_tariq", label: "Shopkeeper · دکاندار" },
  { user: "helper_shazia", label: "Helper · مددگار" },
  { user: "officer_aslam", label: "Officer · افسر" },
  { user: "admin_ayesha", label: "Admin · ایڈمن" },
  { user: "auditor_iqbal", label: "Auditor · آڈیٹر" },
];

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (getSession()) router.replace("/dashboard");
  }, [router]);

  async function handleLogin(u = username, p = password) {
    setError("");
    setLoading(true);
    try {
      const data = await login(u, p);
      saveSession({
        token: data.access_token,
        role: data.role,
        userId: data.user_id,
        username: data.username,
      });
      router.push("/dashboard");
    } catch (e) {
      const err = e as ApiError;
      setError(err?.message_ur ?? err?.message_en ?? "Could not connect to server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-emerald-50 p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-lg p-8 space-y-5">
        <h1 className="text-4xl font-bold text-center text-emerald-700">رہبر</h1>
        <p className="text-center text-gray-600">Rahbar — Relief Support</p>

        <input
          className="w-full h-14 border-2 rounded-2xl px-4 text-lg"
          placeholder="صارف کا نام / Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          className="w-full h-14 border-2 rounded-2xl px-4 text-lg"
          type="password"
          placeholder="پاس ورڈ / Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleLogin()}
        />

        {error && <p className="text-red-600 text-center font-bold">{error}</p>}

        <button
          onClick={() => handleLogin()}
          disabled={loading}
          className="w-full h-14 rounded-2xl bg-emerald-600 text-white text-xl font-bold disabled:opacity-50"
        >
          {loading ? "..." : "لاگ ان / Login"}
        </button>

        <div className="border-t pt-4">
          <p className="text-sm text-gray-500 mb-2 text-center">Demo accounts (password123)</p>
          <div className="grid grid-cols-2 gap-2">
            {DEMO.map((d) => (
              <button
                key={d.user}
                onClick={() => handleLogin(d.user, "password123")}
                disabled={loading}
                className="h-12 rounded-xl bg-emerald-100 text-emerald-800 text-sm font-bold"
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}