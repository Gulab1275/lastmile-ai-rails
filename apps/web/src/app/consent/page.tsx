"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  UserCheck, Wallet, Receipt, Users, Volume2, ShieldX, ShieldCheck,
  Building2, ExternalLink, CheckCircle2, Lock,
} from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type ConsentScope, type ConsentStatus, type ConsentRecord } from "@/lib/api";
import { getActiveCitizenId, getSession, speak } from "@/lib/session";

interface ScopeMeta {
  scope: ConsentScope;
  icon: React.ReactNode;
  ur: string;
  en: string;
  descUr: string;
  descEn: string;
}

const SCOPES: ScopeMeta[] = [
  {
    scope: "identity",
    icon: <UserCheck className="w-8 h-8" />,
    ur: "شناخت کی تفصیلات",
    en: "Identity Verification",
    descUr: "نادرا اور سرکاری ڈیٹا سے آپ کے شناختی کارڈ اور نام کی تصدیق۔",
    descEn: "NADRA biometric and name matching verification.",
  },
  {
    scope: "income",
    icon: <Wallet className="w-8 h-8" />,
    ur: "آمدنی و مالی حالات",
    en: "Household Income",
    descUr: "احساس/بی آئی ایس پی کی غربت جانچ اور کیش گرانٹ کی اہلیت۔",
    descEn: "Eligibility and poverty scoring against income threshold.",
  },
  {
    scope: "bills",
    icon: <Receipt className="w-8 h-8" />,
    ur: "یوٹیلیٹی و بجلی کے بل",
    en: "Utility Bills & Address",
    descUr: "بجلی اور گیس کے بل سے پتے اور رہائش کی تصدیق۔",
    descEn: "Address residency proof via meter reading and bill verification.",
  },
  {
    scope: "helper_acting",
    icon: <Users className="w-8 h-8" />,
    ur: "مددگار ورکر کے اختیارات",
    en: "Field Helper Acting Access",
    descUr: "آپ کا مجاز فیلڈ ورکر آپ کی طرف سے فارم بھر اور جمع کرا سکتا ہے۔",
    descEn: "Authorized helper can fill and lodge claims on your behalf.",
  },
];

type Probe =
  | { kind: "allowed"; caseId: string }
  | { kind: "blocked"; err: ApiError }
  | { kind: "none" }
  | { kind: "error"; err: ApiError };

export default function ConsentPage() {
  const [role, setRole] = useState("");
  const [citizenId, setCitizenId] = useState("");
  const [status, setStatus] = useState<ConsentStatus | null>(null);
  const [busy, setBusy] = useState<string>("");
  const [error, setError] = useState("");
  const [lastRevocation, setLastRevocation] = useState<ConsentRecord | null>(null);
  const [probe, setProbe] = useState<Probe | null>(null);
  const [probing, setProbing] = useState(false);

  const load = useCallback(async (id: string) => {
    try {
      setStatus(await api.getConsentStatus(id));
    } catch (e) {
      const err = e as ApiError;
      setError(err.message_ur ?? err.message_en ?? "Could not load consent status");
    }
  }, []);

  useEffect(() => {
    const id = getActiveCitizenId();
    setCitizenId(id);
    setRole(getSession()?.role ?? "");
    if (id) load(id);
  }, [load]);

  async function toggle(scope: ConsentScope, isOn: boolean) {
    setBusy(scope);
    setError("");
    setProbe(null);
    try {
      if (isOn) {
        const revokedRecord = await api.withdrawConsent(citizenId, scope, "Revoked by citizen via web ledger");
        setLastRevocation(revokedRecord);
        speak("رضامندی منسوخ کر دی گئی ہے۔ اب رسائی فوری بلاک ہے۔", "ur-PK");
      } else {
        await api.grantConsent(citizenId, scope);
        setLastRevocation(null);
        speak("رضامندی فراہم کر دی گئی ہے۔", "ur-PK");
      }
      await load(citizenId);
    } catch (e) {
      const err = e as ApiError;
      setError(err.message_ur ?? err.message_en ?? "Error updating consent");
    } finally {
      setBusy("");
    }
  }

  // Live Access Check (Proof of Instant 403 upon revocation)
  async function checkAccess() {
    setProbing(true);
    setProbe(null);
    try {
      const mine = (await api.listCases()).filter((c) => c.citizen_id === citizenId);
      if (mine.length === 0) {
        setProbe({ kind: "none" });
        return;
      }
      await api.getCase(mine[0].id);
      setProbe({ kind: "allowed", caseId: mine[0].id });
    } catch (e) {
      const err = e as ApiError;
      setProbe(err.status === 403 ? { kind: "blocked", err } : { kind: "error", err });
    } finally {
      setProbing(false);
    }
  }

  return (
    <AppShell title="رضامندی لیجر · Consent & Data Ledger">
      <div className="bg-white rounded-3xl p-5 border border-[#E2DDD3] shadow-sm space-y-2">
        <h2 className="text-xl font-bold text-[#0B4F43]">میرا ڈیٹا کس کے پاس ہے؟ · Who Has My Data</h2>
        <p className="text-sm text-[#5B6F6A]">
          آپ کے ڈیٹا پر مکمل کنٹرول آپ کا ہے۔ آپ کسی بھی وقت کسی بھی ایجنسی یا مددگار کی رسائی منسوخ کر سکتے ہیں۔ منسوخی پر سرور فوری طور پر رسائی بلاک (HTTP 403) کرتا ہے۔
        </p>
      </div>

      {error && (
        <div className="bg-[#FEE2E2] border border-[#F87171] text-[#991B1B] rounded-2xl p-3 font-bold text-sm">
          {error}
        </div>
      )}

      {/* Immediate "Access Stopped" Confirmation with Audit Link */}
      {lastRevocation && (
        <div className="bg-[#FEF3C7] border-2 border-[#C77700] rounded-3xl p-5 space-y-3 shadow-md animate-fade-up">
          <div className="flex items-center gap-3">
            <Lock className="w-8 h-8 text-[#C77700] shrink-0" />
            <div>
              <p className="text-xl font-bold text-[#92400E]">رسائی فوری طور پر روک دی گئی · Access Stopped</p>
              <p className="text-xs text-[#78350F]">
                Scope: <span className="font-mono font-bold uppercase">{lastRevocation.scope}</span> · Revoked at {new Date(lastRevocation.revoked_at || Date.now()).toLocaleTimeString()}
              </p>
            </div>
          </div>
          <p className="text-sm text-[#17302B]">
            سرور نے فوری طور پر اس ڈیٹا تک تمام بیرونی رسائی بلاک کر دی ہے۔ یہ منسوخی ڈیجیٹل آڈٹ ہیش چین میں محفوظ ہو چکی ہے۔
          </p>
          {lastRevocation.audit_hash && (
            <div className="bg-white rounded-xl p-3 border border-[#FCD34D] text-xs space-y-1">
              <span className="font-bold text-[#0B4F43]">آڈٹ لاگ ہیش · Cryptographic Audit Hash:</span>
              <p className="font-mono text-[11px] text-[#5B6F6A] break-all">{lastRevocation.audit_hash}</p>
              <Link
                href="/auditor"
                className="inline-flex items-center gap-1 font-bold text-[#0B4F43] hover:underline pt-1 text-xs"
              >
                آڈٹ چین میں تصدیق دیکھیں · Verify in Audit Ledger <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          )}
        </div>
      )}

      {/* "Who has my data" Grantee Cards */}
      <div className="space-y-4">
        {/* Card 1: Government Public Rails Grantee */}
        <div className="bg-white rounded-3xl border border-[#E2DDD3] shadow p-5 space-y-3">
          <div className="flex items-center gap-3 border-b border-[#E2DDD3] pb-3">
            <div className="w-10 h-10 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] flex items-center justify-center">
              <Building2 className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <p className="font-bold text-[#17302B]">سرکاری ڈی پی آئی ریلز · Government DPI Rails (NADRA, BISP, Raast)</p>
              <p className="text-xs text-[#5B6F6A]">اہلیت کی جانچ اور براہ راست رقم کی منتقلی کے لیے</p>
            </div>
          </div>

          <div className="grid gap-3 pt-1">
            {SCOPES.slice(0, 3).map((s) => {
              const isOn = !!status?.active_scopes.includes(s.scope);
              const record = status?.all_consents.find((c) => c.scope === s.scope);
              return (
                <div key={s.scope} className="bg-[#F7F4EE] rounded-2xl p-4 border border-[#E2DDD3] space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className={isOn ? "text-[#1F8A5B]" : "text-[#5B6F6A]"}>{s.icon}</span>
                      <div>
                        <p className="font-bold text-sm text-[#17302B]">{s.ur} · {s.en}</p>
                        <p className="text-xs text-[#5B6F6A]">{s.descUr}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => speak(s.descUr)}
                      type="button"
                      className="min-h-[36px] min-w-[36px] rounded-xl bg-white text-[#0B4F43] flex items-center justify-center border border-[#E2DDD3]"
                      aria-label="Listen description"
                    >
                      <Volume2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                      isOn ? "bg-[#DDEFE9] text-[#0B4F43]" : "bg-slate-200 text-[#5B6F6A]"
                    }`}>
                      {isOn ? "✓ فعال (Active)" : "منسوخ (Revoked)"}
                    </span>

                    <button
                      onClick={() => toggle(s.scope, isOn)}
                      disabled={busy === s.scope || !status}
                      type="button"
                      className={`min-h-[44px] px-5 rounded-xl font-bold text-sm transition ${
                        isOn
                          ? "bg-white border-2 border-[#B3261E] text-[#B3261E] hover:bg-[#FEE2E2]"
                          : "bg-[#0B4F43] text-white hover:bg-[#093e34]"
                      } disabled:opacity-50`}
                    >
                      {busy === s.scope ? "..." : isOn ? "واپس لیں · Withdraw" : "اجازت دیں · Grant"}
                    </button>
                  </div>

                  {record && (
                    <p className="text-[10px] text-[#5B6F6A] font-mono">
                      {isOn ? `Active since: ${new Date(record.granted_at).toLocaleDateString()}` : `Revoked: ${record.revoked_at ? new Date(record.revoked_at).toLocaleDateString() : ""}`}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Card 2: Field Helper Grantee */}
        <div className="bg-white rounded-3xl border border-[#E2DDD3] shadow p-5 space-y-3">
          <div className="flex items-center gap-3 border-b border-[#E2DDD3] pb-3">
            <div className="w-10 h-10 rounded-2xl bg-[#FEF3C7] text-[#92400E] flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <p className="font-bold text-[#17302B]">مددگار ورکر · Field Helper (Shazia Khan)</p>
              <p className="text-xs text-[#5B6F6A]">فیلڈ میں آپ کی جانب سے درخواستیں جمع کرانے کے اختیارات</p>
            </div>
          </div>

          {(() => {
            const s = SCOPES[3]; // helper_acting
            const isOn = !!status?.active_scopes.includes(s.scope);
            return (
              <div className="bg-[#F7F4EE] rounded-2xl p-4 border border-[#E2DDD3] space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className={isOn ? "text-[#1F8A5B]" : "text-[#5B6F6A]"}>{s.icon}</span>
                    <div>
                      <p className="font-bold text-sm text-[#17302B]">{s.ur} · {s.en}</p>
                      <p className="text-xs text-[#5B6F6A]">{s.descUr}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => speak(s.descUr)}
                    type="button"
                    className="min-h-[36px] min-w-[36px] rounded-xl bg-white text-[#0B4F43] flex items-center justify-center border border-[#E2DDD3]"
                    aria-label="Listen description"
                  >
                    <Volume2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                    isOn ? "bg-[#DDEFE9] text-[#0B4F43]" : "bg-slate-200 text-[#5B6F6A]"
                  }`}>
                    {isOn ? "✓ مجاز ہے (Authorized)" : "اختیار منسوخ (Revoked)"}
                  </span>

                  <button
                    onClick={() => toggle(s.scope, isOn)}
                    disabled={busy === s.scope || !status}
                    type="button"
                    className={`min-h-[44px] px-5 rounded-xl font-bold text-sm transition ${
                      isOn
                        ? "bg-white border-2 border-[#B3261E] text-[#B3261E] hover:bg-[#FEE2E2]"
                        : "bg-[#0B4F43] text-white hover:bg-[#093e34]"
                    } disabled:opacity-50`}
                  >
                    {busy === s.scope ? "..." : isOn ? "اختیار واپس لیں · Withdraw" : "اختیار دیں · Authorize"}
                  </button>
                </div>
              </div>
            );
          })()}
        </div>
      </div>

      {/* Realtime 403 Enforcement Probe for Judges & Testers */}
      <div className="bg-white rounded-3xl border-2 border-[#38BDF8] p-5 shadow space-y-3">
        <div className="flex items-center justify-between">
          <p className="font-bold text-lg text-[#075985]">رسائی کی براہ راست جانچ · Live Access Control Test</p>
          <span className="text-xs font-bold bg-[#E0F2FE] text-[#0369A1] px-2.5 py-1 rounded-full">Proof of 403</span>
        </div>
        <p className="text-xs text-[#5B6F6A]">
          اوپر سے رضامندی منسوخ کرنے کے بعد بٹن دبائیں۔ اگر رضامندی واپس لی گئی ہے تو سرور کیس ڈیٹا دینے سے انکار کر کے <b>HTTP 403 Forbidden</b> دے گا۔
        </p>
        <button
          onClick={checkAccess}
          disabled={probing || !citizenId}
          type="button"
          className="w-full min-h-[48px] rounded-2xl bg-[#0284C7] text-white font-bold text-base hover:bg-[#0369A1] transition disabled:opacity-40"
        >
          {probing ? "سرور سے چیک ہو رہا ہے..." : "Try reading citizen's case as a third party"}
        </button>

        {probe?.kind === "blocked" && (
          <div className="rounded-2xl bg-[#FEE2E2] border border-[#F87171] text-[#7F1D1D] p-4 flex gap-3">
            <ShieldX className="w-10 h-10 shrink-0 text-[#B3261E]" />
            <div className="space-y-1">
              <p className="text-lg font-bold">HTTP {probe.err.status} — ACCESS BLOCKED</p>
              <p className="text-sm font-bold">{probe.err.message_ur ?? "رضامندی کے بغیر رسائی بلاک کر دی گئی ہے"}</p>
              <p className="text-xs text-[#991B1B]">{probe.err.message_en}</p>
              <p className="text-xs text-[#5B6F6A] pt-1">یہ بلاک شدہ کوشش خودکار طریقے سے آڈٹ لاگ میں درج ہو گئی ہے۔</p>
            </div>
          </div>
        )}

        {probe?.kind === "allowed" && (
          <div className="rounded-2xl bg-[#DDEFE9] border border-[#1F8A5B] text-[#065F46] p-4 flex gap-3 items-center">
            <CheckCircle2 className="w-8 h-8 shrink-0 text-[#1F8A5B]" />
            <div>
              <p className="font-bold text-sm">رسائی منظور ہے · Allowed</p>
              <p className="text-xs">کیونکہ متعلقہ اسکوپ فعال ہے، کیس {probe.caseId} کامیابی سے پڑھ لیا گیا۔</p>
            </div>
          </div>
        )}

        {probe?.kind === "none" && (
          <p className="bg-[#FEF3C7] text-[#92400E] rounded-xl p-3 text-xs">
            اس شہری کے نام پر ابھی کوئی کیس موجود نہیں ہے۔ پہلے <Link href="/apply" className="underline font-bold">درخواست</Link> میں کیس بنائیں۔
          </p>
        )}
      </div>
    </AppShell>
  );
}
