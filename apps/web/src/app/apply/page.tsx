"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  User, CreditCard, Phone, Users, Wallet, Camera, Mic, Volume2, Send, CheckCircle2,
  AlertTriangle, HelpCircle, FileText, ArrowRight, ArrowLeft, ShieldCheck, RefreshCw,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { StepStones } from "@/components/ui/StepStones";
import { ConfidenceRing } from "@/components/ui/ConfidenceRing";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import api, { type ApiError, type CaseCreate, type Decision } from "@/lib/api";
import { getActiveCitizenId, getActiveCitizenName, getSession, speak } from "@/lib/session";
import { queueCase } from "@/lib/offlineQueue";

type Field = "citizen_name" | "cnic" | "phone" | "household_size" | "monthly_income";
const STEPS: {
  key: Field; icon: React.ReactNode; ur: string; en: string; type: "text" | "tel"; hint: string; ok: (v: string) => boolean;
}[] = [
  { key: "citizen_name", icon: <User className="w-8 h-8" />, ur: "آپ کا پورا نام کیا ہے؟", en: "What is your full name?", type: "text", hint: "Parveen Bibi", ok: (v) => v.trim().length >= 3 },
  { key: "cnic", icon: <CreditCard className="w-8 h-8" />, ur: "شناختی کارڈ نمبر بتائیں", en: "Your CNIC number", type: "tel", hint: "42101-1234567-1", ok: (v) => /^\d{5}-?\d{7}-?\d$/.test(v) },
  { key: "phone", icon: <Phone className="w-8 h-8" />, ur: "آپ کا موبائل فون نمبر کیا ہے؟", en: "Your mobile phone number", type: "tel", hint: "0300-1112223", ok: (v) => /^03\d{2}-?\d{7}$/.test(v) },
  { key: "household_size", icon: <Users className="w-8 h-8" />, ur: "گھر میں کل کتنے افراد رہتے ہیں؟", en: "How many people in your household?", type: "tel", hint: "5", ok: (v) => Number(v) >= 1 },
  { key: "monthly_income", icon: <Wallet className="w-8 h-8" />, ur: "گھر کی کل ماہانہ آمدنی کتنی ہے؟ (روپے)", en: "Total monthly household income (PKR)", type: "tel", hint: "18000", ok: (v) => v !== "" && Number(v) >= 0 },
];

const TOTAL_STEPS = STEPS.length + 2; // + utility bill + final review

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

  // Stepping stones milestone calculation (0 to 4)
  const currentMilestone = result
    ? result.route === "auto_approve" ? 4 : 3
    : step < 3 ? 0 : step < 5 ? 1 : 2;

  function say() {
    if (cur) speak(cur.ur, "ur-PK");
    else if (step === STEPS.length) speak("اپنے بجلی کے بل کی تصویر لیں یا اپ لوڈ کریں", "ur-PK");
    else speak("کیا آپ اپنی یہ معلومات بھیجنا چاہتے ہیں؟", "ur-PK");
  }

  function voice() {
    if (!cur) return;
    setListening(true);
    const ok = listen(
      (t) => setValues((v) => ({ ...v, [cur.key]: cur.type === "tel" ? t.replace(/[^\d-]/g, "") : t })),
      () => setListening(false)
    );
    if (!ok) {
      setListening(false);
      speak("آواز کی سہولت دستیاب نہیں ہے، برائے مہربانی لکھیں", "ur-PK");
      setError("Voice input not supported in this browser. Please type or use keyboard.");
    }
  }

  async function submit() {
    setBusy(true);
    setError("");
    const payload: CaseCreate = {
      citizen_name: values.citizen_name,
      cnic: values.cnic,
      phone: values.phone,
      household_size: Number(values.household_size),
      monthly_income: Number(values.monthly_income),
      benefit_type: "relief_cash_grant",
    };
    try {
      if (!navigator.onLine) {
        await queueCase({ ...payload, citizen_id: getActiveCitizenId() });
        setOfflineSaved(true);
        speak("درخواست فون میں محفوظ ہو گئی۔ انٹرنیٹ آنے پر خودکار چلی جائے گی۔", "ur-PK");
        return;
      }
      const created = await api.createCase(payload);
      if (file) await api.uploadDocument(created.id, file);
      await api.submitCase(created.id);
      const evalRes = await api.evaluateCase(created.id);
      setResult(evalRes);
      speak(evalRes.reason_simple.ur, "ur-PK");
    } catch (e) {
      const err = e as ApiError;
      setError(err.message_ur ?? err.message_en ?? "Something went wrong while submitting");
    } finally {
      setBusy(false);
    }
  }

  if (needFamily) {
    return (
      <AppShell title="درخواست · Relief Application">
        <Card className="p-6 space-y-4 text-center border-amber-200 bg-amber-50/50">
          <p className="text-lg font-bold text-amber-900">پہلے خاندان منتخب کریں · Choose a family first</p>
          <p className="text-sm text-amber-800">مددگار موڈ میں درخواست شروع کرنے سے پہلے خاندان کا چناؤ لازمی ہے۔</p>
          <Link href="/families" className="inline-block pt-1">
            <Button variant="secondary">خاندان کھولیں · Open families directory</Button>
          </Link>
        </Card>
      </AppShell>
    );
  }

  if (offlineSaved) {
    return (
      <AppShell title="درخواست محفوظ ہو گئی · Application Saved">
        <Card className="p-6 space-y-4 text-center border-sky-200 bg-sky-50/50">
          <div className="w-14 h-14 rounded-2xl bg-sky-100 text-sky-700 flex items-center justify-center mx-auto">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <p className="text-xl font-bold text-sky-950">فارم فون میں محفوظ ہو گیا ہے</p>
            <p className="text-sm text-sky-800">
              Saved locally on this phone. It will be sent automatically when network signal returns.
            </p>
          </div>
          <p className="text-xs font-mono bg-white px-3 py-1.5 rounded-lg border border-sky-200 inline-block text-sky-900">
            Idempotency key active · No duplicate claims
          </p>
          <div className="pt-2">
            <Link href="/dashboard">
              <Button variant="secondary">ہوم پر جائیں · Back to Home</Button>
            </Link>
          </div>
        </Card>
      </AppShell>
    );
  }

  // ==================== DECISION SCREEN (3 DISTINCT POLISHED LAYOUTS) ====================
  if (result) {
    if (result.route === "auto_approve") {
      return (
        <AppShell title="درخواست کی منظوری · Application Approved">
          <StepStones currentStep={4} />
          <div className="bg-emerald-50 border border-emerald-300 rounded-2xl p-6 space-y-5 text-center shadow-sm mt-4">
            <div className="flex items-center justify-between">
              <span className="px-3 py-1 bg-emerald-600 text-white text-xs font-bold rounded-full">
                خودکار منظوری · Auto-Approved
              </span>
              <ConfidenceRing confidence={result.confidence} color="#059669" label="اعتماد" />
            </div>

            <div className="space-y-2">
              <div className="w-14 h-14 rounded-2xl bg-emerald-100 flex items-center justify-center mx-auto text-emerald-700">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h2 className="text-2xl font-bold text-emerald-950 font-heading">
                مبارک ہو! آپ کی درخواست منظور ہو گئی
              </h2>
              <p className="text-base text-emerald-900 font-medium">{result.reason_simple.ur}</p>
              <p className="text-xs text-emerald-700 font-sans">{result.reason_simple.en}</p>
            </div>

            <div className="bg-white rounded-xl p-4 border border-emerald-200 text-start space-y-1 shadow-sm">
              <p className="text-xs font-bold text-emerald-800 uppercase tracking-wide">ادائیگی کی تفصیل · Payment Rail</p>
              <p className="font-bold text-slate-900 text-sm">SBP Raast Fast Payment Rail</p>
              <p className="text-xs text-slate-600">
                کرپٹوگرافک منظوری ٹوکن جاری کر دیا گیا ہے۔ رقم براہ راست آپ کے اکاؤنٹ میں منتقل ہوگی۔
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Button
                variant="outline"
                onClick={() => speak(result.reason_simple.ur, "ur-PK")}
                className="flex-1"
              >
                <Volume2 className="w-4 h-4 text-[#0B4F43]" /> سنیں · Listen
              </Button>
              <Link href="/cases" className="flex-1">
                <Button variant="secondary" className="w-full">
                  میرے کیس · View Cases
                </Button>
              </Link>
            </div>
          </div>
        </AppShell>
      );
    }

    if (result.route === "ask_more_proof") {
      const missingDoc = result.missing[0] || "utility_bill";
      return (
        <AppShell title="مزید ثبوت درکار ہے · More Proof Needed">
          <StepStones currentStep={3} />
          <div className="bg-amber-50 border border-amber-300 rounded-2xl p-6 space-y-5 text-center shadow-sm mt-4">
            <div className="flex items-center justify-between">
              <span className="px-3 py-1 bg-amber-600 text-white text-xs font-bold rounded-full">
                اضافی دستاویز · Need One More Document
              </span>
              <ConfidenceRing confidence={result.confidence} color="#D97706" label="اعتماد" />
            </div>

            <div className="space-y-2">
              <div className="w-14 h-14 rounded-2xl bg-amber-100 flex items-center justify-center mx-auto text-amber-700">
                <AlertTriangle className="w-8 h-8" />
              </div>
              <h2 className="text-2xl font-bold text-amber-950 font-heading">
                ایک اضافی کاغذ کی ضرورت ہے
              </h2>
              <p className="text-base text-amber-900 font-bold">{result.reason_simple.ur}</p>
              <p className="text-xs text-amber-800 font-sans">{result.reason_simple.en}</p>
            </div>

            <div className="bg-white rounded-xl p-4 border border-amber-200 text-start space-y-2 shadow-sm">
              <p className="text-xs font-bold text-amber-800 uppercase tracking-wide">مطلوبہ کاغذ · Required Document</p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-bold text-slate-900 text-sm">
                    {missingDoc.includes("bill") ? "بجلی کا واضح بل (Utility Bill)" : "شناختی کارڈ کی واضح کاپی (Clear CNIC)"}
                  </p>
                  <p className="text-xs text-slate-500">دھندلاہٹ یا نامکمل فیلڈ کی وجہ سے خودکار سسٹم نے تصدیق روکی ہے۔</p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Link href="/documents" className="flex-1">
                <Button variant="primary" className="w-full">
                  <Camera className="w-4 h-4 me-1" /> کاغذ اپ لوڈ کریں · Upload
                </Button>
              </Link>
              <Link href="/cases" className="flex-1">
                <Button variant="neutral" className="w-full">
                  کیس دیکھیں · View Case
                </Button>
              </Link>
            </div>
          </div>
        </AppShell>
      );
    }

    // Route: human_review (Calm, reassuring indigo #4F46E5 — NEVER RED)
    return (
      <AppShell title="افسر کا جائزہ · Human Officer Review">
        <StepStones currentStep={3} />
        <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-6 space-y-5 text-center shadow-sm mt-4">
          <div className="flex items-center justify-between">
            <span className="px-3 py-1 bg-indigo-600 text-white text-xs font-bold rounded-full">
              انسانی جائزہ · Human Review Required
            </span>
            <ConfidenceRing confidence={result.confidence} color="#4F46E5" label="اعتماد" />
          </div>

          <div className="space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-indigo-100 flex items-center justify-center mx-auto text-indigo-700">
              <HelpCircle className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold text-indigo-950 font-heading">
              پریشان نہ ہوں — افسر جائزہ لے رہا ہے
            </h2>
            <p className="text-base text-indigo-900 font-bold">{result.reason_simple.ur}</p>
            <p className="text-xs text-indigo-700 font-sans">{result.reason_simple.en}</p>
          </div>

          <div className="bg-white rounded-xl p-4 border border-indigo-200 text-start space-y-1 shadow-sm">
            <p className="text-xs font-bold text-indigo-800 uppercase tracking-wide">پالیسی گارنٹی · Zero Auto-Reject Guarantee</p>
            <p className="text-xs text-slate-700 leading-relaxed">
              ہماری پالیسی کے تحت کمپیوٹر کبھی بھی کسی درخواست کو خود بخود مسترد نہیں کرتا۔ آپ کا کیس ریلیف افسر کو تفصیلی نوٹس کے ساتھ بھیج دیا گیا ہے۔
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => speak(result.reason_simple.ur, "ur-PK")}
              className="flex-1"
            >
              <Volume2 className="w-4 h-4 text-indigo-700" /> سنیں · Listen
            </Button>
            <Link href="/cases" className="flex-1">
              <Button variant="secondary" className="w-full bg-indigo-600 hover:bg-indigo-700">
                کیس ٹریک کریں · Track Case
              </Button>
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

  // ==================== WIZARD QUESTION STEPS ====================
  return (
    <AppShell title="نئی ریلیف درخواست · Relief Application">
      <StepStones currentStep={currentMilestone} />

      <Card className="p-6 sm:p-8 space-y-6 text-center mt-4">
        {/* Step Icon */}
        <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-[#0B4F43] border border-emerald-100 flex items-center justify-center mx-auto">
          {cur ? cur.icon : step === STEPS.length ? <Camera className="w-7 h-7 text-[#0B4F43]" /> : <Send className="w-7 h-7 text-[#D97706]" />}
        </div>

        {/* Step Prompts */}
        <div className="space-y-1">
          <h2 className="text-2xl font-bold font-heading text-slate-900">
            {cur ? cur.ur : step === STEPS.length ? "بجلی کے بل کی تصویر لیں" : "کیا آپ معلومات بھیجنا چاہتے ہیں؟"}
          </h2>
          <p className="text-sm text-slate-500 font-sans">
            {cur ? cur.en : step === STEPS.length ? "Take a photo of your electricity bill (optional proof)" : "Review your answers and submit"}
          </p>
        </div>

        {/* Audio Listen Button */}
        <div>
          <button
            onClick={say}
            type="button"
            className="px-4 py-2 rounded-xl bg-slate-100 text-[#0B4F43] hover:bg-slate-200 text-xs font-semibold inline-flex items-center gap-2 transition"
          >
            <Volume2 className="w-4 h-4" /> سوال سنیں · Listen in Urdu
          </button>
        </div>

        {/* Input & Mic Button */}
        {cur && (
          <div className="space-y-4 max-w-md mx-auto pt-2">
            <input
              className="w-full min-h-[52px] border-2 border-slate-300 rounded-xl px-4 text-xl text-center bg-white text-slate-900 font-bold focus:border-[#0B4F43] focus:ring-1 focus:ring-[#0B4F43] focus:outline-none"
              type={cur.type}
              inputMode={cur.type === "tel" ? "numeric" : "text"}
              placeholder={cur.hint}
              value={value}
              onChange={(e) => setValues({ ...values, [cur.key]: e.target.value })}
            />

            {/* Voice Mic Button */}
            <button
              onClick={voice}
              disabled={listening}
              type="button"
              className={`w-full min-h-[48px] rounded-xl font-bold text-sm inline-flex items-center justify-center gap-2 transition shadow-sm ${
                listening
                  ? "bg-rose-600 text-white animate-pulse"
                  : "bg-[#0B4F43] text-white hover:bg-[#084137]"
              }`}
            >
              <Mic className="w-5 h-5" />
              {listening ? "سن رہا ہوں..." : "بول کر بتائیں · Speak in Urdu"}
            </button>
          </div>
        )}

        {/* Photo Upload Step */}
        {step === STEPS.length && (
          <div className="max-w-md mx-auto space-y-3">
            <label className="min-h-[100px] rounded-2xl border-2 border-dashed border-[#0B4F43]/40 bg-slate-50 hover:bg-emerald-50/40 text-[#0B4F43] font-bold flex flex-col items-center justify-center cursor-pointer transition p-4">
              <Camera className="w-7 h-7 mb-1 text-[#0B4F43]" />
              <span className="text-sm">{file ? `✓ ${file.name}` : "تصویر منتخب کریں · Choose / Snap photo"}</span>
              <span className="text-xs text-slate-500 font-normal mt-0.5">JPG or PNG</span>
              <input
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <p className="text-xs text-slate-500">اگر بل دستیاب نہیں تو آپ اس کے بغیر بھی آگے بڑھ سکتے ہیں۔</p>
          </div>
        )}

        {/* Final Confirmation Summary */}
        {step === TOTAL_STEPS - 1 && (
          <div className="text-start bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-2 max-w-md mx-auto text-sm">
            <p className="font-bold text-xs uppercase text-[#0B4F43] tracking-wide border-b border-slate-200 pb-1.5">
              درخواست کا خلاصہ · Application Summary
            </p>
            <div className="space-y-1 text-xs">
              <p className="flex justify-between">
                <span className="text-slate-500">نام / Full Name:</span>
                <span className="font-bold text-slate-900">{values.citizen_name}</span>
              </p>
              <p className="flex justify-between">
                <span className="text-slate-500">شناختی کارڈ / CNIC:</span>
                <span className="font-mono font-bold text-slate-900" dir="ltr">{values.cnic}</span>
              </p>
              <p className="flex justify-between">
                <span className="text-slate-500">فون / Phone:</span>
                <span className="font-mono font-bold text-slate-900" dir="ltr">{values.phone}</span>
              </p>
              <p className="flex justify-between">
                <span className="text-slate-500">افراد خانہ / Family:</span>
                <span className="font-bold text-slate-900">{values.household_size}</span>
              </p>
              <p className="flex justify-between">
                <span className="text-slate-500">ماہانہ آمدنی / Income:</span>
                <span className="font-mono font-bold text-slate-900">Rs {Number(values.monthly_income).toLocaleString()}</span>
              </p>
              <p className="flex justify-between">
                <span className="text-slate-500">دستاویز / Document:</span>
                <span className="font-medium text-slate-900">{file ? file.name : "کوئی نہیں (بغیر بل)"}</span>
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-3 text-xs font-medium max-w-md mx-auto">
            {error}
          </div>
        )}

        {/* Wizard Controls */}
        <div className="grid grid-cols-2 gap-3 pt-3 max-w-md mx-auto">
          <Button
            variant="neutral"
            onClick={() => { setError(""); setStep(step - 1); }}
            disabled={step === 0 || busy}
          >
            <ArrowRight className="w-4 h-4 rtl:rotate-0 rotate-180" /> واپس · Back
          </Button>

          {step < TOTAL_STEPS - 1 ? (
            <Button
              variant="secondary"
              onClick={() => { setError(""); setStep(step + 1); }}
              disabled={cur ? !cur.ok(value) : false}
            >
              آگے · Next <ArrowLeft className="w-4 h-4 rtl:rotate-0 rotate-180" />
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={submit}
              disabled={busy}
            >
              {busy ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> جانچ ہو رہی ہے...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" /> بھیجیں · Submit
                </>
              )}
            </Button>
          )}
        </div>
      </Card>
    </AppShell>
  );
}
