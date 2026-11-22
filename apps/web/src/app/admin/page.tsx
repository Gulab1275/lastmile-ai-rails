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
        {error ? <p className="text-rose-700 font-bold p-4 bg-rose-50 rounded-xl">{error}</p> : <p className="p-4 text-xs text-slate-500">لوڈ ہو رہا ہے...</p>}
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

  const numInput = "w-full min-h-[46px] border border-slate-300 rounded-xl px-4 text-sm bg-white text-slate-900 focus:border-[#0B4F43] focus:ring-1 focus:ring-[#0B4F43] focus:outline-none";

  return (
    <AppShell title="ایڈمن پورٹل · Policy & Gateway Administration">
      {/* Tab Switcher */}
      <div className="flex gap-2 p-1.5 bg-white rounded-xl border border-slate-200 shadow-sm">
        <button
          onClick={() => { setTab("rules"); setError(""); }}
          type="button"
          className={`flex-1 min-h-[40px] rounded-lg font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 transition ${
            tab === "rules" ? "bg-[#0B4F43] text-white shadow-sm" : "text-slate-600 hover:bg-slate-50"
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" /> قواعد و ڈیجیٹل ٹوئن · Rules
        </button>
        <button
          onClick={() => { setTab("keys"); setError(""); }}
          type="button"
          className={`flex-1 min-h-[40px] rounded-lg font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 transition ${
            tab === "keys" ? "bg-[#0B4F43] text-white shadow-sm" : "text-slate-600 hover:bg-slate-50"
          }`}
        >
          <Key className="w-4 h-4" /> پبلک ریلز API چابیاں · API Keys ({keys.length})
        </button>
      </div>

      {msg && <p className="bg-emerald-50 text-emerald-900 border border-emerald-200 rounded-xl p-3.5 font-medium text-xs">{msg}</p>}
      {error && <p className="bg-rose-50 text-rose-900 border border-rose-200 rounded-xl p-3.5 font-medium text-xs">{error}</p>}

      {/* ==================== TAB 1: RULES & SIMULATION ==================== */}
      {tab === "rules" && (
        <div className="space-y-4">
          <Card className="p-5 sm:p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <span className="font-bold text-slate-900 text-sm">فعال پالیسی · Active Rule Set</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowJson(!showJson)}
                  type="button"
                  className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-mono font-medium text-slate-700 flex items-center gap-1 border border-slate-200"
                >
                  <Code className="w-3.5 h-3.5" /> {showJson ? "Form View" : "JSON"}
                </button>
                <span className="px-2.5 py-0.5 bg-emerald-100 text-emerald-800 rounded-md text-xs font-semibold font-mono">
                  v{active.version}
                </span>
              </div>
            </div>

            {showJson ? (
              <pre className="bg-slate-900 text-emerald-400 p-4 rounded-xl text-xs overflow-x-auto font-mono">
                {JSON.stringify(draft, null, 2)}
              </pre>
            ) : (
              <div className="space-y-3.5">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-700">
                    زیادہ سے زیادہ ماہانہ آمدنی · Max monthly income (PKR)
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => set("max_monthly_income", Math.max(0, draft.max_monthly_income - 1000))}
                      className="min-h-[46px] w-12 rounded-xl bg-slate-100 text-slate-700 text-lg font-bold hover:bg-slate-200 border border-slate-300"
                    >
                      −
                    </button>
                    <input
                      className={numInput}
                      type="number"
                      value={draft.max_monthly_income}
                      onChange={(e) => set("max_monthly_income", Number(e.target.value))}
                    />
                    <button
                      type="button"
                      onClick={() => set("max_monthly_income", draft.max_monthly_income + 1000)}
                      className="min-h-[46px] w-12 rounded-xl bg-slate-100 text-slate-700 text-lg font-bold hover:bg-slate-200 border border-slate-300"
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-700">
                    خودکار منظوری کی حد · Auto-approve limit (PKR)
                  </label>
                  <input
                    className={numInput}
                    type="number"
                    value={draft.max_auto_approve_amount}
                    onChange={(e) => set("max_auto_approve_amount", Number(e.target.value))}
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-700">
                    کم از کم افراد خانہ · Min household size
                  </label>
                  <input
                    className={numInput}
                    type="number"
                    value={draft.min_household_size}
                    onChange={(e) => set("min_household_size", Number(e.target.value))}
                  />
                </div>

                <label className="flex items-center gap-2.5 font-medium text-xs text-slate-800 pt-1 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded text-[#0B4F43] accent-[#0B4F43]"
                    checked={draft.requires_utility_bill}
                    onChange={(e) => set("requires_utility_bill", e.target.checked)}
                  />
                  بجلی کا بل لازمی شرط ہے · Utility bill verification required
                </label>
              </div>
            )}
          </Card>

          <div className="grid grid-cols-2 gap-3">
            <Button
              variant="secondary"
              onClick={simulate}
              disabled={busy || draftKey === JSON.stringify(active)}
              className="bg-sky-700 hover:bg-sky-800 text-xs sm:text-sm"
            >
              <FlaskConical className="w-4 h-4" /> Test on Digital Twin
            </Button>
            <Button
              variant="primary"
              onClick={publish}
              disabled={busy || !canPublish}
              className="text-xs sm:text-sm"
            >
              <Rocket className="w-4 h-4" /> Publish Rule · شائع کریں
            </Button>
          </div>
          {!canPublish && (
            <p className="text-[11px] text-slate-500 text-center">پالیسی شائع کرنے سے پہلے ڈیجیٹل ٹوئن پر ٹیسٹ چلانا لازمی ہے۔</p>
          )}

          {/* Digital Twin Results */}
          {sim && (
            <Card className="p-5 space-y-4 border-sky-300 bg-sky-50/30">
              <p className="text-base font-bold text-sky-950 font-heading">
                ڈیجیٹل ٹوئن تجزیہ · Digital Twin Simulation (v{sim.previous_rule_version} → v{sim.draft_rule_version})
              </p>

              <div className="space-y-2.5 text-xs">
                <div className="space-y-1">
                  <div className="flex justify-between font-medium text-slate-700">
                    <span>پہلے (Before v{sim.previous_rule_version}) منظوری کا تناسب:</span>
                    <b className="font-mono">{pct(sim.previous_approval_rate)}</b>
                  </div>
                  <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-slate-400"
                      style={{ width: `${sim.previous_approval_rate * 100}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between font-medium text-slate-700">
                    <span>بعد میں (Projected v{sim.draft_rule_version}) منظوری کا تناسب:</span>
                    <b className="font-mono text-emerald-700">{pct(sim.projected_approval_rate)}</b>
                  </div>
                  <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-600"
                      style={{ width: `${sim.projected_approval_rate * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-sky-200 flex items-center justify-between text-xs">
                <p className={`font-bold ${sim.approval_rate_delta >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                  متوقع اثر · Delta: {sim.approval_rate_delta >= 0 ? "+" : ""}{pct(sim.approval_rate_delta)}
                </p>
                <span className="text-[11px] bg-sky-100 text-sky-800 font-mono font-medium px-2 py-0.5 rounded">
                  {sim.total_cases_simulated} Historical Cases
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">{sim.impact_summary}</p>
            </Card>
          )}

          {/* Version History */}
          <Card className="p-5">
            <p className="font-bold text-xs uppercase tracking-wider text-slate-500 mb-2">ورژن ہسٹری · Version History</p>
            <div className="divide-y divide-slate-100 text-xs">
              {[...versions].reverse().map((v) => (
                <div key={v.version} className="py-2.5 flex justify-between items-center">
                  <span className="text-slate-800">v{v.version} · {v.name} (آمدنی حد: Rs {v.rule_set.max_monthly_income.toLocaleString()})</span>
                  {v.is_active && <StatusBadge status="approved" labelUr="فعال" labelEn="ACTIVE" />}
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* ==================== TAB 2: API KEYS ==================== */}
      {tab === "keys" && (
        <div className="space-y-4">
          <Card className="p-5 sm:p-6 space-y-4">
            <div className="space-y-0.5">
              <p className="font-bold text-slate-900 text-sm sm:text-base">نئی پارٹنر API چابی بنائیں · Issue Public Rails Key</p>
              <p className="text-xs text-slate-500">
                ریلیف پارٹنرز اور فلاحی اداروں کو پبلک ریلز (اسکیم چیک، ہیلتھ، آسک) تک براہ راست رسائی دینے کے لیے۔
              </p>
            </div>

            <div className="flex gap-2">
              <input
                className="flex-1 min-h-[46px] border border-slate-300 rounded-xl px-4 text-sm bg-white text-slate-900 focus:border-[#0B4F43] focus:ring-1 focus:ring-[#0B4F43] focus:outline-none"
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

          {/* Single-display API Key Card */}
          {createdKey && (
            <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 space-y-3 shadow-sm">
              <div className="flex items-center gap-2 text-amber-900">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
                <p className="font-bold text-sm sm:text-base">
                  اہم: یہ چابی صرف ایک بار دکھائی جائے گی · Save API key now
                </p>
              </div>
              <p className="text-xs text-amber-800 leading-relaxed">
                سیکیورٹی کی خاطر یہ چابی ڈیٹا بیس میں SHA-256 ہیش ہو چکی ہے اور دوبارہ کبھی نہیں دیکھی جا سکے گی۔ اسے ابھی کاپی کر لیں۔
              </p>

              <div className="bg-white rounded-xl p-3 border border-amber-200 flex items-center justify-between gap-2">
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
                className="w-full text-xs"
              >
                میں نے چابی محفوظ کر لی ہے · Dismiss
              </Button>
            </div>
          )}

          {/* Keys List */}
          <Card className="p-5 space-y-3">
            <p className="font-bold text-slate-900 text-xs uppercase tracking-wider">موجودہ پبلک ریلز چابیاں · Active Keys</p>
            {keys.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-4">ابھی کوئی API چابی جاری نہیں کی گئی۔</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {keys.map((k) => {
                  const isRevoked = !!k.revoked_at;
                  return (
                    <div key={k.id} className="py-3 flex items-center justify-between gap-3 text-xs">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900">{k.name}</span>
                          <StatusBadge
                            status={isRevoked ? "revoked" : "active"}
                            labelUr={isRevoked ? "منسوخ" : "فعال"}
                            labelEn={isRevoked ? "Revoked" : "Active"}
                          />
                        </div>
                        <p className="font-mono text-slate-500">{k.masked_key}</p>
                        <p className="text-[11px] text-slate-400">
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
