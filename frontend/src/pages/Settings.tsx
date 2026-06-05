import { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle, XCircle, Loader2, Plus, X } from "lucide-react";

interface Props {
  onBack: () => void;
}

interface ProviderConfig {
  provider_id: string;
  base_url: string;
  model: string;
  has_api_key: boolean;
  custom_models: string;
  api_key?: string;
}

interface Provider {
  provider_id: string;
  models: string[];
}

const PROVIDER_LABELS: Record<string, string> = {
  mock: "Mock（本地测试）",
  openai_compatible: "OpenAI 兼容",
  anthropic: "Anthropic 兼容",
};

export default function Settings({ onBack }: Props) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [configs, setConfigs] = useState<Record<string, ProviderConfig>>({});
  const [activeProvider, setActiveProvider] = useState("mock");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, { success: boolean; error?: string; elapsed_seconds?: number }>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [customModelInput, setCustomModelInput] = useState<Record<string, string>>({});

  const loadConfig = () => {
    fetch("/api/models").then(r => r.json()).then((d: Provider[]) => setProviders(d)).catch(() => {});
    fetch("/api/models/config").then(r => r.json()).then((d: Record<string, unknown>) => {
      const ap = d.active_provider as string;
      setActiveProvider(ap);
      const cfgs: Record<string, ProviderConfig> = {};
      for (const [k, v] of Object.entries(d)) {
        if (k !== "active_provider" && typeof v === "object" && v !== null) {
          cfgs[k] = v as ProviderConfig;
        }
      }
      setConfigs(cfgs);
    }).catch(() => {});
  };

  useEffect(() => { loadConfig(); }, []);

  const handleSaveProvider = async (pid: string) => {
    setSaving(true);
    setSaved(false);
    try {
      const cfg = configs[pid];
      if (!cfg) return;

      await fetch("/api/models/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider_id: pid,
          api_key: cfg.api_key || undefined,
          base_url: cfg.base_url || undefined,
          model: cfg.model || undefined,
          custom_models: cfg.custom_models || undefined,
        }),
      });

      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleSetActive = async (pid: string) => {
    await fetch("/api/models/active", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider_id: pid }),
    });
    setActiveProvider(pid);
  };

  const handleTest = async (pid: string) => {
    setTesting(pid);
    setTestResult(prev => ({ ...prev, [pid]: undefined as unknown as { success: boolean; error?: string } }));
    try {
      const res = await fetch(`/api/models/test?provider_id=${pid}`, { method: "POST" });
      const data = await res.json();
      setTestResult(prev => ({ ...prev, [pid]: data }));
    } catch {
      setTestResult(prev => ({ ...prev, [pid]: { success: false, error: "请求失败" } }));
    } finally {
      setTesting(null);
    }
  };

  const updateConfig = (pid: string, field: string, value: string) => {
    setConfigs(prev => ({
      ...prev,
      [pid]: { ...prev[pid], [field]: value },
    }));
  };

  const addCustomModel = (pid: string) => {
    const input = customModelInput[pid]?.trim();
    if (!input) return;
    const cfg = configs[pid];
    if (!cfg) return;
    const existing = cfg.custom_models ? cfg.custom_models.split(",").map(s => s.trim()) : [];
    if (!existing.includes(input)) {
      existing.push(input);
      updateConfig(pid, "custom_models", existing.join(", "));
    }
    setCustomModelInput(prev => ({ ...prev, [pid]: "" }));
  };

  const removeCustomModel = (pid: string, model: string) => {
    const cfg = configs[pid];
    if (!cfg) return;
    const existing = cfg.custom_models.split(",").map(s => s.trim()).filter(m => m !== model);
    updateConfig(pid, "custom_models", existing.join(", "));
  };

  const getAvailableModels = (pid: string): string[] => {
    const provider = providers.find(p => p.provider_id === pid);
    const builtIn = provider?.models ?? [];
    const cfg = configs[pid];
    const custom = cfg?.custom_models ? cfg.custom_models.split(",").map(s => s.trim()).filter(Boolean) : [];
    return [...new Set([...builtIn, ...custom])];
  };

  return (
    <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[800px] flex items-center gap-4">
          <button onClick={onBack} className="inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[14px] text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-colors">
            <ArrowLeft size={16} /> 返回
          </button>
          <h1 className="text-[22px] font-bold tracking-[-0.25px]">LLM 设置</h1>
        </div>
      </header>

      <main className="mx-auto max-w-[800px] px-6 py-8 space-y-6">
        {/* 供应商列表 */}
        {["mock", "openai_compatible", "anthropic"].map(pid => {
          const cfg = configs[pid];
          if (!cfg) return null;
          const isActive = activeProvider === pid;
          const availableModels = getAvailableModels(pid);
          const tr = testResult[pid];

          return (
            <div key={pid} className={`rounded-[12px] border p-5 transition-colors ${isActive ? "border-[#0075de] bg-[#0075de]/[0.02]" : "border-[rgba(0,0,0,0.1)] bg-white"}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <h2 className="text-[16px] font-semibold">{PROVIDER_LABELS[pid] ?? pid}</h2>
                  {isActive && <span className="rounded-[9999px] bg-[#e6f7f6] px-2 py-0.5 text-[11px] font-semibold text-[#2a9d99]">当前使用</span>}
                </div>
                <div className="flex gap-2">
                  {!isActive && (
                    <button onClick={() => handleSetActive(pid)}
                      className="rounded-[4px] bg-[rgba(0,0,0,0.05)] px-3 py-1.5 text-[12px] font-medium hover:bg-[rgba(0,0,0,0.08)] transition-colors">
                      设为默认
                    </button>
                  )}
                  <button onClick={() => handleTest(pid)} disabled={testing === pid}
                    className="rounded-[4px] bg-[rgba(0,0,0,0.05)] px-3 py-1.5 text-[12px] font-medium hover:bg-[rgba(0,0,0,0.08)] disabled:opacity-50 transition-colors">
                    {testing === pid ? <Loader2 size={12} className="inline animate-spin mr-1" /> : null}
                    测试连接
                  </button>
                  <button onClick={() => handleSaveProvider(pid)} disabled={saving}
                    className="rounded-[4px] bg-[#0075de] px-3 py-1.5 text-[12px] font-semibold text-white hover:bg-[#005bab] disabled:opacity-50 transition-colors">
                    保存
                  </button>
                </div>
              </div>

              {/* 测试结果 */}
              {tr && (
                <div className={`mb-4 rounded-[8px] px-3 py-2 text-[13px] ${tr.success ? "bg-[#e6f7f6] text-[#2a9d99]" : "bg-[#fde8e8] text-[#d44]"}`}>
                  {tr.success ? (
                    <span className="inline-flex items-center gap-1"><CheckCircle size={14} /> 连接成功，耗时 {tr.elapsed_seconds}s</span>
                  ) : (
                    <span className="inline-flex items-center gap-1"><XCircle size={14} /> 连接失败：{tr.error}</span>
                  )}
                </div>
              )}

              {/* API Key */}
              {pid !== "mock" && (
                <div className="mb-3">
                  <label className="block text-[13px] font-medium mb-1">API Key</label>
                  <div className="relative">
                    <input
                      type={showKeys[pid] ? "text" : "password"}
                      value={cfg.api_key}
                      onChange={(e) => updateConfig(pid, "api_key", e.target.value)}
                      placeholder={cfg.has_api_key ? "已配置（留空保持不变）" : "sk-... / sk-ant-..."}
                      className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 pr-16 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
                    />
                    <button onClick={() => setShowKeys(prev => ({ ...prev, [pid]: !prev[pid] }))}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-[12px] text-[#0075de] hover:underline">
                      {showKeys[pid] ? "隐藏" : "显示"}
                    </button>
                  </div>
                </div>
              )}

              {/* API 地址 */}
              {pid !== "mock" && (
                <div className="mb-3">
                  <label className="block text-[13px] font-medium mb-1">API 地址</label>
                  <input
                    type="text"
                    value={cfg.base_url}
                    onChange={(e) => updateConfig(pid, "base_url", e.target.value)}
                    className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
                  />
                </div>
              )}

              {/* 模型选择 */}
              <div className="mb-3">
                <label className="block text-[13px] font-medium mb-1">模型</label>
                <select
                  value={cfg.model}
                  onChange={(e) => updateConfig(pid, "model", e.target.value)}
                  className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
                >
                  <option value="">请选择模型</option>
                  {availableModels.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                {/* 预设模型标签 */}
                {availableModels.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {availableModels.map(m => (
                      <button key={m} onClick={() => updateConfig(pid, "model", m)}
                        className={`rounded-[9999px] px-2.5 py-0.5 text-[11px] font-medium transition-colors ${cfg.model === m ? "bg-[#0075de] text-white" : "bg-[rgba(0,0,0,0.05)] text-[#615d59] hover:bg-[rgba(0,0,0,0.08)]"}`}>
                        {m}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* 自定义模型 */}
              {pid !== "mock" && (
                <div>
                  <label className="block text-[13px] font-medium mb-1">自定义模型</label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={customModelInput[pid] ?? ""}
                      onChange={(e) => setCustomModelInput(prev => ({ ...prev, [pid]: e.target.value }))}
                      onKeyDown={(e) => { if (e.key === "Enter") addCustomModel(pid); }}
                      placeholder="输入模型名称，按回车添加"
                      className="flex-1 rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] transition-all"
                    />
                    <button onClick={() => addCustomModel(pid)}
                      className="rounded-[4px] bg-[rgba(0,0,0,0.05)] px-3 py-2 hover:bg-[rgba(0,0,0,0.08)] transition-colors">
                      <Plus size={14} />
                    </button>
                  </div>
                  {/* 已添加的自定义模型 */}
                  {cfg.custom_models && cfg.custom_models.split(",").map(s => s.trim()).filter(Boolean).map(m => (
                    <span key={m} className="inline-flex items-center gap-1 rounded-[9999px] bg-[#f2f9ff] px-2.5 py-0.5 text-[11px] font-medium text-[#097fe8] mr-1.5 mb-1.5">
                      {m}
                      <button onClick={() => removeCustomModel(pid, m)} className="hover:text-[#d44]">
                        <X size={10} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {saved && (
          <div className="fixed bottom-6 right-6 rounded-[8px] bg-[#e6f7f6] px-4 py-2 text-[14px] text-[#2a9d99] shadow-lg flex items-center gap-2">
            <CheckCircle size={16} /> 配置已保存
          </div>
        )}
      </main>
    </div>
  );
}
