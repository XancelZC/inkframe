import { useEffect, useState } from "react";
import { ArrowLeft, Plus, Trash2, CheckCircle, XCircle, Loader2, RefreshCw, Star } from "lucide-react";
import AddProviderModal from "../components/AddProviderModal";
import ModelCombobox from "../components/ModelCombobox";
import MaskedInput from "../components/MaskedInput";

interface Props {
  onBack: () => void;
}

interface Provider {
  id: string;
  name: string;
  type: string;
  base_url: string;
  api_key: string;
  api_key_masked: string;
  has_api_key: boolean;
  model: string;
  models: string[];
}

const TYPE_LABELS: Record<string, string> = {
  mock: "Mock",
  openai_compatible: "OpenAI 兼容",
  anthropic: "Anthropic 兼容",
};

export default function Settings({ onBack }: Props) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [activeId, setActiveId] = useState("mock");
  const [showAddModal, setShowAddModal] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, { success: boolean; error?: string; elapsed_seconds?: number }>>({});
  const [fetching, setFetching] = useState<string | null>(null);
  const [fetchResult, setFetchResult] = useState<Record<string, { success: boolean; error?: string; note?: string }>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Provider | null>(null);

  const loadConfig = () => {
    fetch("/api/models/config").then(r => r.json()).then(d => {
      setProviders(d.providers || []);
      setActiveId(d.active_provider_id || "mock");
      // 默认展开 active provider
      if (!expandedId) setExpandedId(d.active_provider_id || "mock");
    }).catch(() => {});
  };

  useEffect(() => { loadConfig(); }, []);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  // ── 添加供应商 ──────────────────────────────────────────────────
  const handleAdd = async (name: string, type: string, baseUrl: string, apiKey: string) => {
    const res = await fetch("/api/models", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, type, base_url: baseUrl, api_key: apiKey }),
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    loadConfig();
    setExpandedId(data.id);
    showToast("供应商已添加");
  };

  // ── 更新供应商 ──────────────────────────────────────────────────
  const handleUpdate = async (pid: string, updates: Partial<Provider>) => {
    setSaving(pid);
    try {
      await fetch(`/api/models/${pid}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      loadConfig();
      showToast("已保存");
    } finally {
      setSaving(null);
    }
  };

  // ── 删除供应商 ──────────────────────────────────────────────────
  const handleDelete = async () => {
    if (!deleteTarget) return;
    await fetch(`/api/models/${deleteTarget.id}`, { method: "DELETE" });
    setDeleteTarget(null);
    loadConfig();
    showToast("已删除");
  };

  // ── 设为默认 ────────────────────────────────────────────────────
  const handleSetActive = async (pid: string) => {
    await fetch(`/api/models/${pid}/active`, { method: "PUT" });
    setActiveId(pid);
    showToast("已设为默认");
  };

  // ── 测试连接 ────────────────────────────────────────────────────
  const handleTest = async (pid: string) => {
    setTesting(pid);
    setTestResult(prev => ({ ...prev, [pid]: undefined as never }));
    try {
      const res = await fetch(`/api/models/${pid}/test`, { method: "POST" });
      const data = await res.json();
      setTestResult(prev => ({ ...prev, [pid]: data }));
    } catch {
      setTestResult(prev => ({ ...prev, [pid]: { success: false, error: "请求失败" } }));
    } finally {
      setTesting(null);
    }
  };

  // ── 获取模型 ────────────────────────────────────────────────────
  const handleFetch = async (pid: string) => {
    setFetching(pid);
    setFetchResult(prev => ({ ...prev, [pid]: undefined as never }));
    try {
      const res = await fetch(`/api/models/${pid}/fetch`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        setFetchResult(prev => ({ ...prev, [pid]: { success: true, note: data.note } }));
        loadConfig();
      } else {
        setFetchResult(prev => ({ ...prev, [pid]: { success: false, error: data.error } }));
      }
    } catch {
      setFetchResult(prev => ({ ...prev, [pid]: { success: false, error: "请求失败" } }));
    } finally {
      setFetching(null);
    }
  };

  // ── 渲染 ────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[800px] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={onBack} className="inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[14px] text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-colors">
              <ArrowLeft size={16} /> 返回
            </button>
            <h1 className="text-[22px] font-bold tracking-[-0.25px]">LLM 设置</h1>
          </div>
          <button onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[14px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] transition-all">
            <Plus size={16} />
            添加供应商
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-[800px] px-6 py-8 space-y-4">
        {providers.map(provider => {
          const isActive = activeId === provider.id;
          const isExpanded = expandedId === provider.id;
          const tr = testResult[provider.id];
          const fr = fetchResult[provider.id];

          return (
            <div key={provider.id}
              className={`rounded-[12px] border transition-colors ${isActive ? "border-[#0075de] bg-[#0075de]/[0.02]" : "border-[rgba(0,0,0,0.1)] bg-white"}`}>

              {/* 卡片头部 */}
              <div className="flex items-center justify-between px-5 py-4 cursor-pointer"
                onClick={() => setExpandedId(isExpanded ? null : provider.id)}>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[16px] font-semibold">{provider.name}</span>
                    <span className="rounded-[4px] bg-[#f6f5f4] px-1.5 py-0.5 text-[11px] text-[#615d59]">
                      {TYPE_LABELS[provider.type] ?? provider.type}
                    </span>
                  </div>
                  {isActive && (
                    <span className="inline-flex items-center gap-1 rounded-[9999px] bg-[#e6f7f6] px-2 py-0.5 text-[11px] font-semibold text-[#2a9d99]">
                      <Star size={10} /> 默认
                    </span>
                  )}
                  {provider.model && (
                    <span className="text-[13px] text-[#a39e98]">{provider.model}</span>
                  )}
                </div>
                <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                  {!isActive && provider.type !== "mock" && (
                    <button onClick={() => handleSetActive(provider.id)}
                      className="rounded-[4px] px-2 py-1 text-[12px] text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-colors">
                      设为默认
                    </button>
                  )}
                  {provider.type !== "mock" && (
                    <button onClick={() => setDeleteTarget(provider)}
                      className="rounded-[4px] p-1.5 text-[#a39e98] hover:text-[#d44] hover:bg-[#fde8e8] transition-colors">
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>

              {/* 展开内容 */}
              {isExpanded && (
                <div className="px-5 pb-5 space-y-4 border-t border-[rgba(0,0,0,0.1)] pt-4">
                  {/* Mock 供应商简化显示 */}
                  {provider.type === "mock" ? (
                    <p className="text-[14px] text-[#615d59]">
                      Mock 供应商返回确定性 JSON，用于开发和测试，无需配置。
                    </p>
                  ) : (
                    <>
                      {/* 名称 */}
                      <div>
                        <label className="block text-[13px] font-medium mb-1.5">名称</label>
                        <input
                          type="text"
                          value={provider.name}
                          onChange={e => handleUpdate(provider.id, { name: e.target.value })}
                          className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
                        />
                      </div>

                      {/* API 地址 */}
                      <div>
                        <label className="block text-[13px] font-medium mb-1.5">API 地址</label>
                        <input
                          type="text"
                          value={provider.base_url}
                          onChange={e => handleUpdate(provider.id, { base_url: e.target.value })}
                          className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
                        />
                      </div>

                      {/* API Key */}
                      <div>
                        <label className="block text-[13px] font-medium mb-1.5">API Key</label>
                        <MaskedInput
                          value={provider.api_key}
                          maskedValue={provider.api_key_masked}
                          onChange={v => handleUpdate(provider.id, { api_key: v })}
                          placeholder="sk-..."
                        />
                      </div>

                      {/* 模型选择 */}
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <label className="text-[13px] font-medium">模型</label>
                          <button onClick={() => handleFetch(provider.id)} disabled={fetching === provider.id}
                            className="inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[12px] text-[#0075de] hover:bg-[#f2f9ff] disabled:opacity-50 transition-colors">
                            {fetching === provider.id ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                            获取模型
                          </button>
                        </div>

                        {/* fetch 结果 */}
                        {fr && (
                          <div className={`mb-2 rounded-[4px] px-2 py-1 text-[12px] ${fr.success ? "bg-[#e6f7f6] text-[#2a9d99]" : "bg-[#fde8e8] text-[#d44]"}`}>
                            {fr.success ? `获取到 ${provider.models.length} 个模型` : `获取失败：${fr.error}`}
                          </div>
                        )}

                        <ModelCombobox
                          models={provider.models}
                          value={provider.model}
                          onChange={m => handleUpdate(provider.id, { model: m })}
                          onAddCustom={m => {
                            const existing = provider.models || [];
                            if (!existing.includes(m)) {
                              handleUpdate(provider.id, { models: [...existing, m], model: m });
                            } else {
                              handleUpdate(provider.id, { model: m });
                            }
                          }}
                          placeholder="选择模型"
                        />
                      </div>

                      {/* 操作按钮 */}
                      <div className="flex items-center gap-3 pt-2">
                        <button onClick={() => handleTest(provider.id)} disabled={testing === provider.id}
                          className="rounded-[4px] bg-[rgba(0,0,0,0.05)] px-4 py-2 text-[13px] font-medium hover:bg-[rgba(0,0,0,0.08)] disabled:opacity-50 transition-colors inline-flex items-center gap-1.5">
                          {testing === provider.id ? <Loader2 size={14} className="animate-spin" /> : null}
                          测试连接
                        </button>
                        {saving === provider.id && (
                          <span className="text-[12px] text-[#a39e98]">保存中...</span>
                        )}
                      </div>

                      {/* 测试结果 */}
                      {tr && (
                        <div className={`rounded-[8px] px-3 py-2 text-[13px] ${tr.success ? "bg-[#e6f7f6] text-[#2a9d99]" : "bg-[#fde8e8] text-[#d44]"}`}>
                          {tr.success ? (
                            <span className="inline-flex items-center gap-1"><CheckCircle size={14} /> 连接成功，耗时 {tr.elapsed_seconds}s</span>
                          ) : (
                            <span className="inline-flex items-center gap-1"><XCircle size={14} /> 连接失败：{tr.error}</span>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </main>

      {/* 添加弹窗 */}
      {showAddModal && (
        <AddProviderModal
          onAdd={handleAdd}
          onClose={() => setShowAddModal(false)}
        />
      )}

      {/* 删除确认 */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="rounded-[12px] bg-white p-6 w-[400px] shadow-2xl">
            <h3 className="text-[18px] font-semibold mb-2">确认删除</h3>
            <p className="text-[14px] text-[#615d59] mb-6">
              确定要删除供应商「{deleteTarget.name}」吗？
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteTarget(null)}
                className="rounded-[4px] px-4 py-2 text-[14px] font-medium bg-[rgba(0,0,0,0.05)] hover:bg-[rgba(0,0,0,0.08)] transition-colors">
                取消
              </button>
              <button onClick={handleDelete}
                className="rounded-[4px] px-4 py-2 text-[14px] font-semibold text-white bg-[#d44] hover:bg-[#b33] transition-colors">
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 rounded-[8px] bg-[#e6f7f6] px-4 py-2 text-[14px] text-[#2a9d99] shadow-lg flex items-center gap-2 z-50">
          <CheckCircle size={16} /> {toast}
        </div>
      )}
    </div>
  );
}
