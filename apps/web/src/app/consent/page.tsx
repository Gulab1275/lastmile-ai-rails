"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  UserCheck, Wallet, Receipt, Users, Volume2, ShieldX,
  Building2, ExternalLink, CheckCircle2, Lock,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { BigToggle } from "@/components/ui/BigToggle";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api, { type ApiError, type ConsentScope, type ConsentStatus, type ConsentRecord } from "@/lib/api";
import { getActiveCitizenId, speak } from "@/lib/session";

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
    icon: <UserCheck className="w-5 h-5" />,
    ur: "شناخت کی تفصیلات",
    en: "Identity Verification",
    descUr: "نادرا اور سرکاری ڈیٹا سے شناختی کارڈ اور نام کی تصدیق۔",
    descEn: "NADRA biometric and name matching verification.",
  },
  {
    scope: "income",
    icon: <Wallet className="w-5 h-5" />,
    ur: "آمدنی و مالی حالات",
    en: "Household Income",
    descUr: "احساس/بی آئی ایس پی کی غربت جانچ اور کیش گرانٹ کی اہلیت۔",
    descEn: "Eligibility and poverty scoring against income threshold.",
  },
  {
    scope: "bills",
    icon: <Receipt className="w-5 h-5" />,
    ur: "یوٹیلیٹی و بجلی کے بل",
    en: "Utility Bills & Address",
    descUr: "بجلی اور گیس کے بل سے پتے اور رہائش کی تصدیق۔",
    descEn: "Address residency proof via meter reading and bill verification.",
  },
  {
    scope: "helper_acting",
    icon: <Users className="w-5 h-5" />,
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
      <Card className="p-5 space-y-1.5">
        <h2 className="text-xl font-bold font-heading text-slate-900">میرا ڈیٹا کس کے پاس ہے؟ · Who Has My Data</h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          آپ کے ڈیٹا پر مکمل کنٹرول آپ کا ہے۔ آپ کسی بھی وقت کسی بھی ایجنسی یا مددگار کی رسائی منسوخ کر سکتے ہیں۔ منسوخی پر سرور فوری طور پر رسائی بلاک (HTTP 403) کرتا ہے۔
        </p>
      </Card>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-4 font-medium text-xs">
          {error}
        </div>
      )}

      {/* Immediate "Access Stopped" Banner */}
      {lastRevocation && (
        <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-base font-bold text-amber-950 font-heading">رسائی فوری طور پر روک دی گئی · Access Stopped</p>
              <p className="text-xs text-amber-800">
                Scope: <span className="font-mono font-bold uppercase">{lastRevocation.scope}</span> · Revoked at {new Date(lastRevocation.revoked_at || Date.now()).toLocaleTimeString()}
              </p>
            </div>
          </div>
          <p className="text-xs text-slate-700 leading-relaxed">
            سرور نے فوری طور پر اس ڈیٹا تک تمام بیرونی رسائی بلاک کر دی ہے۔ یہ منسوخی کرپٹوگرافک آڈٹ ہیش چین میں محفوظ ہو چکی ہے۔
          </p>
          {lastRevocation.audit_hash && (
            <div className="bg-white rounded-xl p-3 border border-amber-200 text-xs space-y-1 shadow-sm">
              <span className="font-bold text-[#0B4F43] block">کرپٹوگرافک آڈٹ ہیش:</span>
              <p className="font-mono text-[11px] text-slate-600 break-all">{lastRevocation.audit_hash}</p>
              <Link
                href="/auditor"
                className="inline-flex items-center gap-1 font-bold text-[#0B4F43] hover:underline pt-1 text-xs"
              >
                آڈٹ چین میں تصدیق دیکھیں · Verify in Audit Ledger <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}
        </div>
      )}

      {/* Grantee Cards */}
      <div className="space-y-4">
        {/* Government Rails */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-[#0B4F43] flex items-center justify-center shrink-0">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <p className="font-bold text-slate-900 text-sm sm:text-base">سرکاری ڈی پی آئی ریلز · Government DPI Rails</p>
              <p className="text-xs text-slate-500">NADRA, BISP, SBP Raast</p>
            </div>
          </div>

          <div className="grid gap-3">
            {SCOPES.slice(0, 3).map((s) => {
              const isOn = !!status?.active_scopes.includes(s.scope);

              return (
                <div key={s.scope} className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2.5">
                      <div className={`p-2 rounded-lg mt-0.5 shrink-0 ${isOn ? "bg-emerald-100 text-[#0B4F43]" : "bg-slate-200 text-slate-600"}`}>
                        {s.icon}
                      </div>
                      <div className="space-y-0.5">
                        <p className="font-bold text-xs sm:text-sm text-slate-900">{s.ur}</p>
                        <p className="text-xs text-slate-500 leading-normal">{s.descUr}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => speak(s.descUr, "ur-PK")}
                      type="button"
                      className="p-1.5 rounded-lg bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 shrink-0"
                      aria-label="Listen description"
                    >
                      <Volume2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="pt-1">
                    <BigToggle
                      checked={isOn}
                      onChange={() => toggle(s.scope, isOn)}
                      disabled={busy === s.scope || !status}
                      labelUr={isOn ? "رسائی فعال ہے (اجازت دی گئی ہے)" : "رسائی منسوخ ہے (بلاک شدہ)"}
                      labelEn={isOn ? "Active" : "Blocked"}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Field Helper */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-900 flex items-center justify-center shrink-0">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="font-bold text-slate-900 text-sm sm:text-base">مددگار ورکر · Field Helper</p>
              <p className="text-xs text-slate-500">فیلڈ میں آپ کی جانب سے درخواستیں جمع کرانے کے اختیارات</p>
            </div>
          </div>

          {(() => {
            const s = SCOPES[3]; // helper_acting
            const isOn = !!status?.active_scopes.includes(s.scope);
            return (
              <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 space-y-2">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <div className={`p-2 rounded-lg mt-0.5 shrink-0 ${isOn ? "bg-emerald-100 text-[#0B4F43]" : "bg-slate-200 text-slate-600"}`}>
                      {s.icon}
                    </div>
                    <div className="space-y-0.5">
                      <p className="font-bold text-xs sm:text-sm text-slate-900">{s.ur}</p>
                      <p className="text-xs text-slate-500 leading-normal">{s.descUr}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => speak(s.descUr, "ur-PK")}
                    type="button"
                    className="p-1.5 rounded-lg bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 shrink-0"
                    aria-label="Listen description"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="pt-1">
                  <BigToggle
                    checked={isOn}
                    onChange={() => toggle(s.scope, isOn)}
                    disabled={busy === s.scope || !status}
                    labelUr={isOn ? "مددگار مجاز ہے" : "اختیار منسوخ ہے"}
                    labelEn={isOn ? "Authorized" : "Revoked"}
                  />
                </div>
              </div>
            );
          })()}
        </Card>
      </div>

      {/* Live 403 Access Probe */}
      <Card className="p-5 space-y-3 border-sky-300 bg-sky-50/40">
        <div className="flex items-center justify-between">
          <p className="font-bold text-sm text-sky-950">رسائی کی لائیو جانچ · Live Access Control Test</p>
          <span className="text-[11px] font-bold bg-sky-100 text-sky-800 px-2 py-0.5 rounded">Proof of 403</span>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          اوپر سے رضامندی منسوخ کرنے کے بعد بٹن دبائیں۔ اگر رضامندی واپس لی گئی ہے تو سرور کیس ڈیٹا دینے سے انکار کر کے <b>HTTP 403 Forbidden</b> دے گا۔
        </p>
        <Button
          variant="secondary"
          onClick={checkAccess}
          disabled={probing || !citizenId}
          className="w-full bg-sky-700 hover:bg-sky-800"
        >
          {probing ? "سرور سے چیک ہو رہا ہے..." : "Try reading citizen's case as a third party"}
        </Button>

        {probe?.kind === "blocked" && (
          <div className="rounded-xl bg-rose-50 border border-rose-200 text-rose-900 p-4 flex gap-3 text-xs">
            <ShieldX className="w-6 h-6 shrink-0 text-rose-600 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-bold">HTTP {probe.err.status} — ACCESS BLOCKED</p>
              <p className="font-medium">{probe.err.message_ur ?? "رضامندی کے بغیر رسائی بلاک کر دی گئی ہے"}</p>
              <p className="text-slate-500 font-sans">{probe.err.message_en}</p>
            </div>
          </div>
        )}

        {probe?.kind === "allowed" && (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-950 p-3.5 flex gap-2.5 items-center text-xs">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <p>کیونکہ متعلقہ اسکوپ فعال ہے، کیس <span className="font-mono font-bold">{probe.caseId.slice(0, 8)}</span> کامیابی سے پڑھ لیا گیا۔</p>
          </div>
        )}

        {probe?.kind === "none" && (
          <p className="bg-amber-50 text-amber-900 rounded-xl p-3 text-xs border border-amber-200">
            اس شہری کے نام پر ابھی کوئی کیس موجود نہیں ہے۔ پہلے <Link href="/apply" className="underline font-bold">درخواست</Link> میں کیس بنائیں۔
          </p>
        )}
      </Card>
    </AppShell>
  );
}
