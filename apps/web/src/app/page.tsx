"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, User, HeartHandshake, Store, Users, ClipboardList, SlidersHorizontal, ScrollText } from "lucide-react";
import { login, type ApiError } from "@/lib/api";
import { getSession, saveSession } from "@/lib/session";
import Logo from "@/components/logo";

const DEMO = [
  { user: "citizen_parveen", ur: "بیوہ", en: "Widow", Icon: HeartHandshake, tone: "from-rose-500 to-pink-600" },
  { user: "citizen_tariq", ur: "دکاندار", en: "Shopkeeper", Icon: Store, tone: "from-amber-400 to-orange-500" },
  { user: "helper_shazia", ur: "مددگار", en: "Helper", Icon: Users, tone: "from-sky-500 to-blue-600" },
  { user: "officer_aslam", ur: "افسر", en: "Officer", Icon: ClipboardList, tone: "from-indigo-500 to-violet-600" },
  { user: "admin_ayesha", ur: "ایڈمن", en: "Admin", Icon: SlidersHorizontal, tone: "from-emerald-500 to-teal-600" },
  { user: "auditor_iqbal", ur: "آڈیٹر", en: "Auditor", Icon: ScrollText, tone: "from-slate-600 to-slate-800" },
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
      saveSession({ token: data.access_token, role: data.role, userId: data.user_id, username: data.username });
      router.push("/dashboard");
    } catch (e) {
      const err = e as ApiError;
      setError(err?.message_ur ?? err?.message_en ?? "Could not connect to server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-emerald-900 via-emerald-700 to-teal-500 flex items-center justify-center p-4">
      <div className="pattern-dots absolute inset-0" aria-hidden="true" />
      <div className="absolute -top-24 -start-24 w-80 h-80 rounded-full bg-emerald-300/30 blur-3xl animate-float" aria-hidden="true" />
      <div className="absolute -bottom-24 -end-24 w-96 h-96 rounded-full bg-amber-300/20 blur-3xl animate-float" aria-hidden="true" />

      <div className="relative w-full max-w-md space-y-5 animate-fade-up">
        <div className="text-center text-white space-y-2">
          <div className="flex justify-center animate-float"><Logo size={72} /></div>
          <h1 className="text-5xl font-bold">رہبر</h1>
          <p className="text-emerald-100">Rahbar — relief that finds its way to those who need it</p>
        </div>

        <div className="glass rounded-3xl shadow-lift p-6 space-y-4">
          <div className="relative">
            <User className="absolute top-4 start-4 w-6 h-6 text-emerald-600" />
            <input
              className="w-full h-14 border-2 rounded-2xl ps-12 pe-4 text-lg bg-white"
              placeholder="صارف کا نام / Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="relative">
            <Lock className="absolute top-4 start-4 w-6 h-6 text-emerald-600" />
            <input
              className="w-full h-14 border-2 rounded-2xl ps-12 pe-4 text-lg bg-white"
              type="password"
              placeholder="پاس ورڈ / Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            />
          </div>
          {error && <p className="text-red-600 text-center font-bold">{error}</p>}
          <button
            onClick={() => handleLogin()}
            disabled={loading}
            className="w-full h-14 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-600 text-white text-xl font-bold shadow-lift disabled:opacity-50"
          >
            {loading ? "..." : "لاگ ان · Login"}
          </button>
        </div>

        <div className="glass rounded-3xl p-4">
          <p className="text-sm text-emerald-900 mb-3 text-center font-bold">Quick demo · ایک ٹچ میں داخل ہوں (password123)</p>
          <div className="grid grid-cols-3 gap-2">
            {DEMO.map(({ user, ur, en, Icon, tone }) => (
              <button
                key={user}
                onClick={() => handleLogin(user, "password123")}
                disabled={loading}
                className="rounded-2xl bg-white p-3 flex flex-col items-center gap-1 shadow hover:-translate-y-0.5 transition disabled:opacity-50"
              >
                <span className={`w-11 h-11 rounded-xl bg-gradient-to-br ${tone} text-white flex items-center justify-center`}>
                  <Icon className="w-6 h-6" />
                </span>
                <span className="font-bold text-sm leading-tight">{ur}</span>
                <span className="text-xs text-gray-500 leading-tight">{en}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}