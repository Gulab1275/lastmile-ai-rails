"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, User, ChevronDown, ChevronUp, Info, ArrowLeft, Shield, Sparkles } from "lucide-react";
import { login, type ApiError } from "@/lib/api";
import { getSession, saveSession } from "@/lib/session";
import Logo from "@/components/logo";
import {
  WidowParveenIllustration,
  ShopkeeperTariqIllustration,
  HelperShaziaIllustration,
} from "@/components/ui/PersonaIllustrations";

const PERSONAS = [
  {
    user: "citizen_parveen",
    ur: "پروین بی بی",
    en: "Parveen Bibi (Widow)",
    subtitle: "صوتی اور تصویری امداد",
    Illustration: WidowParveenIllustration,
    tag: "صوتی معاونت · Voice",
    badgeBg: "bg-pink-50 text-pink-700 border-pink-200",
  },
  {
    user: "citizen_tariq",
    ur: "طارق جاوید",
    en: "Tariq Javed (Shopkeeper)",
    subtitle: "فوری راستی پیمنٹ ٹریکر",
    Illustration: ShopkeeperTariqIllustration,
    tag: "تیز رفتار · Fast Track",
    badgeBg: "bg-amber-50 text-amber-800 border-amber-200",
  },
  {
    user: "helper_shazia",
    ur: "شازیہ خان",
    en: "Shazia Khan (Field Helper)",
    subtitle: "مشترکہ فون اور آف لائن سنک",
    Illustration: HelperShaziaIllustration,
    tag: "فیلڈ ورکر · Helper",
    badgeBg: "bg-sky-50 text-sky-800 border-sky-200",
  },
];

const ADMIN_PERSONAS = [
  { user: "officer_aslam", ur: "اسلم خان", en: "Officer Aslam", role: "Human Review", icon: "⚖️" },
  { user: "admin_ayesha", ur: "عائشہ صدیق", en: "Admin Ayesha", role: "Rules & Keys", icon: "⚙️" },
  { user: "auditor_iqbal", ur: "اقبال احمد", en: "Auditor Iqbal", role: "Audit Hash Trail", icon: "📜" },
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
        setError("صارف کا نام یا پاس ورڈ درست نہیں ہے · Incorrect credentials (use password123)");
      } else if (err.status === 403) {
        setError("اس رول کے لیے اجازت دستیاب نہیں · Access forbidden for this role");
      } else {
        setError(err?.message_ur ?? err?.message_en ?? "سرور سے رابطہ قائم نہیں ہو سکا · Could not connect to backend");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 py-8 sm:py-12">
      <div className="w-full max-w-xl space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-2 rounded-2xl bg-[#0B4F43] shadow-md mb-1">
            <Logo size={44} />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold font-heading text-slate-900 tracking-tight">
            رہبر <span className="text-xl font-normal text-slate-500 font-sans">· Rahbar</span>
          </h1>
          <p className="text-base font-semibold text-[#0B4F43]">
            ریلیف جو سیدھا مستحق تک پہنچے
          </p>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            AI on Public Rails — Relief assistance designed for citizens on weak connections and without form literacy.
          </p>
        </div>

        {/* 1-Touch Demo Persona Selection Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#D97706]" />
              <span className="font-bold text-sm text-slate-900">
                ایک ٹچ میں لاگ ان کریں · Demo Personas
              </span>
            </div>
            <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
              Default PIN: password123
            </span>
          </div>

          {/* 3 Core Citizen Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {PERSONAS.map(({ user, ur, en, subtitle, Illustration, tag, badgeBg }) => (
              <button
                key={user}
                onClick={() => handleLogin(user, "password123")}
                disabled={loading}
                type="button"
                className="rounded-xl border border-slate-200 p-3.5 flex flex-col items-center text-center transition hover:border-[#0B4F43] hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-[#0B4F43] active:scale-[0.98] disabled:opacity-50 group"
              >
                <div className="mb-2">
                  <Illustration size={44} />
                </div>
                <p className="font-bold text-sm text-slate-900 leading-snug group-hover:text-[#0B4F43]">
                  {ur}
                </p>
                <p className="text-[11px] text-slate-500 font-sans mt-0.5">
                  {en.split(" ")[0]}
                </p>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border mt-2 ${badgeBg}`}>
                  {tag}
                </span>
              </button>
            ))}
          </div>

          {/* Operational Roles: Officer, Admin, Auditor */}
          <div className="pt-2 border-t border-slate-100 space-y-2">
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              سرکاری و تکنیکی رول · Institutional Roles:
            </p>
            <div className="grid grid-cols-3 gap-2">
              {ADMIN_PERSONAS.map(({ user, ur, en, role, icon }) => (
                <button
                  key={user}
                  onClick={() => handleLogin(user, "password123")}
                  disabled={loading}
                  type="button"
                  className="rounded-xl border border-slate-200 bg-slate-50/70 p-2 text-center hover:bg-white hover:border-[#0B4F43] transition focus:outline-none focus:ring-2 focus:ring-[#0B4F43] disabled:opacity-50"
                >
                  <span className="text-base block mb-0.5">{icon}</span>
                  <p className="font-bold text-xs text-slate-900 truncate">{ur}</p>
                  <p className="text-[10px] text-slate-500 truncate">{role}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Traditional Credentials Form Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6 space-y-4">
          <p className="font-bold text-sm text-slate-900">
            یا صارف نام اور پاس ورڈ درج کریں · Or sign in with username
          </p>

          <div className="space-y-3">
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700">
                صارف کا نام · Username
              </label>
              <div className="relative">
                <User className="absolute top-3 start-3.5 w-4 h-4 text-slate-400" />
                <input
                  className="w-full min-h-[46px] border border-slate-300 rounded-xl ps-10 pe-4 text-sm bg-white text-slate-900 focus:border-[#0B4F43] focus:ring-1 focus:ring-[#0B4F43]"
                  placeholder="e.g. citizen_parveen"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700">
                پاس ورڈ · Password
              </label>
              <div className="relative">
                <Lock className="absolute top-3 start-3.5 w-4 h-4 text-slate-400" />
                <input
                  className="w-full min-h-[46px] border border-slate-300 rounded-xl ps-10 pe-4 text-sm bg-white text-slate-900 focus:border-[#0B4F43] focus:ring-1 focus:ring-[#0B4F43]"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                />
              </div>
            </div>
          </div>

          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-3 text-xs font-medium">
              {error}
            </div>
          )}

          <button
            onClick={() => handleLogin()}
            disabled={loading || !username.trim()}
            type="button"
            className="w-full min-h-[48px] rounded-xl bg-[#0B4F43] text-white text-sm font-bold shadow-sm hover:bg-[#084137] transition disabled:opacity-50 flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-[#0B4F43] focus:ring-offset-2"
          >
            {loading ? "لاگ ان ہو رہا ہے..." : "لاگ ان کریں · Sign In"}
            <ArrowLeft className="w-4 h-4 rtl:rotate-0 rotate-180" />
          </button>

          {/* Accounts Guide */}
          <div className="pt-2 text-center">
            <button
              onClick={() => setShowAccountsHelper(!showAccountsHelper)}
              className="text-xs text-slate-600 inline-flex items-center gap-1 hover:text-[#0B4F43] font-medium"
              type="button"
            >
              <Info className="w-3.5 h-3.5" />
              <span>ڈیمو اکاؤنٹس کی تفصیلات · View demo accounts guide</span>
              {showAccountsHelper ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showAccountsHelper && (
              <div className="mt-3 text-start text-xs text-slate-700 bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-2">
                <p className="font-bold text-[#0B4F43]">
                  Common Password: <code className="bg-white px-2 py-0.5 rounded border border-slate-200 font-mono">password123</code>
                </p>
                <div className="space-y-1.5 pt-1">
                  <p><span className="font-mono font-bold text-slate-900">citizen_parveen</span> — پروین بی بی (Widow / Biometrics)</p>
                  <p><span className="font-mono font-bold text-slate-900">citizen_tariq</span> — طارق جاوید (Shopkeeper / Fast Payouts)</p>
                  <p><span className="font-mono font-bold text-slate-900">helper_shazia</span> — شازیہ خان (Field Helper / Acting Mode)</p>
                  <p><span className="font-mono font-bold text-slate-900">officer_aslam</span> — اسلم خان (Relief Review Officer)</p>
                  <p><span className="font-mono font-bold text-slate-900">admin_ayesha</span> — عائشہ صدیق (Policy Rules & API Keys)</p>
                  <p><span className="font-mono font-bold text-slate-900">auditor_iqbal</span> — اقبال احمد (Audit Trail Inspector)</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
