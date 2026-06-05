import { useState } from "react";
import { X, Loader2 } from "lucide-react";

interface Props {
  onAdd: (name: string, type: string, baseUrl: string, apiKey: string) => Promise<void>;
  onClose: () => void;
}

const PROVIDER_TYPES = [
  { value: "openai_compatible", label: "OpenAI 兼容", placeholder: "https://api.openai.com/v1" },
  { value: "anthropic", label: "Anthropic 兼容", placeholder: "https://api.anthropic.com" },
];

export default function AddProviderModal({ onAdd, onClose }: Props) {
  const [name, setName] = useState("");
  const [type, setType] = useState("openai_compatible");
  const [baseUrl, setBaseUrl] = useState("https://api.openai.com/v1");
  const [apiKey, setApiKey] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const selectedType = PROVIDER_TYPES.find(t => t.value === type);

  const handleSubmit = async () => {
    if (!name.trim()) { setError("请输入供应商名称"); return; }
    if (!baseUrl.trim()) { setError("请输入 API 地址"); return; }
    if (!apiKey.trim()) { setError("请输入 API Key"); return; }
    setSubmitting(true);
    setError("");
    try {
      await onAdd(name.trim(), type, baseUrl.trim(), apiKey.trim());
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "添加失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="rounded-[12px] bg-white w-[480px] shadow-2xl" onClick={e => e.stopPropagation()}>
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(0,0,0,0.1)]">
          <h2 className="text-[18px] font-semibold">添加供应商</h2>
          <button onClick={onClose} className="text-[#615d59] hover:text-[rgba(0,0,0,0.95)] transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* 表单 */}
        <div className="px-6 py-5 space-y-4">
          {/* 名称 */}
          <div>
            <label className="block text-[13px] font-medium mb-1.5">名称</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="例如：我的 DeepSeek、公司 OpenAI"
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
            />
          </div>

          {/* 协议类型 */}
          <div>
            <label className="block text-[13px] font-medium mb-1.5">协议类型</label>
            <select
              value={type}
              onChange={e => {
                setType(e.target.value);
                const t = PROVIDER_TYPES.find(pt => pt.value === e.target.value);
                if (t) setBaseUrl(t.placeholder);
              }}
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
            >
              {PROVIDER_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          {/* API 地址 */}
          <div>
            <label className="block text-[13px] font-medium mb-1.5">API 地址</label>
            <input
              type="text"
              value={baseUrl}
              onChange={e => setBaseUrl(e.target.value)}
              placeholder={selectedType?.placeholder}
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
            />
          </div>

          {/* API Key */}
          <div>
            <label className="block text-[13px] font-medium mb-1.5">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder={type === "anthropic" ? "sk-ant-..." : "sk-..."}
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
            />
          </div>

          {error && (
            <p className="rounded-[4px] bg-[#fde8e8] px-3 py-2 text-[13px] text-[#d44]">{error}</p>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-[rgba(0,0,0,0.1)]">
          <button onClick={onClose}
            className="rounded-[4px] px-4 py-2 text-[14px] font-medium bg-[rgba(0,0,0,0.05)] hover:bg-[rgba(0,0,0,0.08)] transition-colors">
            取消
          </button>
          <button onClick={handleSubmit} disabled={submitting}
            className="rounded-[4px] px-4 py-2 text-[14px] font-semibold text-white bg-[#0075de] hover:bg-[#005bab] disabled:opacity-50 transition-colors inline-flex items-center gap-2">
            {submitting && <Loader2 size={14} className="animate-spin" />}
            添加
          </button>
        </div>
      </div>
    </div>
  );
}
