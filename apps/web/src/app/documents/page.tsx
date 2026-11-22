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
      setError((e as ApiError).message_ur ?? (e as ApiError).message_en ?? "Could not check the document");
    } finally {
      setBusy(false);
    }
  }

  const tampered = !!res && res.tamper_score >= 0.5;

  return (
    <AppShell title="کاغذ جانچ · Document Verification">
      <Card className="p-5 space-y-2">
        <h2 className="text-xl font-bold text-[#0B4F43]">دستاویز کی خودکار جانچ · Document Blur & Tamper Check</h2>
        <p className="text-sm text-[#5B6F6A]">
          شناختی کارڈ یا بجلی کے بل کی تصویر اپ لوڈ کریں۔ کمپیوٹر ویژن تصویر کا فوکس (Blur)، دستاویزی ترمیم (Tamper) اور تحریر کی درستی جانچتا ہے۔
        </p>
      </Card>

      {/* Upload Zone */}
      <Card className="p-6 space-y-4 text-center">
        <label className="block p-6 rounded-2xl border-2 border-dashed border-[#0B4F43]/40 bg-[#F7F4EE] hover:bg-[#DDEFE9]/30 text-[#0B4F43] font-bold cursor-pointer transition shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] flex items-center justify-center mx-auto mb-2">
            <Camera className="w-7 h-7" />
          </div>
          <span className="text-base block">
            {file ? `✓ ${file.name}` : "تصویر منتخب کریں یا کیمرے سے کھینچیں · Choose or Snap Photo"}
          </span>
          <span className="text-xs text-[#5B6F6A] font-normal block mt-1">
            CNIC, Electricity Bill, or Income Certificate (JPG, PNG)
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
              className="max-h-60 mx-auto rounded-2xl border-2 border-[#E2DDD3] shadow-md object-contain"
            />
            <div className="absolute top-2 right-2 bg-black/70 text-white text-[11px] px-2 py-0.5 rounded-lg flex items-center gap-1">
              <Eye className="w-3.5 h-3.5" /> پریویو
            </div>
          </div>
        )}

        <Button
          variant="primary"
          onClick={check}
          disabled={!file || busy}
          className="w-full flex items-center justify-center gap-2"
        >
          {busy ? (
            <>
              <RefreshCw className="w-5 h-5 animate-spin" /> دستاویز کی جانچ ہو رہی ہے...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" /> جانچیں · Check Document
            </>
          )}
        </Button>

        <p className="text-[11px] text-[#5B6F6A]">
          ٹیسٹنگ ٹپ: فائل کے نام میں &ldquo;blur&rdquo; یا &ldquo;fake&rdquo; رکھ کر ڈیمو سسٹم کے مختلف نتائج دیکھ سکتے ہیں۔
        </p>
      </Card>

      {error && (
        <div className="bg-[#FEE2E2] border border-[#F87171] text-[#991B1B] rounded-2xl p-4 font-bold text-sm">
          {error}
        </div>
      )}

      {/* Visual Blur Gate Alert & Diagnosis */}
      {res && (
        <div className="space-y-4 animate-fade-up">
          {/* Prominent Blur Gate Alert */}
          {res.is_blurry ? (
            <div className="bg-[#FEF3C7] border-2 border-[#C77700] rounded-3xl p-5 space-y-3 shadow-soft">
              <div className="flex items-center justify-between">
                <StatusBadge status="need_proof" labelUr="دھندلی تصویر" labelEn="Blurry Photo" />
                <button
                  onClick={() => speak("تصویر دھندلی ہے، براہ کرم بہتر روشنی میں دوبارہ تصویر لیں", "ur-PK")}
                  type="button"
                  className="min-h-[36px] min-w-[36px] rounded-xl bg-white text-[#92400E] flex items-center justify-center border border-[#FCD34D]"
                  aria-label="Listen warning"
                >
                  <Volume2 className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-2xl bg-[#C77700]/10 text-[#C77700] flex items-center justify-center shrink-0">
                  <AlertTriangle className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-[#92400E]">تصویر دھندلی ہے — دوبارہ لیں</h3>
                  <p className="text-sm text-[#78350F] mt-0.5">
                    The photo is blurry and text cannot be extracted reliably. Please retake it in steady light.
                  </p>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-3 border border-[#FCD34D] text-xs text-[#78350F] space-y-1">
                <p className="font-bold">بہتر تصویر کے لیے مشورے:</p>
                <ul className="list-disc ps-4 space-y-0.5">
                  <li>کیمرے کو کاغذ کے بالکل سامنے سیدھا پکڑیں۔</li>
                  <li>کافی روشنی میں تصویر بنائیں تاکہ پرچھائیں نہ پڑے۔</li>
                  <li>کاغذ کے چاروں کونے فریم کے اندر ہونے چاہئیں۔</li>
                </ul>
              </div>
            </div>
          ) : tampered ? (
            <div className="bg-[#FEE2E2] border-2 border-[#B3261E] rounded-3xl p-5 space-y-3 shadow-soft">
              <div className="flex items-center justify-between">
                <StatusBadge status="scam" labelUr="مشکوک ترمیم" labelEn="Tamper Detected" />
                <button
                  onClick={() => speak("کاغذ میں ممکنہ ترمیم کا شبہ ہے، یہ افسر کو بھیجا جائے گا", "ur-PK")}
                  type="button"
                  className="min-h-[36px] min-w-[36px] rounded-xl bg-white text-[#B3261E] flex items-center justify-center border border-[#FCA5A5]"
                  aria-label="Listen warning"
                >
                  <Volume2 className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-2xl bg-[#B3261E]/10 text-[#B3261E] flex items-center justify-center shrink-0">
                  <ShieldAlert className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-[#7F1D1D]">کاغذ میں تبدیلی کا شبہ ہے</h3>
                  <p className="text-sm text-[#991B1B] mt-0.5">
                    Possible digital editing detected. It will be routed to a human officer for manual verification.
                  </p>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-3 border border-[#FCA5A5] text-xs text-[#7F1D1D]">
                <p className="font-bold">پالیسی گارنٹی: ہمارا سسٹم کبھی بھی خودکار مسترد نہیں کرتا۔ افسر اصلی کاغذات کی خود جانچ کرے گا۔</p>
              </div>
            </div>
          ) : (
            <div className="bg-[#DDEFE9] border-2 border-[#1F8A5B] rounded-3xl p-5 space-y-3 shadow-soft">
              <div className="flex items-center justify-between">
                <StatusBadge status="approved" labelUr="کاغذ صاف ہے" labelEn="Clean & Sharp" />
                <button
                  onClick={() => speak("کاغذ صاف اور اصلی ہے، تصدیق کامیاب رہی", "ur-PK")}
                  type="button"
                  className="min-h-[36px] min-w-[36px] rounded-xl bg-white text-[#0B4F43] flex items-center justify-center border border-[#A7F3D0]"
                  aria-label="Listen confirmation"
                >
                  <Volume2 className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-2xl bg-[#1F8A5B]/10 text-[#1F8A5B] flex items-center justify-center shrink-0">
                  <CheckCircle2 className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-[#0B4F43]">کاغذ صاف اور اصلی لگتا ہے</h3>
                  <p className="text-sm text-[#17302B] mt-0.5">
                    The document looks sharp and genuine. OCR extracted details successfully.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Detailed Scores & Field Confidences */}
          <Card className="p-5 space-y-4">
            <h4 className="font-bold text-sm uppercase text-[#0B4F43]">تکنیکی پیمانے · Technical Verification Metrics</h4>

            {/* Sharpness Score Meter */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-bold">
                <span className="text-[#17302B]">
                  تصویر کا نکھار (Sharpness Score) {res.is_blurry ? "— ناکافی" : "— تسلی بخش"}
                </span>
                <span className={res.is_blurry ? "text-[#C77700]" : "text-[#1F8A5B]"}>
                  {Math.round(res.blur_score)} / 500
                </span>
              </div>
              <div className="h-3 bg-[#E2DDD3] rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    res.is_blurry ? "bg-[#C77700]" : "bg-[#1F8A5B]"
                  }`}
                  style={{ width: `${Math.min(100, (res.blur_score / 500) * 100)}%` }}
                />
              </div>
              <p className="text-[10px] text-[#5B6F6A]">کم از کم قابل قبول نکھار: 100.0</p>
            </div>

            {/* Tamper Score Meter */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-bold">
                <span className="text-[#17302B]">
                  ترمیم کا شبہ (Tamper Risk) {tampered ? "— بلند خطرہ" : "— محفوظ"}
                </span>
                <span className={tampered ? "text-[#B3261E]" : "text-[#1F8A5B]"}>
                  {Math.round(res.tamper_score * 100)}%
                </span>
              </div>
              <div className="h-3 bg-[#E2DDD3] rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    tampered ? "bg-[#B3261E]" : "bg-[#1F8A5B]"
                  }`}
                  style={{ width: `${Math.min(100, res.tamper_score * 100)}%` }}
                />
              </div>
            </div>

            {/* Field Confidence Dots & Extracted Values */}
            {Object.keys(res.fields).length > 0 && (
              <div className="pt-2 border-t border-[#E2DDD3] space-y-2">
                <p className="font-bold text-xs text-[#0B4F43]">
                  کاغذ سے نکالی گئی معلومات اور فیلڈ اعتماد (Field OCR Confidence):
                </p>
                <div className="grid gap-2">
                  {Object.entries(res.fields).map(([k, val]) => {
                    const c = res.field_confidences[k] ?? 1.0;
                    const isHigh = c >= 0.8;
                    const isMid = c >= 0.5 && c < 0.8;
                    const dotColor = isHigh ? "bg-[#1F8A5B]" : isMid ? "bg-[#C77700]" : "bg-[#B3261E]";

                    return (
                      <div
                        key={k}
                        className="bg-[#F7F4EE] rounded-xl p-3 flex items-center justify-between text-xs border border-[#E2DDD3]"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-2.5 h-2.5 rounded-full ${dotColor} shrink-0`}
                            title={`Confidence: ${Math.round(c * 100)}%`}
                          />
                          <span className="font-bold text-[#17302B] capitalize">{k.replace("_", " ")}:</span>
                          <span className="text-[#17302B] font-mono">{String(val)}</span>
                        </div>
                        <span
                          className={`font-mono font-bold px-2 py-0.5 rounded-md ${
                            isHigh
                              ? "bg-[#DDEFE9] text-[#065F46]"
                              : isMid
                              ? "bg-[#FEF3C7] text-[#92400E]"
                              : "bg-[#FEE2E2] text-[#7F1D1D]"
                          }`}
                        >
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
