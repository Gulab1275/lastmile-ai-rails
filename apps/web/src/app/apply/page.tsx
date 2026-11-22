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
  { key: "citizen_name", icon: <User className="w-10 h-10" />, ur: "آپ کا پورا نام کیا ہے؟", en: "What is your full name?", type: "text", hint: "Parveen Bibi", ok: (v) => v.trim().length >= 3 },
  { key: "cnic", icon: <CreditCard className="w-10 h-10" />, ur: "شناختی کارڈ نمبر بتائیں", en: "Your CNIC number", type: "tel", hint: "42101-1234567-1", ok: (v) => /^\d{5}-?\d{7}-?\d$/.test(v) },
  { key: "phone", icon: <Phone className="w-10 h-10" />, ur: "آپ کا موبائل فون نمبر کیا ہے؟", en: "Your mobile phone number", type: "tel", hint: "0300-1112223", ok: (v) => /^03\d{2}-?\d{7}$/.test(v) },
  { key: "household_size", icon: <Users className="w-10 h-10" />, ur: "گھر میں کل کتنے افراد رہتے ہیں؟", en: "How many people in your household?", type: "tel", hint: "5", ok: (v) => Number(v) >= 1 },
  { key: "monthly_income", icon: <Wallet className="w-10 h-10" />, ur: "گھر کی کل ماہانہ آمدنی کتنی ہے؟ (روپے)", en: "Total monthly household income (PKR)", type: "tel", hint: "18000", ok: (v) => v !== "" && Number(v) >= 0 },
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
        <div className="bg-[#FFFBEB] border-2 border-[#FCD34D] rounded-3xl p-6 space-y-4 text-center shadow-soft">
          <p className="text-xl font-bold text-[#92400E]">پہلے خاندان منتخب کریں · Choose a family first</p>
          <p className="text-sm text-[#78350F]">مددگار موڈ میں درخواست شروع کرنے سے پہلے خاندان کا چناؤ لازمی ہے۔</p>
          <Link href="/families">
            <Button variant="secondary">خاندان کھولیں · Open families list</Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  if (offlineSaved) {
    return (
      <AppShell title="درخواست محفوظ ہو گئی · Application Saved">
        <div className="bg-[#E0F2FE] border-2 border-[#38BDF8] text-[#075985] rounded-3xl p-6 space-y-4 text-center shadow-soft">
          <ShieldCheck className="w-16 h-16 mx-auto text-[#0284C7]" />
          <p className="text-2xl font-bold">فارم فون میں محفوظ ہو گیا ہے</p>
          <p className="text-base text-[#0C4A6E]">
            Saved locally on this phone. It will be sent automatically when signal returns.
          </p>
          <p className="text-xs font-mono bg-white/70 rounded-xl p-2 inline-block">Idempotency key active · No duplicate claims</p>
          <div className="pt-2">
            <Link href="/dashboard">
              <Button variant="secondary">ہوم پر جائیں · Back to Home</Button>
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

  // ==================== DECISION SCREEN (3 DISTINCT POLISHED LAYOUTS) ====================
  if (result) {
    if (result.route === "auto_approve") {
      return (
        <AppShell title="درخواست منظور · Approved">
          <StepStones currentStep={4} />
          <div className="bg-[#DDEFE9] border-2 border-[#1F8A5B] rounded-3xl p-6 space-y-5 text-center shadow-lift mt-4">
            <div className="flex items-center justify-between">
              <span className="px-3.5 py-1.5 bg-[#1F8A5B] text-white text-xs font-bold rounded-full shadow-sm">
                خودکار منظوری · Auto-Approved
              </span>
              <ConfidenceRing confidence={result.confidence} color="#1F8A5B" label="اعتماد" />
            </div>

            <div className="space-y-2">
              <div className="w-16 h-16 rounded-full bg-[#1F8A5B]/10 flex items-center justify-center mx-auto text-[#1F8A5B]">
                <CheckCircle2 className="w-10 h-10 animate-bounce" />
              </div>
              <h2 className="text-3xl font-bold text-[#0B4F43]">مبارک ہو! آپ کی درخواست منظور ہو گئی</h2>
              <p className="text-base text-[#17302B] font-medium">{result.reason_simple.ur}</p>
              <p className="text-sm text-[#5B6F6A]">{result.reason_simple.en}</p>
            </div>

            <div className="bg-white rounded-2xl p-4 border border-[#1F8A5B]/30 text-start space-y-1.5 shadow-sm">
              <p className="text-xs font-bold text-[#1F8A5B] uppercase tracking-wide">ادائیگی کی تفصیل · Payment Rail</p>
              <p className="font-bold text-[#17302B] text-base">SBP Raast Fast Payment Rail</p>
              <p className="text-xs text-[#5B6F6A]">
                کرپٹوگرافک منظوری ٹوکن جاری کر دیا گیا ہے۔ رقم براہ راست آپ کے اکاؤنٹ میں منتقل ہوگی۔
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Button
                variant="outline"
                onClick={() => speak(result.reason_simple.ur)}
                className="flex-1"
              >
                <Volume2 className="w-5 h-5 text-[#0B4F43]" /> سنیں · Listen
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
          <div className="bg-[#FEF3C7] border-2 border-[#C77700] rounded-3xl p-6 space-y-5 text-center shadow-soft mt-4">
            <div className="flex items-center justify-between">
              <span className="px-3.5 py-1.5 bg-[#C77700] text-white text-xs font-bold rounded-full shadow-sm">
                اضافی دستاویز · Need One More Document
              </span>
              <ConfidenceRing confidence={result.confidence} color="#C77700" label="اعتماد" />
            </div>

            <div className="space-y-2">
              <div className="w-16 h-16 rounded-full bg-[#C77700]/10 flex items-center justify-center mx-auto text-[#C77700]">
                <AlertTriangle className="w-10 h-10" />
              </div>
              <h2 className="text-2xl font-bold text-[#92400E]">ایک اضافی کاغذ کی ضرورت ہے</h2>
              <p className="text-base text-[#17302B] font-bold">{result.reason_simple.ur}</p>
              <p className="text-sm text-[#78350F]">{result.reason_simple.en}</p>
            </div>

            <div className="bg-white rounded-2xl p-4 border border-[#FCD34D] text-start space-y-2 shadow-sm">
              <p className="text-xs font-bold text-[#C77700] uppercase tracking-wide">مطلوبہ کاغذ · Required Document</p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#FEF3C7] text-[#C77700] flex items-center justify-center shrink-0">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <p className="font-bold text-[#17302B]">
                    {missingDoc.includes("bill") ? "بجلی کا واضح بل (Utility Bill)" : "شناختی کارڈ کی واضح کاپی (Clear CNIC)"}
                  </p>
                  <p className="text-xs text-[#5B6F6A]">دھندلاہٹ یا نامکمل فیلڈ کی وجہ سے خودکار سسٹم نے تصدیق روکی ہے۔</p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Link href="/documents" className="flex-1">
                <Button variant="primary" className="w-full">
                  <Camera className="w-5 h-5 me-1" /> کاغذ اپ لوڈ کریں · Upload
                </Button>
              </Link>
              <Link href="/cases" className="flex-1">
                <Button variant="outline" className="w-full">
                  کیس دیکھیں · View Case
                </Button>
              </Link>
            </div>
          </div>
        </AppShell>
      );
    }

    // Route: human_review (Calm, reassuring blue #4C5FD5 — NEVER RED)
    return (
      <AppShell title="افسر کا جائزہ · Human Officer Review">
        <StepStones currentStep={3} />
        <div className="bg-[#EEF2FF] border-2 border-[#4C5FD5] rounded-3xl p-6 space-y-5 text-center shadow-soft mt-4">
          <div className="flex items-center justify-between">
            <span className="px-3.5 py-1.5 bg-[#4C5FD5] text-white text-xs font-bold rounded-full shadow-sm">
              انسانی جائزہ · Human Review Required
            </span>
            <ConfidenceRing confidence={result.confidence} color="#4C5FD5" label="اعتماد" />
          </div>

          <div className="space-y-2">
            <div className="w-16 h-16 rounded-full bg-[#4C5FD5]/10 flex items-center justify-center mx-auto text-[#4C5FD5]">
              <HelpCircle className="w-10 h-10" />
            </div>
            <h2 className="text-2xl font-bold text-[#1E1B4B]">پریشان نہ ہوں — افسر جائزہ لے رہا ہے</h2>
            <p className="text-base text-[#17302B] font-bold">{result.reason_simple.ur}</p>
            <p className="text-sm text-[#4338CA]">{result.reason_simple.en}</p>
          </div>

          <div className="bg-white rounded-2xl p-4 border border-[#C7D2FE] text-start space-y-2 shadow-sm">
            <p className="text-xs font-bold text-[#4C5FD5] uppercase tracking-wide">پالیسی گارنٹی · Zero Auto-Reject Guarantee</p>
            <p className="text-xs text-[#312E81] leading-relaxed">
              ہماری پالیسی کے تحت کمپیوٹر کبھی بھی کسی درخواست کو خود بخود مسترد نہیں کرتا۔ آپ کا کیس ریلیف افسر کو تفصیلی نوٹس کے ساتھ بھیج دیا گیا ہے۔
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => speak(result.reason_simple.ur)}
              className="flex-1"
            >
              <Volume2 className="w-5 h-5 text-[#4C5FD5]" /> سنیں · Listen
            </Button>
            <Link href="/cases" className="flex-1">
              <Button variant="secondary" className="w-full bg-[#4C5FD5] hover:bg-[#3d4ec2]">
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
      {/* Stepping Stones Path Component */}
      <StepStones currentStep={currentMilestone} />

      <Card className="p-6 space-y-5 text-center mt-4">
        {/* Step Icon */}
        <div className="w-16 h-16 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] flex items-center justify-center mx-auto">
          {cur ? cur.icon : step === STEPS.length ? <Camera className="w-8 h-8 text-[#0F6B5A]" /> : <Send className="w-8 h-8 text-[#E8A33D]" />}
        </div>

        {/* Step Prompts */}
        <div>
          <h2 className="text-2xl font-bold text-[#17302B]">
            {cur ? cur.ur : step === STEPS.length ? "بجلی کے بل کی تصویر لیں" : "کیا آپ معلومات بھیجنا چاہتے ہیں؟"}
          </h2>
          <p className="text-sm text-[#5B6F6A] mt-1">
            {cur ? cur.en : step === STEPS.length ? "Take a photo of your electricity bill (optional proof)" : "Review your answers and submit"}
          </p>
        </div>

        {/* Audio Listen Button */}
        <button
          onClick={say}
          type="button"
          className="min-h-[48px] px-5 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] font-bold inline-flex items-center gap-2 hover:bg-[#cde4dc] transition"
        >
          <Volume2 className="w-5 h-5" /> سوال سنیں · Listen in Urdu
        </button>

        {/* Text Input & Big Voice Mic Button */}
        {cur && (
          <div className="space-y-4 max-w-md mx-auto">
            <input
              className="w-full min-h-[58px] border-2 border-[#E2DDD3] rounded-2xl px-4 text-xl text-center bg-[#F7F4EE] text-[#17302B] font-bold focus:border-[#0F6B5A] focus:outline-none"
              type={cur.type}
              inputMode={cur.type === "tel" ? "numeric" : "text"}
              placeholder={cur.hint}
              value={value}
              onChange={(e) => setValues({ ...values, [cur.key]: e.target.value })}
            />

            {/* Voice Mic Button with Waveform */}
            <button
              onClick={voice}
              disabled={listening}
              type="button"
              className={`w-full min-h-[52px] rounded-2xl font-bold inline-flex items-center justify-center gap-3 transition shadow-sm ${
                listening
                  ? "bg-[#B3261E] text-white animate-pulse"
                  : "bg-[#0B4F43] text-white hover:bg-[#093e34]"
              }`}
            >
              <Mic className="w-6 h-6" />
              {listening ? (
                <span className="flex items-center gap-2">
                  <span>سن رہا ہوں...</span>
                  <span className="flex gap-1 items-end h-4">
                    <span className="w-1 bg-white h-2 animate-bounce" />
                    <span className="w-1 bg-white h-4 animate-bounce delay-75" />
                    <span className="w-1 bg-white h-3 animate-bounce delay-150" />
                  </span>
                </span>
              ) : (
                "بول کر بتائیں · Speak in Urdu"
              )}
            </button>
          </div>
        )}

        {/* Photo Upload Step */}
        {step === STEPS.length && (
          <div className="max-w-md mx-auto space-y-3">
            <label className="min-h-[80px] rounded-2xl border-2 border-dashed border-[#0F6B5A] text-[#0B4F43] font-bold flex flex-col items-center justify-center cursor-pointer hover:bg-[#DDEFE9]/30 transition p-4">
              <Camera className="w-7 h-7 mb-1 text-[#0F6B5A]" />
              <span className="text-sm">{file ? `✓ ${file.name}` : "تصویر منتخب کریں · Choose / Snap photo"}</span>
              <input
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <p className="text-xs text-[#5B6F6A]">اگر بل دستیاب نہیں تو آپ اس کے بغیر بھی آگے بڑھ سکتے ہیں۔</p>
          </div>
        )}

        {/* Final Confirmation Summary */}
        {step === TOTAL_STEPS - 1 && (
          <div className="text-start bg-[#F7F4EE] rounded-2xl p-4 border border-[#E2DDD3] space-y-1.5 max-w-md mx-auto text-sm">
            <p className="font-bold text-xs uppercase text-[#0B4F43] mb-2">درخواست کا خلاصہ · Application Summary</p>
            <p>👤 <b>نام / Name:</b> {values.citizen_name}</p>
            <p>🪪 <b>شناختی کارڈ / CNIC:</b> {values.cnic}</p>
            <p>📞 <b>فون / Phone:</b> {values.phone}</p>
            <p>👨‍👩‍👧 <b>افراد خانہ / Family:</b> {values.household_size}</p>
            <p>💰 <b>ماہانہ آمدنی / Income:</b> Rs {values.monthly_income}</p>
            <p>📷 <b>دستاویز / Document:</b> {file ? file.name : "کوئی نہیں (بغیر بل)"}</p>
          </div>
        )}

        {error && (
          <div className="bg-[#FEE2E2] border border-[#F87171] text-[#991B1B] rounded-2xl p-3 font-bold text-sm">
            {error}
          </div>
        )}

        {/* Navigation Action Buttons */}
        <div className="grid grid-cols-2 gap-3 pt-2 max-w-md mx-auto">
          <Button
            variant="outline"
            onClick={() => { setError(""); setStep(step - 1); }}
            disabled={step === 0 || busy}
            className="flex items-center justify-center gap-1"
          >
            <ArrowRight className="w-4 h-4" /> واپس · Back
          </Button>

          {step < TOTAL_STEPS - 1 ? (
            <Button
              variant="secondary"
              onClick={() => { setError(""); setStep(step + 1); }}
              disabled={cur ? !cur.ok(value) : false}
              className="flex items-center justify-center gap-1"
            >
              آگے · Next <ArrowLeft className="w-4 h-4" />
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={submit}
              disabled={busy}
              className="flex items-center justify-center gap-2"
            >
              {busy ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> جانچ ہو رہی ہے...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" /> بھیجیں · Submit Claim
                </>
              )}
            </Button>
          )}
        </div>
      </Card>
    </AppShell>
  );
}
