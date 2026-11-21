"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Volume2 } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type CaseItem, type CaseStatus } from "@/lib/api";
import { getSession, speak } from "@/lib/session";

const LOOK: Record<CaseStatus, { ur: string; en: string; step: number; color: string }> = {
  draft: { ur: "مسودہ", en: "Draft", step: 1, color: "bg-gray-200 text-gray-800" },
  submitted: { ur: "جمع ہو گئی", en: "Submitted", step: 1, color: "bg-sky-100 text-sky-800" },
  processing: { ur: "کارروائی جاری", en: "Processing", step: 2, color: "bg-sky-100 text-sky-800" },
  in_review: { ur: "افسر دیکھ رہا ہے", en: "With an officer", step: 2, color: "bg-sky-100 text-sky-800" },
  need_proof: { ur: "مزید ثبوت چاہیے", en: "More proof needed", step: 2, color: "bg-amber-100 text-amber-900" },
  need_more_info: { ur: "مزید معلومات چاہیے", en: "More info needed", step: 2, color: "bg-amber-100 text-amber-900" },
  approved: { ur: "منظور", en: "Approved", step: 3, color: "bg-emerald-100 text-emerald-800" },
  disbursed: { ur: "رقم بھیج دی گئی", en: "Paid out", step: 4, color: "bg-emerald-200 text-emerald-900" },
  rejected: { ur: "مسترد", en: "Rejected", step: 3, color: "bg-red-100 text-red-800" },
};

export default function CasesPage() {
  const [cases, setCases] = useState<CaseItem[] | null>(null);
  const [open, setOpen] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const active = localStorage.getItem("active_citizen");
    const isHelper = getSession()?.role === "helper";
    api.listCases()
      .then((all) => setCases(isHelper && active ? all.filter((c) => c.citizen_id === active) : all))
      .catch((e: ApiError) => setError(e.message_ur ?? e.message_en ?? "Error"));
  }, []);

  return (
    <AppShell title="میرے کیس · My Cases">
      {error && <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">{error}</p>}
      {cases && cases.length === 0 && (
        <div className="bg-white rounded-3xl p-6 text-center space-y-3">
          <p className="text-xl font-bold">ابھی کوئی کیس نہیں · No cases yet</p>
          <Link href="/apply" className="block h-14 leading-[3.5rem] rounded-2xl bg-emerald-600 text-white font-bold">نئی درخواست · Apply</Link>
        </div>
      )}

      {cases?.map((c) => {
        const look = LOOK[c.status];
        const d = c.decision;
        return (
          <div key={c.id} className="bg-white rounded-3xl shadow p-5 space-y-3">
            <button className="w-full text-start" onClick={() => setOpen(open === c.id ? "" : c.id)}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-lg font-bold">{c.citizen_name}</p>
                <span className={`px-3 rounded-full font-bold ${look.color}`}>{look.ur} · {look.en}</span>
              </div>
              <div className="flex gap-1 mt-3">
                {[1, 2, 3, 4].map((n) => (
                  <div key={n} className={`h-2 flex-1 rounded-full ${n <= look.step ? "bg-emerald-500" : "bg-gray-200"}`} />
                ))}
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>جمع</span><span>جانچ</span><span>فیصلہ</span><span>ادائیگی</span>
              </div>
            </button>

            {open === c.id && (
              <div className="border-t pt-3 space-y-2">
                <p className="text-gray-500 text-sm">Case {c.id} · {c.cnic}</p>
                <p>مطلوبہ رقم · Requested: Rs {c.requested_amount}</p>
                {d ? (
                  <>
                    <div className="flex items-start gap-2">
                      <div className="flex-1">
                        <p className="text-lg font-bold">{d.reason_simple.ur}</p>
                        <p className="text-gray-600">{d.reason_simple.en}</p>
                      </div>
                      <button onClick={() => speak(d.reason_simple.ur)} className="h-12 w-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center" aria-label="Play audio">
                        <Volume2 className="w-6 h-6" />
                      </button>
                    </div>
                    {d.missing.length > 0 && <ul className="list-disc ps-6 text-amber-800">{d.missing.map((m) => <li key={m}>{m}</li>)}</ul>}
                    <p className="text-sm text-gray-500">Confidence {Math.round(d.confidence * 100)}% · Rule v{d.rule_version}</p>
                  </>
                ) : (
                  <p className="text-gray-500">فیصلے کا انتظار · Waiting for a decision</p>
                )}
                {c.officer_notes && <p className="bg-gray-100 rounded-xl p-3 text-sm">Officer note: {c.officer_notes}</p>}
              </div>
            )}
          </div>
        );
      })}
    </AppShell>
  );
}