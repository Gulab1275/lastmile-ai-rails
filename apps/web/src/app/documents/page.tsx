"use client";

import { useEffect, useState } from "react";
import { Camera, CheckCircle2, AlertTriangle, ShieldAlert } from "lucide-react";
import AppShell from "@/components/appShell";
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
    setBusy(true); setError(""); setRes(null);
    try {
      const r = await api.checkDocument(file);
      setRes(r);
      speak(r.is_blurry ? "تصویر دھندلی ہے، دوبارہ لیں" : r.tamper_score >= 0.5 ? "کاغذ میں تبدیلی کا شبہ ہے" : "کاغذ صاف ہے");
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not check the document");
    } finally { setBusy(false); }
  }

  const tampered = !!res && res.tamper_score >= 0.5;
  const v = !res ? null
    : res.is_blurry ? { tone: "bg-amber-100 text-amber-900", icon: <AlertTriangle className="w-12 h-12" />, ur: "تصویر دھندلی ہے، دوبارہ لیں", en: "The photo is blurry. Please retake it in better light." }
    : tampered ? { tone: "bg-red-100 text-red-900", icon: <ShieldAlert className="w-12 h-12" />, ur: "کاغذ میں تبدیلی کا شبہ ہے", en: "Possible editing detected. Sent to an officer. It is never auto-rejected." }
    : { tone: "bg-emerald-100 text-emerald-900", icon: <CheckCircle2 className="w-12 h-12" />, ur: "کاغذ صاف اور اصلی لگتا ہے", en: "The document looks clear and genuine." };

  return (
    <AppShell title="کاغذ جانچ · Document Check">
      <p className="text-gray-600">Upload a photo of a CNIC or electricity bill. The system checks sharpness (blur) and signs of digital editing (tampering).</p>

      <label className="block h-20 leading-[5rem] text-center rounded-2xl border-2 border-dashed border-emerald-400 text-emerald-700 font-bold cursor-pointer bg-white">
        <Camera className="inline w-6 h-6 me-2" />{file ? file.name : "تصویر منتخب کریں · Choose photo"}
        <input type="file" accept="image/*" capture="environment" className="hidden" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setRes(null); }} />
      </label>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      {preview && <img src={preview} alt="preview" className="max-h-56 mx-auto rounded-2xl" />}
      <button onClick={check} disabled={!file || busy} className="w-full h-14 rounded-2xl bg-emerald-600 text-white text-lg font-bold disabled:opacity-40">
        {busy ? "..." : "جانچیں · Check"}
      </button>
      <p className="text-xs text-gray-500">Demo tip (mock mode): name the file with “blur” or “fake” to see those results. With the real backend, use a really blurry photo or an edited image.</p>

      {error && <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">{error}</p>}

      {res && v && (
        <div className={`rounded-3xl p-5 space-y-3 ${v.tone}`}>
          <div className="flex items-center gap-4">{v.icon}<div><p className="text-2xl font-bold">{v.ur}</p><p>{v.en}</p></div></div>
          <div>
            <div className="flex justify-between text-sm"><span>Sharpness score {res.is_blurry ? "(too low)" : "(good)"}</span><b>{Math.round(res.blur_score)}</b></div>
            <div className="h-4 bg-white/70 rounded-full overflow-hidden"><div className={`h-full ${res.is_blurry ? "bg-amber-500" : "bg-emerald-600"}`} style={{ width: `${Math.min(100, res.blur_score / 5)}%` }} /></div>
          </div>
          <div>
            <div className="flex justify-between text-sm"><span>Chance of tampering</span><b>{Math.round(res.tamper_score * 100)}%</b></div>
            <div className="h-4 bg-white/70 rounded-full overflow-hidden"><div className={`h-full ${tampered ? "bg-red-600" : "bg-emerald-600"}`} style={{ width: `${res.tamper_score * 100}%` }} /></div>
          </div>
          {Object.keys(res.fields).length > 0 && (
            <div className="bg-white/70 rounded-2xl p-3 text-sm">
              <p className="font-bold mb-1">Read from the document</p>
              {Object.entries(res.fields).map(([k, val]) => {
                const c = res.field_confidences[k];
                return (
                  <p key={k} className="flex justify-between gap-2">
                    <span>{k}: <b>{String(val)}</b></span>
                    {c !== undefined && <span className={c < 0.6 ? "text-red-700 font-bold" : ""}>{Math.round(c * 100)}%</span>}
                  </p>
                );
              })}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}