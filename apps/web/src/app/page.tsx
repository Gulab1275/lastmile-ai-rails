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
    roleUr: "بیوہ شہری · غیر خواندہ",
    en: "Parveen Bibi (Widow)",
    subtitle: "صوتی اور تصویری امداد",
    Illustration: WidowParveenIllustration,
    accent: "border-[#F472B6] hover:bg-[#FDF2F8]",
    tag: "Voice-First",
  },
  {
    user: "citizen_tariq",
    ur: "طارق جاوید",
    roleUr: "دکاندار شہری · ریلیف سائل",
    en: "Tariq Javed (Shopkeeper)",
    subtitle: "فوری راستی پیمنٹ ٹریکر",
    Illustration: ShopkeeperTariqIllustration,
    accent: "border-[#F59E0B] hover:bg-[#FEF3C7]",
    tag: "Fast Track",
  },
  {
    user: "helper_shazia",
    ur: "شازیہ خان",
    roleUr: "فیلڈ مددگار · آن دا گراؤنڈ",
    en: "Shazia Khan (Field Helper)",
    subtitle: "مشترکہ فون اور آف لائن سنک",
    Illustration: HelperShaziaIllustration,
    accent: "border-[#0284C7] hover:bg-[#E0F2FE]",
    tag: "Field Worker",
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
        setError("صارف کا نام یا پاس ورڈ درست نہیں ہے · Incorrect username or password (try password123)");
      } else if (err.status === 403) {
        setError("اس رول کے لیے اجازت دستیاب نہیں · Access forbidden for this persona");
      } else {
        setError(err?.message_ur ?? err?.message_en ?? "سرور سے رابطہ قائم نہیں ہو سکا · Could not connect to live backend");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#0B4F43] via-[#0F6B5A] to-[#08352D] flex flex-col items-center justify-center p-4">
      {/* Subtle traditional geometric pattern */}
      <div className="pattern-dots absolute inset-0 opacity-25" aria-hidden="true" />
      <div className="absolute -top-24 -start-24 w-80 h-80 rounded-full bg-[#DDEFE9]/20 blur-3xl animate-float" aria-hidden="true" />
      <div className="absolute -bottom-24 -end-24 w-96 h-96 rounded-full bg-[#E8A33D]/15 blur-3xl animate-float" aria-hidden="true" />

      <div className="relative w-full max-w-lg space-y-4 animate-fade-up py-4">
        {/* Brand Hero & "The Path" Motif */}
        <div className="text-center text-white space-y-2">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-2xl bg-white/10 backdrop-blur border border-white/20 flex items-center justify-center shadow-lift">
              <Logo size={48} />
            </div>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold font-heading tracking-tight">رہبر · Rahbar</h1>
          <p className="text-base sm:text-lg text-[#DDEFE9] font-bold">
            ریلیف جو سیدھا مستحق تک پہنچے
          </p>
          <p className="text-xs text-[#DDEFE9]/80 font-sans">
            AI on Public Rails · Relief assistance for those who cannot read forms
          </p>
        </div>

        {/* 3 Citizen Hero Characters Illustration Strip */}
        <div className="bg-white/95 backdrop-blur-md rounded-3xl p-4 shadow-lift border border-white/40 space-y-3">
          <div className="flex items-center justify-between pb-1">
            <span className="text-xs font-bold text-[#0B4F43] flex items-center gap-1.5 font-heading text-sm">
              <Sparkles className="w-4 h-4 text-[#E8A33D]" /> ایک ٹچ میں لاگ ان کریں · Tap a Persona to Enter
            </span>
            <span className="text-[10px] text-[#5B6F6A] font-mono">Password: password123</span>
          </div>

          {/* 3 Core Citizen Personas */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {PERSONAS.map(({ user, ur, en, subtitle, Illustration, accent, tag }) => (
              <button
                key={user}
                onClick={() => handleLogin(user, "password123")}
                disabled={loading}
                type="button"
                className={`min-h-[110px] rounded-2xl bg-white border-2 ${accent} p-3 flex flex-col items-center justify-center text-center transition shadow-sm hover:shadow-md hover:-translate-y-0.5 active:scale-95 disabled:opacity-50`}
              >
                <Illustration size={48} />
                <p className="font-bold text-sm text-[#17302B] mt-1 font-heading leading-tight">{ur}</p>
                <p className="text-[10px] text-[#5B6F6A] font-sans truncate w-full">{en.split(" ")[0]}</p>
                <span className="text-[9px] font-bold bg-[#F7F4EE] text-[#0B4F43] px-1.5 py-0.5 rounded-full mt-1">
                  {tag}
                </span>
              </button>
            ))}
          </div>

          {/* Institutional Personas: Officer, Admin, Auditor */}
          <div className="grid grid-cols-3 gap-2 pt-1 border-t border-[#E2DDD3]">
            {ADMIN_PERSONAS.map(({ user, ur, en, role, icon }) => (
              <button
                key={user}
                onClick={() => handleLogin(user, "password123")}
                disabled={loading}
                type="button"
                className="min-h-[48px] rounded-xl bg-[#F7F4EE] border border-[#E2DDD3] p-1.5 flex items-center gap-1.5 text-start hover:border-[#0B4F43] transition disabled:opacity-50"
              >
                <span className="text-base px-1">{icon}</span>
                <div className="min-w-0">
                  <p className="font-bold text-[11px] text-[#17302B] truncate">{ur}</p>
                  <p className="text-[9px] text-[#5B6F6A] truncate">{role}</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Traditional Credentials Form Card */}
        <div className="bg-white/95 backdrop-blur-md rounded-3xl shadow-lift p-5 space-y-3.5 border border-white/40">
          <p className="text-xs font-bold text-[#5B6F6A] text-center">یا اپنا شناختی یوزر نام درج کریں · Or sign in with username</p>

          <div className="space-y-2">
            <div className="relative">
              <User className="absolute top-3.5 start-4 w-5 h-5 text-[#0F6B5A]" />
              <input
                className="w-full min-h-[48px] border-2 border-[#E2DDD3] rounded-2xl ps-12 pe-4 text-sm bg-white text-[#17302B] focus:border-[#0F6B5A]"
                placeholder="صارف کا نام / Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div className="relative">
              <Lock className="absolute top-3.5 start-4 w-5 h-5 text-[#0F6B5A]" />
              <input
                className="w-full min-h-[48px] border-2 border-[#E2DDD3] rounded-2xl ps-12 pe-4 text-sm bg-white text-[#17302B] focus:border-[#0F6B5A]"
                type="password"
                placeholder="پاس ورڈ / Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              />
            </div>
          </div>

          {error && (
            <div className="bg-[#FEE2E2] border border-[#F87171] text-[#991B1B] rounded-2xl p-3 text-center font-bold text-xs">
              {error}
            </div>
          )}

          {/* Primary Action Button: Amber #E8A33D with dark text #17302B */}
          <button
            onClick={() => handleLogin()}
            disabled={loading || !username.trim()}
            type="button"
            className="w-full min-h-[50px] rounded-2xl bg-[#E8A33D] text-[#17302B] text-base font-bold shadow hover:bg-[#d9942e] transition disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? "لاگ ان ہو رہا ہے..." : "لاگ ان کریں · Sign In"}
            <ArrowLeft className="w-4 h-4 rtl:rotate-0 rotate-180" />
          </button>

          {/* Expandable Demo Guide */}
          <div className="pt-1 text-center">
            <button
              onClick={() => setShowAccountsHelper(!showAccountsHelper)}
              className="text-xs font-bold text-[#0B4F43] inline-flex items-center gap-1 hover:underline"
              type="button"
            >
              <Info className="w-3.5 h-3.5" /> تمام ڈیمو اکاؤنٹس کی فہرست · View demo accounts guide
              {showAccountsHelper ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showAccountsHelper && (
              <div className="mt-2 text-start text-xs text-[#17302B] bg-[#F7F4EE] rounded-2xl p-3 border border-[#E2DDD3] space-y-1 animate-fade-up">
                <p className="font-bold text-[#0B4F43]">Common Password: <code className="bg-white px-1.5 py-0.5 rounded border">password123</code></p>
                <ul className="list-disc ps-4 space-y-1 text-[11px]">
                  <li><span className="font-mono font-bold">citizen_parveen</span> — پروین بی بی (Widow / Biometrics)</li>
                  <li><span className="font-mono font-bold">citizen_tariq</span> — طارق جاوید (Shopkeeper / Fast Payouts)</li>
                  <li><span className="font-mono font-bold">helper_shazia</span> — شازیہ خان (Field Helper / Acting Mode)</li>
                  <li><span className="font-mono font-bold">officer_aslam</span> — اسلم خان (Relief Review Officer)</li>
                  <li><span className="font-mono font-bold">admin_ayesha</span> — عائشہ صدیق (Policy Rules & API Keys)</li>
                  <li><span className="font-mono font-bold">auditor_iqbal</span> — اقبال احمد (Audit Trail Inspector)</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
