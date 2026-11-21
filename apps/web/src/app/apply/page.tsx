"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  User, CreditCard, Phone, Users, Wallet, Camera, Mic, Volume2, Send, CheckCircle2, AlertTriangle, HelpCircle,
} from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type CaseCreate, type Decision } from "@/lib/api";
import { getActiveCitizenId, getActiveCitizenName, getSession, speak } from "@/lib/session";
import { queueCase } from "@/lib/offlineQueue";

type Field = "citizen_name" | "cnic" | "phone" | "household_size" | "monthly_income";
const STEPS: {
  key: Field; icon: React.ReactNode; ur: string; en: string; type: "text" | "tel"; hint: string; ok: (v: string) => boolean;
}[] = [
  { key: "citizen_name", icon: <User className="w-16 h-16" />, ur: "آپ کا پورا نام کیا ہے؟", en: "What is your full name?", type: "text", hint: "Parveen Bibi", ok: (v) => v.trim().length >= 3 },
  { key: "cnic", icon: <CreditCard className="w-16 h-16" />, ur: "آپ کے شناختی کارڈ کا نمبر بتائیں", en: "Your CNIC number", type: "tel", hint: "42101-1234567-1", ok: (v) => /^\d{5}-?\d{7}-?\d$/.test(v) },
  { key: "phone", icon: <Phone className="w-16 h-16" />, ur: "آپ کا موبائل نمبر کیا ہے؟", en: "Your mobile number", type: "tel", hint: "0300-1112223", ok: (v) => /^03\d{2}-?\d{7}$/.test(v) },
  { key: "household_size", icon: <Users className="w-16 h-16" />, ur: "گھر میں کتنے لوگ ہیں؟", en: "How many people live in your home?", type: "tel", hint: "5", ok: (v) => Number(v) >= 1 },
  { key: "monthly_income", icon: <Wallet className="w-16 h-16" />, ur: "گھر کی ماہانہ آمدنی کتنی ہے؟ (روپے)", en: "Monthly household income (PKR)", type: "tel", hint: "18000", ok: (v) => v !== "" && Number(v) >= 0 },
];
const TOTAL = STEPS.length + 2; // + bill photo + review

interface Recognition {
  lang: string; start(): void; onend: (() => void) | null; onerror: (() => void) | null;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
}

function listen(onText: (t: string) => void, onEnd: () => void): boolean {
  const w = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  if (!Ctor) return false;
  const r = new Ctor();
  r.lang = "ur-PK";
  r.onresult = (e) => onText(e.results[0][0].transcript);
  r.onend = onEnd;
  r.onerror = onEnd;
  r.start();
  return true;
}

export default function ApplyPage() {
  const [step, setStep] = useState(0);
  const [values, setValues] = useState<Record<string, string>>({});
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState("");
  const [needFamily, setNeedFamily] = useState(false);
  const [offlineSaved, setOfflineSaved] = useState(false);
  const [result, setResult] = useState<Decision | null>(null);

  useEffect(() => {
    const s = getSession();
    if (s?.role === "helper" && !getActiveCitizenName()) setNeedFamily(true);
  }, []);

  const cur = step < STEPS.length ? STEPS[step] : null;
  const value = cur ? values[cur.key] ?? "" : "";

  function say() {
    if (cur) speak(cur.ur, "ur-PK");
    else if (step === STEPS.length) speak("اپنے بجلی کے بل کی تصویر لیں", "ur-PK");
    else speak("کیا آپ درخواست بھیجنا چاہتے ہیں؟", "ur-PK");
  }

  function voice() {
    if (!cur) return;
    setListening(true);
    const ok = listen(
      (t) => setValues((v) => ({ ...v, [cur.key]: cur.type === "tel" ? t.replace(/[^\d-]/g, "") : t })),
      () => setListening(false)
    );
    if (!ok) { setListening(false); setError("Voice input is not supported in this browser. Please type."); }
  }

  async function submit() {
    setBusy(true);
    setError("");
    const payload: CaseCreate = {
      citizen_name: values.citizen_name, cnic: values.cnic, phone: values.phone,
      household_size: Number(values.household_size), monthly_income: Number(values.monthly_income),
      benefit_type: "relief_cash_grant",
    };
    try {
      if (!navigator.onLine) {
        await queueCase({ ...payload, citizen_id: getActiveCitizenId() });
        setOfflineSaved(true);
        return;
      }
      const created = await api.createCase(payload);
      if (file) await api.uploadDocument(created.id, file);
      await api.submitCase(created.id);
      setResult(await api.evaluateCase(created.id));
    } catch (e) {
      const err = e as ApiError;
      setError(err.message_ur ?? err.message_en ?? "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  if (needFamily) {
    return (
      <AppShell title="درخواست · Application">
        <div className="bg-amber-100 rounded-3xl p-6 space-y-3">
          <p className="text-xl font-bold">پہلے خاندان منتخب کریں · Choose a family first</p>
          <Link href="/families" className="block h-14 leading-[3.5rem] text-center rounded-2xl bg-emerald-600 text-white font-bold">
            خاندان کھولیں · Open families
          </Link>
        </div>
      </AppShell>
    );
  }

  if (offlineSaved) {
    return (
      <AppShell title="درخواست · Application">
        <div className="bg-sky-100 text-sky-900 rounded-3xl p-6 space-y-2">
          <p className="text-2xl font-bold">فارم فون میں محفوظ ہو گیا</p>
          <p>Saved on this phone. It will be sent automatically when the internet is back.</p>
        </div>
      </AppShell>
    );
  }

  if (result) {
    const look =
      result.route === "auto_approve"
        ? { bg: "bg-emerald-100 text-emerald-900", icon: <CheckCircle2 className="w-14 h-14" />, ur: "منظور", en: "Approved" }
        : result.route === "ask_more_proof"
        ? { bg: "bg-amber-100 text-amber-900", icon: <AlertTriangle className="w-14 h-14" />, ur: "مزید ثبوت چاہیے", en: "More proof needed" }
        : { bg: "bg-sky-100 text-sky-900", icon: <HelpCircle className="w-14 h-14" />, ur: "افسر جانچ کرے گا", en: "An officer will review" };
    return (
      <AppShell title="نتیجہ · Result">
        <div className={`rounded-3xl p-6 space-y-3 ${look.bg}`}>
          <div className="flex items-center gap-4">
            {look.icon}
            <div className="flex-1">
              <p className="text-3xl font-bold">{look.ur}</p>
              <p>{look.en}</p>
            </div>
            <button onClick={() => speak(result.reason_simple.ur)} className="h-12 w-12 rounded-2xl bg-white/60 flex items-center justify-center" aria-label="Play audio">
              <Volume2 className="w-6 h-6" />
            </button>
          </div>
          <p className="text-xl">{result.reason_simple.ur}</p>
          <p>{result.reason_simple.en}</p>
          {result.missing.length > 0 && (
            <ul className="list-disc ps-6">{result.missing.map((m) => <li key={m}>{m}</li>)}</ul>
          )}
          <p className="text-sm">Confidence {Math.round(result.confidence * 100)}% · Rule version v{result.rule_version}</p>
        </div>
        <Link href="/cases" className="block h-14 leading-[3.5rem] text-center rounded-2xl bg-emerald-600 text-white text-lg font-bold">
          میرے کیس دیکھیں · View my cases
        </Link>
      </AppShell>
    );
  }

  return (
    <AppShell title="نئی درخواست · New Application">
      <div className="h-3 bg-white rounded-full overflow-hidden">
        <div className="h-full bg-emerald-500 transition-all" style={{ width: `${((step + 1) / TOTAL) * 100}%` }} />
      </div>
      <p className="text-center text-gray-500">{step + 1} / {TOTAL}</p>

      <div className="bg-white rounded-3xl shadow p-6 space-y-5 text-center">
        <div className="text-emerald-600 flex justify-center">
          {cur ? cur.icon : step === STEPS.length ? <Camera className="w-16 h-16" /> : <Send className="w-16 h-16" />}
        </div>
        <div>
          <p className="text-2xl font-bold">
            {cur ? cur.ur : step === STEPS.length ? "بجلی کے بل کی تصویر لیں" : "درخواست بھیجیں؟"}
          </p>
          <p className="text-gray-500">
            {cur ? cur.en : step === STEPS.length ? "Take a photo of your electricity bill (optional)" : "Check your answers and send"}
          </p>
        </div>

        <button onClick={say} className="h-14 px-6 rounded-2xl bg-emerald-100 text-emerald-800 font-bold inline-flex items-center gap-2">
          <Volume2 className="w-6 h-6" /> سنیں · Listen
        </button>

        {cur && (
          <div className="space-y-3">
            <input
              className="w-full h-16 border-2 rounded-2xl px-4 text-2xl text-center"
              type={cur.type}
              inputMode={cur.type === "tel" ? "numeric" : "text"}
              placeholder={cur.hint}
              value={value}
              onChange={(e) => setValues({ ...values, [cur.key]: e.target.value })}
            />
            <button onClick={voice} disabled={listening} className="w-full h-14 rounded-2xl bg-emerald-600 text-white font-bold inline-flex items-center justify-center gap-2 disabled:opacity-60">
              <Mic className="w-6 h-6" /> {listening ? "سن رہا ہوں..." : "بول کر بتائیں · Speak"}
            </button>
          </div>
        )}

        {step === STEPS.length && (
          <label className="block h-16 leading-[4rem] rounded-2xl border-2 border-dashed border-emerald-400 text-emerald-700 font-bold cursor-pointer">
            {file ? `✓ ${file.name}` : "تصویر منتخب کریں · Choose photo"}
            <input type="file" accept="image/*" capture="environment" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </label>
        )}

        {step === TOTAL - 1 && (
          <div className="text-start bg-emerald-50 rounded-2xl p-4 space-y-1">
            <p>👤 {values.citizen_name}</p>
            <p>🪪 {values.cnic}</p>
            <p>📞 {values.phone}</p>
            <p>👨‍👩‍👧 {values.household_size}</p>
            <p>💰 Rs {values.monthly_income}</p>
            <p>📷 {file ? file.name : "—"}</p>
          </div>
        )}

        {error && <p className="text-red-600 font-bold">{error}</p>}

        <div className="grid grid-cols-2 gap-3">
          <button onClick={() => { setError(""); setStep(step - 1); }} disabled={step === 0 || busy} className="h-14 rounded-2xl bg-gray-200 font-bold disabled:opacity-40">
            واپس · Back
          </button>
          {step < TOTAL - 1 ? (
            <button
              onClick={() => { setError(""); setStep(step + 1); }}
              disabled={cur ? !cur.ok(value) : false}
              className="h-14 rounded-2xl bg-emerald-600 text-white font-bold disabled:opacity-40"
            >
              آگے · Next
            </button>
          ) : (
            <button onClick={submit} disabled={busy} className="h-14 rounded-2xl bg-emerald-700 text-white font-bold disabled:opacity-60">
              {busy ? "..." : "بھیجیں · Submit"}
            </button>
          )}
        </div>
      </div>
    </AppShell>
  );
}