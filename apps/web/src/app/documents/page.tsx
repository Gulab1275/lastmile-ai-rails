"use client";

import { useEffect, useState } from "react";
import { Camera, CheckCircle2, AlertTriangle, ShieldAlert, Volume2, RefreshCw, Upload, Eye } from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api, { type ApiError, type DocCheck } from "@/lib/api";
import { speak } from "@/lib/session";

export default function DocumentsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [res, setRes] = useState<DocCheck | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!file) { setPreview(""); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  async function check() {
    if (!file) return;
    setBusy(true);
    setError("");
    setRes(null);
    try {
      const r = await api.checkDocument(file);
      setRes(r);
      if (r.is_blurry) {
        speak("تصویر دھندلی ہے، براہ کرم بہتر روشنی میں دوبارہ تصویر لیں", "ur-PK");
      } else if (r.tamper_score >= 0.5) {
        speak("کاغذ میں ممکنہ ترمیم کا شبہ ہے، یہ افسر کو بھیجا جائے گا", "ur-PK");
      } else {
        speak("کاغذ صاف اور اصلی ہے، تصدیق کامیاب رہی", "ur-PK");
      }
    } catch (e) {
      setError((e as ApiError).message_ur ?? (e as ApiError).message_en ?? "Could not check document");
    } finally {
      setBusy(false);
    }
  }

  const tampered = !!res && res.tamper_score >= 0.5;

  return (
    <AppShell title="کاغذ جانچ · Document Verification">
      <Card className="p-5 space-y-1.5">
        <h2 className="text-xl font-bold font-heading text-slate-900">دستاویز کی خودکار جانچ · Blur & Tamper Verification</h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          شناختی کارڈ یا بجلی کے بل کی تصویر اپ لوڈ کریں۔ کمپیوٹر ویژن تصویر کا فوکس (Blur)، دستاویزی ترمیم (Tamper) اور تحریر کی درستی جانچتا ہے۔
        </p>
      </Card>

      {/* Upload Zone */}
      <Card className="p-5 sm:p-6 space-y-4 text-center">
        <label className="block p-6 sm:p-8 rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 hover:bg-emerald-50/50 hover:border-[#0B4F43] cursor-pointer transition">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-[#0B4F43] flex items-center justify-center mx-auto mb-2">
            <Camera className="w-6 h-6" />
          </div>
          <span className="text-sm sm:text-base font-bold text-slate-900 block">
            {file ? `✓ ${file.name}` : "تصویر منتخب کریں یا کیمرے سے کھینچیں · Choose Photo"}
          </span>
          <span className="text-xs text-slate-500 block mt-1">
            CNIC or Electricity Bill (JPG, PNG)
          </span>
          <input
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null);
              setRes(null);
            }}
          />
        </label>

        {preview && (
          <div className="relative inline-block mx-auto max-w-full">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={preview}
              alt="preview"
              className="max-h-56 mx-auto rounded-xl border border-slate-200 shadow-sm object-contain"
            />
          </div>
        )}

        <Button
          variant="primary"
          onClick={check}
          disabled={!file || busy}
          className="w-full"
        >
          {busy ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" /> جانچ ہو رہی ہے...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" /> جانچیں · Check Document
            </>
          )}
        </Button>

        <p className="text-[11px] text-slate-500">
          ٹیسٹنگ مشورہ: فائل کے نام میں &ldquo;blur&rdquo; یا &ldquo;fake&rdquo; رکھ کر سسٹم کا برتاؤ دیکھ سکتے ہیں۔
        </p>
      </Card>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-4 font-medium text-xs">
          {error}
        </div>
      )}

      {/* Results Section */}
      {res && (
        <div className="space-y-4">
          {/* Blur Gate Alert */}
          {res.is_blurry ? (
            <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <StatusBadge status="need_proof" labelUr="تصویر دھندلی ہے" labelEn="Blurry Photo" />
                <button
                  onClick={() => speak("تصویر دھندلی ہے، براہ کرم بہتر روشنی میں دوبارہ تصویر لیں", "ur-PK")}
                  type="button"
                  className="p-2 rounded-lg bg-white text-amber-900 border border-amber-200 text-xs flex items-center gap-1 shadow-sm"
                  aria-label="Listen warning"
                >
                  <Volume2 className="w-3.5 h-3.5" /> سنیں
                </button>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-amber-950 font-heading">تصویر دھندلی ہے — دوبارہ لیں</h3>
                  <p className="text-xs text-amber-900 mt-0.5">
                    The photo is blurry and text cannot be extracted reliably. Please retake it in steady light.
                  </p>
                </div>
              </div>
            </div>
          ) : tampered ? (
            <div className="bg-rose-50 border border-rose-300 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <StatusBadge status="scam" labelUr="مشکوک ترمیم" labelEn="Tamper Detected" />
                <button
                  onClick={() => speak("کاغذ میں ممکنہ ترمیم کا شبہ ہے، یہ افسر کو بھیجا جائے گا", "ur-PK")}
                  type="button"
                  className="p-2 rounded-lg bg-white text-rose-900 border border-rose-200 text-xs flex items-center gap-1 shadow-sm"
                  aria-label="Listen warning"
                >
                  <Volume2 className="w-3.5 h-3.5" /> سنیں
                </button>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-800 flex items-center justify-center shrink-0">
                  <ShieldAlert className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-rose-950 font-heading">کاغذ میں تبدیلی کا شبہ ہے</h3>
                  <p className="text-xs text-rose-900 mt-0.5">
                    Possible digital editing detected. It will be routed to a human officer for manual verification.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-emerald-50 border border-emerald-300 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <StatusBadge status="approved" labelUr="کاغذ صاف ہے" labelEn="Clean & Sharp" />
                <button
                  onClick={() => speak("کاغذ صاف اور اصلی ہے، تصدیق کامیاب رہی", "ur-PK")}
                  type="button"
                  className="p-2 rounded-lg bg-white text-emerald-900 border border-emerald-200 text-xs flex items-center gap-1 shadow-sm"
                  aria-label="Listen confirmation"
                >
                  <Volume2 className="w-3.5 h-3.5" /> سنیں
                </button>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-emerald-950 font-heading">کاغذ صاف اور اصلی لگتا ہے</h3>
                  <p className="text-xs text-emerald-800 mt-0.5">
                    The document looks sharp and genuine. OCR extracted details successfully.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Technical Scores Card */}
          <Card className="p-5 space-y-4">
            <h4 className="font-bold text-xs uppercase tracking-wider text-slate-500">
              تکنیکی پیمائش · Quality Metrics
            </h4>

            {/* Sharpness Meter */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">تصویر کا نکھار (Sharpness):</span>
                <span className={res.is_blurry ? "text-amber-700" : "text-emerald-700 font-mono"}>
                  {Math.round(res.blur_score)} / 500
                </span>
              </div>
              <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${res.is_blurry ? "bg-amber-500" : "bg-emerald-600"}`}
                  style={{ width: `${Math.min(100, (res.blur_score / 500) * 100)}%` }}
                />
              </div>
            </div>

            {/* Tamper Risk Meter */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">ترمیم کا شبہ (Tamper Risk):</span>
                <span className={tampered ? "text-rose-700 font-mono" : "text-emerald-700 font-mono"}>
                  {Math.round(res.tamper_score * 100)}%
                </span>
              </div>
              <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${tampered ? "bg-rose-600" : "bg-emerald-600"}`}
                  style={{ width: `${Math.min(100, res.tamper_score * 100)}%` }}
                />
              </div>
            </div>

            {/* Field Confidence Grid */}
            {Object.keys(res.fields).length > 0 && (
              <div className="pt-3 border-t border-slate-100 space-y-2">
                <p className="font-bold text-xs text-slate-900">
                  کاغذ سے نکالی گئی معلومات (Extracted Fields & OCR Confidence):
                </p>
                <div className="grid gap-2">
                  {Object.entries(res.fields).map(([k, val]) => {
                    const c = res.field_confidences[k] ?? 1.0;
                    const isHigh = c >= 0.8;
                    const isMid = c >= 0.5 && c < 0.8;

                    return (
                      <div
                        key={k}
                        className="bg-slate-50 rounded-xl p-3 flex items-center justify-between text-xs border border-slate-200"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full shrink-0 ${isHigh ? "bg-emerald-500" : isMid ? "bg-amber-500" : "bg-rose-500"}`}
                          />
                          <span className="font-semibold text-slate-700 capitalize">{k.replace("_", " ")}:</span>
                          <span className="font-mono text-slate-900" dir="ltr">{String(val)}</span>
                        </div>
                        <span className="font-mono font-semibold text-slate-600">
                          {Math.round(c * 100)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </AppShell>
  );
}
