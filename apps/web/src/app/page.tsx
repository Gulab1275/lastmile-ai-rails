"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, User, HeartHandshake, Store, Users, ClipboardList, SlidersHorizontal, ScrollText, ChevronDown, ChevronUp, Info } from "lucide-react";
import { login, type ApiError } from "@/lib/api";
import { getSession, saveSession } from "@/lib/session";
import Logo from "@/components/logo";

const DEMO = [
  { user: "citizen_parveen", ur: "پروین بی بی", roleUr: "بیوہ شہری", en: "Parveen Bibi (Widow)", Icon: HeartHandshake, role: "citizen" },
  { user: "citizen_tariq", ur: "طارق جاوید", roleUr: "دکاندار شہری", en: "Tariq Javed (Shopkeeper)", Icon: Store, role: "citizen" },
  { user: "helper_shazia", ur: "شازیہ خان", roleUr: "مددگار ورکر", en: "Shazia Khan (Field Helper)", Icon: Users, role: "helper" },
  { user: "officer_aslam", ur: "اسلم خان", roleUr: "ریویو افسر", en: "Aslam Khan (Relief Officer)", Icon: ClipboardList, role: "officer" },
  { user: "admin_ayesha", ur: "عائشہ صدیق", roleUr: "پالیسی ایڈمن", en: "Ayesha Siddiq (Policy Admin)", Icon: SlidersHorizontal, role: "admin" },
  { user: "auditor_iqbal", ur: "اقبال احمد", roleUr: "آڈیٹر", en: "Iqbal Ahmed (Auditor)", Icon: ScrollText, role: "auditor" },
];

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAccountsHelper, setShowAccountsHelper] = useState(false);

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
      if (err.status === 401) {
        setError("صارف کا نام یا پاس ورڈ غلط ہے · Incorrect username or password");
      } else if (err.status === 403) {
        setError("آپ کو اس سسٹم میں داخلے کی اجازت نہیں · Access forbidden for this role");
      } else {
        setError(err?.message_ur ?? err?.message_en ?? "Could not connect to live backend");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#0B4F43] via-[#0F6B5A] to-[#08352D] flex items-center justify-center p-4">
      <div className="pattern-dots absolute inset-0 opacity-30" aria-hidden="true" />
      <div className="absolute -top-24 -start-24 w-80 h-80 rounded-full bg-[#DDEFE9]/20 blur-3xl animate-float" aria-hidden="true" />
      <div className="absolute -bottom-24 -end-24 w-96 h-96 rounded-full bg-[#E8A33D]/15 blur-3xl animate-float" aria-hidden="true" />

      <div className="relative w-full max-w-md space-y-4 animate-fade-up">
        <div className="text-center text-white space-y-1">
          <div className="flex justify-center mb-1"><Logo size={68} /></div>
          <h1 className="text-4xl font-bold tracking-tight">رہبر · Rahbar</h1>
          <p className="text-[#DDEFE9] text-sm">The Last Mile: AI on Public Rails (Coder&apos;s Cup &apos;26)</p>
        </div>

        {/* Login Card */}
        <div className="bg-white/95 backdrop-blur-md rounded-3xl shadow-lift p-6 space-y-4 border border-white/40">
          <div className="relative">
            <User className="absolute top-4 start-4 w-5 h-5 text-[#0F6B5A]" />
            <input
              className="w-full min-h-[52px] border-2 border-[#E2DDD3] rounded-2xl ps-12 pe-4 text-base bg-white text-[#17302B] focus:border-[#0F6B5A]"
              placeholder="صارف کا نام / Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="relative">
            <Lock className="absolute top-4 start-4 w-5 h-5 text-[#0F6B5A]" />
            <input
              className="w-full min-h-[52px] border-2 border-[#E2DDD3] rounded-2xl ps-12 pe-4 text-base bg-white text-[#17302B] focus:border-[#0F6B5A]"
              type="password"
              placeholder="پاس ورڈ / Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            />
          </div>
          {error && (
            <div className="bg-[#FEE2E2] border border-[#F87171] text-[#991B1B] rounded-2xl p-3 text-center font-bold text-sm">
              {error}
            </div>
          )}
          <button
            onClick={() => handleLogin()}
            disabled={loading || !username.trim()}
            className="w-full min-h-[52px] rounded-2xl bg-[#E8A33D] text-[#17302B] text-lg font-bold shadow hover:bg-[#d9942e] transition disabled:opacity-50"
          >
            {loading ? "لاگ ان ہو رہا ہے..." : "لاگ ان · Login"}
          </button>
        </div>

        {/* 1-Touch Quick Persona Login */}
        <div className="bg-white/90 backdrop-blur rounded-3xl p-4 shadow border border-white/30">
          <p className="text-xs text-[#0B4F43] mb-3 text-center font-bold">
            ایک ٹچ میں داخل ہوں · Quick Persona Demo (Pass: password123)
          </p>
          <div className="grid grid-cols-3 gap-2">
            {DEMO.map(({ user, ur, en, Icon }) => (
              <button
                key={user}
                onClick={() => handleLogin(user, "password123")}
                disabled={loading}
                className="min-h-[54px] rounded-2xl bg-white border border-[#E2DDD3] p-2 flex flex-col items-center gap-1 shadow-sm hover:border-[#0B4F43] hover:bg-[#DDEFE9]/30 transition disabled:opacity-50 text-center"
              >
                <div className="w-8 h-8 rounded-xl bg-[#0B4F43] text-[#E8A33D] flex items-center justify-center">
                  <Icon className="w-4 h-4" />
                </div>
                <span className="font-bold text-xs text-[#17302B] leading-tight truncate w-full">{ur}</span>
                <span className="text-[10px] text-[#5B6F6A] leading-tight truncate w-full">{en.split(" ")[0]}</span>
              </button>
            ))}
          </div>

          {/* Expandable Demo Accounts Helper */}
          <div className="mt-3 pt-3 border-t border-[#E2DDD3]">
            <button
              onClick={() => setShowAccountsHelper(!showAccountsHelper)}
              className="w-full flex items-center justify-between text-xs font-bold text-[#0B4F43] hover:underline"
            >
              <span className="flex items-center gap-1.5">
                <Info className="w-4 h-4" /> ڈیمو اکاؤنٹس کی تفصیل · View demo credentials guide
              </span>
              {showAccountsHelper ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {showAccountsHelper && (
              <div className="mt-2 text-xs text-[#17302B] space-y-1.5 bg-[#F7F4EE] rounded-xl p-3 border border-[#E2DDD3]">
                <p className="font-bold text-[#0B4F43]">All accounts share password: <code className="bg-white px-1.5 py-0.5 rounded border">password123</code></p>
                <ul className="list-disc ps-4 space-y-1">
                  {DEMO.map((d) => (
                    <li key={d.user}>
                      <span className="font-mono font-bold text-[#0B4F43]">{d.user}</span> — {d.en} ({d.roleUr})
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
