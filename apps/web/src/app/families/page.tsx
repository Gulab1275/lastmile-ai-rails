"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, UserRound } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type ConsentStatus, type Family } from "@/lib/api";
import { getActiveCitizenId, setActiveCitizen } from "@/lib/session";

export default function FamiliesPage() {
  const [families, setFamilies] = useState<Family[]>([]);
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<Family | null>(null);
  const [consent, setConsent] = useState<ConsentStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getFamilies().then((f) => {
      setFamilies(f);
      const active = getActiveCitizenId();
      const found = f.find((x) => x.id === active);
      if (found) choose(found);
    }).catch((e: ApiError) => setError(e.message_en ?? "Could not load families"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function choose(f: Family) {
    setActiveCitizen(f.id, f.name); // tap 1
    setSelected(f);
    setConsent(null);
    setError("");
    try {
      setConsent(await api.getConsentStatus(f.id));
    } catch (e) {
      setError((e as ApiError).message_ur ?? (e as ApiError).message_en ?? "Consent check failed");
    }
  }

  const shown = families.filter((f) => (f.name + f.cnic).toLowerCase().includes(q.toLowerCase()));

  return (
    <AppShell title="خاندان · My Families">
      {selected && (
        <div className="bg-white rounded-3xl shadow p-5 space-y-3 border-2 border-emerald-500">
          <p className="text-xl font-bold">آپ کام کر رہے ہیں · Acting for: {selected.name}</p>
          {consent && !consent.can_helper_act && (
            <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">
              اس خاندان نے مددگار کی اجازت نہیں دی · No helper consent. Ask the family to allow it.
            </p>
          )}
          {consent?.can_helper_act && <p className="text-emerald-700 font-bold">✓ مددگار کی اجازت موجود ہے · Helper consent active</p>}
          {error && <p className="text-red-600 font-bold">{error}</p>}
          <div className="grid grid-cols-3 gap-2 text-center font-bold">
            <Link href="/apply" className="h-14 leading-[3.5rem] rounded-2xl bg-emerald-600 text-white">درخواست</Link>
            <Link href="/cases" className="h-14 leading-[3.5rem] rounded-2xl bg-emerald-100 text-emerald-800">کیس</Link>
            <Link href="/consent" className="h-14 leading-[3.5rem] rounded-2xl bg-emerald-100 text-emerald-800">رضامندی</Link>
          </div>
        </div>
      )}

      <div className="relative">
        <Search className="absolute top-4 start-4 w-6 h-6 text-gray-400" />
        <input className="w-full h-14 border-2 rounded-2xl ps-12 pe-4 text-lg bg-white" placeholder="تلاش کریں / Search name or CNIC" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <p className="text-gray-500">{shown.length} / {families.length}</p>

      <div className="grid grid-cols-2 gap-3">
        {shown.map((f) => (
          <button
            key={f.id}
            onClick={() => choose(f)}
            className={`rounded-2xl p-4 text-start shadow min-h-24 ${selected?.id === f.id ? "bg-emerald-600 text-white" : "bg-white"}`}
          >
            <UserRound className="w-7 h-7 mb-1" />
            <p className="font-bold leading-tight">{f.name}</p>
            <p className="text-xs opacity-70">{f.cnic}</p>
          </button>
        ))}
      </div>
    </AppShell>
  );
}