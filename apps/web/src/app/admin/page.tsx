"use client";

import { useEffect, useState } from "react";
import {
  FlaskConical, Rocket, Key, Copy, Check, Trash2, AlertTriangle,
  SlidersHorizontal, Code,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api, {
  type ApiError, type RuleSet, type RuleVersion, type SimulationResult,
  type ApiKeyItem, type ApiKeyCreated,
} from "@/lib/api";

export default function AdminPage() {
  const [tab, setTab] = useState<"rules" | "keys">("rules");
  const [showJson, setShowJson] = useState(false);

  // Rules state
  const [active, setActive] = useState<RuleSet | null>(null);
  const [draft, setDraft] = useState<RuleSet | null>(null);
  const [versions, setVersions] = useState<RuleVersion[]>([]);
  const [sim, setSim] = useState<SimulationResult | null>(null);
  const [simulatedFor, setSimulatedFor] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  // API Keys state
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);
  const [keyBusy, setKeyBusy] = useState(false);

  async function loadRules() {
    try {
      const [a, v] = await Promise.all([api.getActiveRules(), api.listRuleVersions()]);
      setActive(a); setDraft(a); setVersions(v);
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not load rules");
    }
  }

  async function loadKeys() {
    try {
      const list = await api.getApiKeys();
      setKeys(list);
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not load API keys");
    }
  }

  useEffect(() => {
    loadRules();
    loadKeys();
  }, []);

  if (!active || !draft) {
    return (
      <AppShell title="ایڈمن پورٹل · Admin Portal">
        {error ? <p className="text-[#B3261E] font-bold p-4 bg-[#FEE2E2] rounded-2xl">{error}</p> : <p className="p-4">لوڈ ہو رہا ہے...</p>}
      </AppShell>
    );
  }

  const draftKey = JSON.stringify(draft);
  const canPublish = sim !== null && simulatedFor === draftKey && draftKey !== JSON.stringify(active);
  const set = <K extends keyof RuleSet>(k: K, v: RuleSet[K]) => setDraft({ ...draft, [k]: v });
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

  async function simulate() {
    setBusy(true); setError(""); setMsg("");
    try {
      setSim(await api.simulateRules(draft!, 100));
      setSimulatedFor(draftKey);
    } catch (e) {
      setError((e as ApiError).message_en ?? "Simulation failed");
    } finally {
      setBusy(false);
    }
  }

  async function publish() {
    setBusy(true); setError("");
    try {
      const p = await api.publishRule(draft!);
      setMsg(`پالیسی ورژن v${p.version} شائع ہو گیا۔ نئے فیصلے اس پالیسی پر فوری نافذ ہوں گے۔ · Published version v${p.version}`);
      setSim(null);
      await loadRules();
    } catch (e) {
      setError((e as ApiError).message_en ?? "Publish failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateKey() {
    if (!newKeyName.trim()) return;
    setKeyBusy(true); setError(""); setMsg("");
    try {
      const created = await api.createApiKey(newKeyName.trim());
      setCreatedKey(created);
      setNewKeyName("");
      setCopied(false);
      await loadKeys();
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not create API key");
    } finally {
      setKeyBusy(false);
    }
  }

  async function handleRevokeKey(keyId: string) {
    setKeyBusy(true); setError("");
    try {
      await api.revokeApiKey(keyId);
      setMsg("چابی فوری طور پر منسوخ کر دی گئی ہے · API key revoked immediately.");
      await loadKeys();
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not revoke key");
    } finally {
      setKeyBusy(false);
    }
  }

  function copyKey(text: string) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  }

  const num = "w-full min-h-[50px] border-2 border-[#E2DDD3] rounded-2xl px-4 text-base bg-white text-[#17302B] focus:border-[#0F6B5A] focus:outline-none";

  return (
    <AppShell title="ایڈمن پورٹل · Policy & Gateway Administration">
      {/* Tab Switcher */}
      <div className="flex gap-2 p-1.5 bg-white rounded-2xl border border-[#E2DDD3] shadow-sm">
        <button
          onClick={() => { setTab("rules"); setError(""); }}
          type="button"
          className={`flex-1 min-h-[44px] rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition ${
            tab === "rules" ? "bg-[#0B4F43] text-white shadow" : "text-[#5B6F6A] hover:bg-slate-100"
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" /> قواعد و ڈیجیٹل ٹوئن · Rules & Simulation
        </button>
        <button
          onClick={() => { setTab("keys"); setError(""); }}
          type="button"
          className={`flex-1 min-h-[44px] rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition ${
            tab === "keys" ? "bg-[#0B4F43] text-white shadow" : "text-[#5B6F6A] hover:bg-slate-100"
          }`}
        >
          <Key className="w-4 h-4" /> پبلک ریلز API چابیاں · API Keys ({keys.length})
        </button>
      </div>

      {msg && <p className="bg-[#DDEFE9] text-[#0B4F43] border border-[#1F8A5B] rounded-2xl p-4 font-bold text-sm shadow-sm">{msg}</p>}
      {error && <p className="bg-[#FEE2E2] text-[#991B1B] border border-[#F87171] rounded-2xl p-4 font-bold text-sm shadow-sm">{error}</p>}

      {/* ==================== TAB 1: RULES & DIGITAL TWIN ==================== */}
      {tab === "rules" && (
        <div className="space-y-4 animate-fade-up">
          <Card className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#E2DDD3] pb-3">
              <span className="font-bold text-[#0B4F43]">فعال پالیسی · Active Rule Set</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowJson(!showJson)}
                  type="button"
                  className="px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-mono font-bold text-[#5B6F6A] flex items-center gap-1"
                >
                  <Code className="w-3.5 h-3.5" /> {showJson ? "Form View" : "JSON"}
                </button>
                <span className="px-3 py-1 bg-[#DDEFE9] text-[#0B4F43] rounded-full text-xs font-bold">
                  v{active.version} ({active.name})
                </span>
              </div>
            </div>

            {showJson ? (
              <pre className="bg-[#17302B] text-emerald-300 p-4 rounded-2xl text-xs overflow-x-auto font-mono">
                {JSON.stringify(draft, null, 2)}
              </pre>
            ) : (
              <>
                <label className="block">
                  <span className="font-bold text-sm text-[#17302B]">زیادہ سے زیادہ ماہانہ آمدنی · Max monthly income (PKR)</span>
                  <div className="flex gap-2 mt-1.5">
                    <button
                      type="button"
                      onClick={() => set("max_monthly_income", Math.max(0, draft.max_monthly_income - 1000))}
                      className="min-h-[50px] w-14 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] text-2xl font-bold hover:bg-[#cbe3da] transition"
                    >
                      −
                    </button>
                    <input
                      className={num}
                      type="number"
                      value={draft.max_monthly_income}
                      onChange={(e) => set("max_monthly_income", Number(e.target.value))}
                    />
                    <button
                      type="button"
                      onClick={() => set("max_monthly_income", draft.max_monthly_income + 1000)}
                      className="min-h-[50px] w-14 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] text-2xl font-bold hover:bg-[#cbe3da] transition"
                    >
                      +
                    </button>
                  </div>
                </label>

                <label className="block">
                  <span className="font-bold text-sm text-[#17302B]">خودکار منظوری کی حد · Auto-approve limit (PKR)</span>
                  <input
                    className={`${num} mt-1.5`}
                    type="number"
                    value={draft.max_auto_approve_amount}
                    onChange={(e) => set("max_auto_approve_amount", Number(e.target.value))}
                  />
                </label>

                <label className="block">
                  <span className="font-bold text-sm text-[#17302B]">کم از کم افراد خانہ · Min household size</span>
                  <input
                    className={`${num} mt-1.5`}
                    type="number"
                    value={draft.min_household_size}
                    onChange={(e) => set("min_household_size", Number(e.target.value))}
                  />
                </label>

                <label className="flex items-center gap-3 font-bold text-sm text-[#17302B] pt-1 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-5 h-5 rounded text-[#0B4F43] accent-[#0B4F43]"
                    checked={draft.requires_utility_bill}
                    onChange={(e) => set("requires_utility_bill", e.target.checked)}
                  />
                  بجلی کا بل لازمی شرط ہے · Utility bill verification required
                </label>
              </>
            )}
          </Card>

          <div className="grid grid-cols-2 gap-3 font-bold">
            <Button
              variant="secondary"
              onClick={simulate}
              disabled={busy || draftKey === JSON.stringify(active)}
              className="bg-[#0284C7] hover:bg-[#0369a1]"
            >
              <FlaskConical className="w-5 h-5" /> Test on Digital Twin
            </Button>
            <Button
              variant="primary"
              onClick={publish}
              disabled={busy || !canPublish}
            >
              <Rocket className="w-5 h-5" /> Publish Rule · شائع کریں
            </Button>
          </div>
          {!canPublish && (
            <p className="text-xs text-[#5B6F6A] text-center">پالیسی شائع کرنے سے پہلے ڈیجیٹل ٹوئن پر ٹیسٹ چلانا لازمی ہے۔</p>
          )}

          {/* Digital Twin Simulation Results with Visual SVG Bars */}
          {sim && (
            <Card className="p-5 space-y-4 border-2 border-[#0284C7] bg-[#E0F2FE]/20 animate-fade-up">
              <p className="text-lg font-bold text-[#0C4A6E]">
                ڈیجیٹل ٹوئن تجزیہ · Digital Twin Simulation (v{sim.previous_rule_version} → v{sim.draft_rule_version})
              </p>

              {/* Handcrafted Visual Bars */}
              <div className="space-y-3">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-bold text-[#17302B]">
                    <span>پہلے (Before v{sim.previous_rule_version}) منظوری کا تناسب</span>
                    <b>{pct(sim.previous_approval_rate)}</b>
                  </div>
                  <div className="h-4 bg-[#E2DDD3] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-slate-400 transition-all duration-700"
                      style={{ width: `${sim.previous_approval_rate * 100}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-bold text-[#17302B]">
                    <span>بعد میں (Projected v{sim.draft_rule_version}) منظوری کا تناسب</span>
                    <b className="text-[#1F8A5B]">{pct(sim.projected_approval_rate)}</b>
                  </div>
                  <div className="h-4 bg-[#E2DDD3] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#1F8A5B] transition-all duration-700"
                      style={{ width: `${sim.projected_approval_rate * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-[#BAE6FD] flex items-center justify-between">
                <p className={`text-base font-bold ${sim.approval_rate_delta >= 0 ? "text-[#1F8A5B]" : "text-[#B3261E]"}`}>
                  متوقع اثر · Delta: {sim.approval_rate_delta >= 0 ? "+" : ""}{pct(sim.approval_rate_delta)}
                </p>
                <span className="text-xs bg-[#E0F2FE] text-[#0369A1] font-mono font-bold px-2.5 py-1 rounded-lg">
                  {sim.total_cases_simulated} Historical Cases
                </span>
              </div>
              <p className="text-xs text-[#5B6F6A]">{sim.impact_summary}</p>
            </Card>
          )}

          {/* Version History */}
          <Card className="p-5">
            <p className="font-bold text-sm text-[#0B4F43] mb-3">ورژن ہسٹری · Policy Version History</p>
            <div className="divide-y divide-[#E2DDD3] text-xs">
              {[...versions].reverse().map((v) => (
                <div key={v.version} className="py-2.5 flex justify-between items-center">
                  <span>v{v.version} · {v.name} (آمدنی حد: Rs {v.rule_set.max_monthly_income.toLocaleString()})</span>
                  {v.is_active && <StatusBadge status="approved" labelUr="فعال" labelEn="ACTIVE" />}
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* ==================== TAB 2: PUBLIC RAILS API KEYS ==================== */}
      {tab === "keys" && (
        <div className="space-y-4 animate-fade-up">
          {/* Create New Key Card */}
          <Card className="p-5 space-y-4">
            <div>
              <p className="font-bold text-[#0B4F43] text-base">نئی پارٹنر API چابی بنائیں · Issue Public Rails Key</p>
              <p className="text-xs text-[#5B6F6A] mt-0.5">
                ریلیف پارٹنرز اور فلاحی اداروں کو پبلک ریلز (اسکیم چیک، ہیلتھ، آسک) تک براہ راست رسائی دینے کے لیے۔
              </p>
            </div>

            <div className="flex gap-2">
              <input
                className="flex-1 min-h-[48px] border-2 border-[#E2DDD3] rounded-2xl px-4 text-sm bg-white text-[#17302B] focus:border-[#0F6B5A] focus:outline-none"
                placeholder="پارٹنر کا نام درج کریں e.g. edhi-foundation"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
              />
              <Button
                variant="primary"
                onClick={handleCreateKey}
                disabled={keyBusy || !newKeyName.trim()}
              >
                {keyBusy ? "بن رہی ہے..." : "چابی بنائیں · Create"}
              </Button>
            </div>
          </Card>

          {/* Single-display API Key Warning Card */}
          {createdKey && (
            <div className="bg-[#FFFBEB] border-2 border-[#E8A33D] rounded-3xl p-5 space-y-3 shadow-lift animate-fade-up">
              <div className="flex items-center gap-2 text-[#92400E]">
                <AlertTriangle className="w-5 h-5 text-[#C77700] shrink-0" />
                <p className="font-bold text-base">
                  اہم: یہ چابی صرف ایک بار دکھائی جائے گی · Save this API key now!
                </p>
              </div>
              <p className="text-xs text-[#78350F]">
                سیکیورٹی کی خاطر یہ چابی ڈیٹا بیس میں SHA-256 ہیش ہو چکی ہے اور دوبارہ کبھی نہیں دیکھی جا سکے گی۔ اسے ابھی کاپی کر لیں۔
              </p>

              <div className="bg-white rounded-2xl p-3 border border-[#FCD34D] flex items-center justify-between gap-2 shadow-sm">
                <span className="font-mono text-xs font-bold text-[#0B4F43] break-all select-all">
                  {createdKey.key}
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => copyKey(createdKey.key)}
                  className="shrink-0"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? "کاپی ہو گئی!" : "Copy"}
                </Button>
              </div>

              <Button
                variant="neutral"
                size="sm"
                onClick={() => setCreatedKey(null)}
                className="w-full"
              >
                میں نے چابی محفوظ کر لی ہے · I have saved the key (Dismiss)
              </Button>
            </div>
          )}

          {/* List of Existing Masked Keys */}
          <Card className="p-5 space-y-3">
            <p className="font-bold text-[#0B4F43] text-sm">موجودہ پبلک ریلز چابیاں · Active Public Rails Keys</p>
            {keys.length === 0 ? (
              <p className="text-xs text-[#5B6F6A] text-center py-4">ابھی کوئی API چابی جاری نہیں کی گئی۔</p>
            ) : (
              <div className="divide-y divide-[#E2DDD3]">
                {keys.map((k) => {
                  const isRevoked = !!k.revoked_at;
                  return (
                    <div key={k.id} className="py-3 flex items-center justify-between gap-3 text-xs">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-[#17302B]">{k.name}</span>
                          <StatusBadge
                            status={isRevoked ? "revoked" : "active"}
                            labelUr={isRevoked ? "منسوخ" : "فعال"}
                            labelEn={isRevoked ? "Revoked" : "Active"}
                          />
                        </div>
                        <p className="font-mono text-[#5B6F6A]">{k.masked_key}</p>
                        <p className="text-[10px] text-[#5B6F6A]">
                          Created: {new Date(k.created_at).toLocaleDateString()}
                          {k.last_used_at && ` · Last used: ${new Date(k.last_used_at).toLocaleDateString()}`}
                        </p>
                      </div>

                      {!isRevoked && (
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleRevokeKey(k.id)}
                          disabled={keyBusy}
                        >
                          <Trash2 className="w-3.5 h-3.5" /> منسوخ · Revoke
                        </Button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      )}
    </AppShell>
  );
}
