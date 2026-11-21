"use client";

import { useCallback, useEffect, useState } from "react";
import { UserCheck, Wallet, Receipt, Users, Volume2 } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type ConsentScope, type ConsentStatus } from "@/lib/api";
import { getActiveCitizenId, speak } from "@/lib/session";

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

export default function ConsentPage() {
  const [citizenId, setCitizenId] = useState("");
  const [status, setStatus] = useState<ConsentStatus | null>(null);
  const [busy, setBusy] = useState<string>("");
  const [error, setError] = useState("");

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
    if (id) load(id);
  }, [load]);

  async function toggle(scope: ConsentScope, isOn: boolean) {
    setBusy(scope);
    setError("");
    try {
      if (isOn) await api.withdrawConsent(citizenId, scope);
      else await api.grantConsent(citizenId, scope);
      await load(citizenId);
    } catch (e) {
      const err = e as ApiError;
      setError(err.message_ur ?? err.message_en ?? "Error");
    } finally {
      setBusy("");
    }
  }

  return (
    <AppShell title="میرا ڈیٹا · My Data & Consent">
      {error && <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">{error}</p>}

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
        <p className="text-sm text-emerald-800">
          Every change is written to the tamper-proof audit log.
        </p>
      </div>
    </AppShell>
  );
}