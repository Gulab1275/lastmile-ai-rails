"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { UserCheck, Wallet, Receipt, Users, Volume2, ShieldX, ShieldCheck } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type ConsentScope, type ConsentStatus } from "@/lib/api";
import { getActiveCitizenId, getSession, speak } from "@/lib/session";

const SCOPES: {
  scope: ConsentScope; icon: React.ReactNode;
  ur: string; en: string; descUr: string; descEn: string;
}[] = [
  { scope: "identity", icon: <UserCheck className="w-10 h-10" />, ur: "شناخت شیئر کریں", en: "Share my identity",
    descUr: "آپ کا نام اور شناختی کارڈ نمبر تصدیق کے لیے دیکھا جائے گا۔", descEn: "Your name and CNIC are checked for verification." },
  { scope: "income", icon: <Wallet className="w-10 h-10" />, ur: "آمدنی شیئر کریں", en: "Share my income",
    descUr: "آپ کی ماہانہ آمدنی اہلیت جانچنے کے لیے استعمال ہوگی۔", descEn: "Your monthly income is used to check eligibility." },
  { scope: "bills", icon: <Receipt className="w-10 h-10" />, ur: "بل شیئر کریں", en: "Share my bills",
    descUr: "بجلی کا بل پتے کی تصدیق کے لیے دیکھا جائے گا۔", descEn: "Your electricity bill confirms your address." },
  { scope: "helper_acting", icon: <Users className="w-10 h-10" />, ur: "مددگار میری طرف سے کام کرے", en: "Helper may act for me",
    descUr: "آپ کا مددگار آپ کی جگہ فارم بھر سکتا ہے۔", descEn: "Your helper can fill forms on your behalf." },
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
  const [withdrew, setWithdrew] = useState(false);
  const [probe, setProbe] = useState<Probe | null>(null);
  const [probing, setProbing] = useState(false);

  const load = useCallback(async (id: string) => {
    try {
      setStatus(await api.getConsentStatus(id));
    } catch (e) {
      const err = e as ApiError;
      setError(err.message_ur ?? err.message_en ?? "Error");
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
      if (isOn) await api.withdrawConsent(citizenId, scope);
      else await api.grantConsent(citizenId, scope);
      setWithdrew(isOn);
      await load(citizenId);
    } catch (e) {
      const err = e as ApiError;
      setError(err.message_ur ?? err.message_en ?? "Error");
    } finally {
      setBusy("");
    }
  }

  // Challenge 06: try to read this family's case the way a helper would.
  async function checkAccess() {
    setProbing(true);
    setProbe(null);
    try {
      const mine = (await api.listCases()).filter((c) => c.citizen_id === citizenId);
      if (mine.length === 0) { setProbe({ kind: "none" }); return; }
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
    <AppShell title="میرا ڈیٹا · My Data & Consent">
      {error && <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">{error}</p>}

      {withdrew && (
        <p className="bg-amber-100 text-amber-900 rounded-2xl p-3 font-bold">
          اجازت واپس لے لی گئی۔ اب مددگار یہ ڈیٹا نہیں دیکھ سکتا۔ · Consent withdrawn. From now on anyone reading this data is blocked instantly (HTTP 403).
        </p>
      )}

      <div className="grid gap-4">
        {SCOPES.map((s) => {
          const isOn = !!status?.active_scopes.includes(s.scope);
          const record = status?.all_consents.find((c) => c.scope === s.scope);
          return (
            <div key={s.scope} className="bg-white rounded-3xl shadow p-5 space-y-3">
              <div className="flex items-center gap-4">
                <div className={isOn ? "text-emerald-600" : "text-gray-400"}>{s.icon}</div>
                <div className="flex-1">
                  <p className="text-xl font-bold">{s.ur}</p>
                  <p className="text-gray-500">{s.en}</p>
                </div>
                <button
                  onClick={() => speak(s.descUr, "ur-PK")}
                  className="h-12 w-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center"
                  aria-label="Play audio"
                >
                  <Volume2 className="w-6 h-6" />
                </button>
              </div>
              <p className="text-gray-600">{s.descUr}</p>
              <p className="text-gray-400 text-sm">{s.descEn}</p>

              <button
                onClick={() => toggle(s.scope, isOn)}
                disabled={busy === s.scope || !status}
                className={`w-full h-14 rounded-2xl text-lg font-bold text-white disabled:opacity-50 ${
                  isOn ? "bg-red-600" : "bg-emerald-600"
                }`}
              >
                {busy === s.scope ? "..." : isOn ? "واپس لیں · Withdraw" : "اجازت دیں · Allow"}
              </button>

              {record && (
                <p className="text-xs text-gray-400">
                  {isOn
                    ? `Granted ${new Date(record.granted_at).toLocaleString()}`
                    : record.revoked_at
                    ? `Withdrawn ${new Date(record.revoked_at).toLocaleString()}`
                    : ""}
                </p>
              )}
            </div>
          );
        })}
      </div>

      <div className="bg-emerald-100 rounded-3xl p-5">
        <p className="font-bold text-emerald-900">
          اس وقت فعال · Currently shared: {status?.active_scopes.length ?? 0}
        </p>
        <p className="text-sm text-emerald-800">Every change is written to the tamper-proof audit log.</p>
      </div>

      {/* ---- Challenge 06: proof that withdrawn consent really blocks access ---- */}
      <div className="bg-white rounded-3xl shadow p-5 space-y-3 border-2 border-sky-300">
        <p className="text-xl font-bold">رسائی کی جانچ · Access check</p>
        {role === "helper" ? (
          <>
            <p className="text-gray-600">
              Withdraw “Share my identity” above, then press the button. The server must refuse to show this family’s case.
            </p>
            <button onClick={checkAccess} disabled={probing || !citizenId} className="w-full h-14 rounded-2xl bg-sky-600 text-white text-lg font-bold disabled:opacity-40">
              {probing ? "..." : "Try to read this family’s case"}
            </button>
            {probe?.kind === "blocked" && (
              <div className="rounded-2xl bg-red-100 text-red-900 p-4 flex gap-3">
                <ShieldX className="w-12 h-12 shrink-0" />
                <div className="space-y-1">
                  <p className="text-2xl font-bold">HTTP {probe.err.status} — ACCESS BLOCKED</p>
                  {probe.err.code && <p className="font-mono text-sm">{probe.err.code}</p>}
                  {probe.err.message_ur && <p className="text-lg">{probe.err.message_ur}</p>}
                  <p>{probe.err.message_en}</p>
                  <p className="text-sm">The blocked attempt is recorded in the audit log.</p>
                </div>
              </div>
            )}
            {probe?.kind === "allowed" && (
              <div className="rounded-2xl bg-emerald-100 text-emerald-900 p-4 flex gap-3 items-center">
                <ShieldCheck className="w-12 h-12 shrink-0" />
                <p className="font-bold">Allowed — consent is active, so case {probe.caseId} can be read.</p>
              </div>
            )}
            {probe?.kind === "none" && <p className="bg-amber-100 rounded-2xl p-3">This family has no case yet. Create one in <Link href="/apply" className="underline font-bold">Apply</Link> first.</p>}
            {probe?.kind === "error" && <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">{probe.err.message_en ?? "Could not run the check"}</p>}
          </>
        ) : (
          <p className="text-gray-600">
            After you withdraw consent, your helper is blocked instantly. To see it: log in as <b>helper_shazia</b>, open Families → Parveen Bibi → Consent, and press “Try to read this family’s case”. The server answers <b>HTTP 403</b>.
          </p>
        )}
      </div>
    </AppShell>
  );
}