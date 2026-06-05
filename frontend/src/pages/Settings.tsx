import { useEffect, useState } from "react";
import { ArrowLeft, Save, CheckCircle } from "lucide-react";

interface Props {
  onBack: () => void;
}

interface ModelConfig {
  provider_id: string;
  base_url: string;
  model: string;
  has_api_key: boolean;
}

interface Provider {
  provider_id: string;
  models: string[];
}

export default function Settings({ onBack }: Props) {
  const [config, setConfig] = useState<ModelConfig | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("https://api.openai.com/v1");
  const [model, setModel] = useState("gpt-4o-mini");
  const [providerId, setProviderId] = useState("mock");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    fetch("/api/models").then(r => r.json()).then((d: Provider[]) => {
      setProviders(d);
    }).catch(() => {});

    fetch("/api/models/config").then(r => r.json()).then((d: ModelConfig) => {
      setConfig(d);
      setProviderId(d.provider_id);
      setBaseUrl(d.base_url);
      setModel(d.model);
    }).catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const body: Record<string, string> = {
        provider_id: providerId,
        base_url: baseUrl,
        model: model,
      };
      if (apiKey) {
        body.api_key = apiKey;
      }

      const res = await fetch("/api/models/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } finally {
      setSaving(false);
    }
  };

  const currentProvider = providers.find(p => p.provider_id === providerId);

  return (
    <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[720px] flex items-center gap-4">
          <button
            onClick={onBack}
            className="inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[14px] text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-colors"
          >
            <ArrowLeft size={16} />
            返回
          </button>
          <h1 className="text-[22px] font-bold tracking-[-0.25px]">LLM 设置</h1>
        </div>
      </header>

      <main className="mx-auto max-w-[720px] px-6 py-8">
        <div className="space-y-6">
          {/* Provider 选择 */}
          <div>
            <label className="block text-[14px] font-medium mb-1">模型供应商</label>
            <select
              value={providerId}
              onChange={(e) => {
                setProviderId(e.target.value);
                // 切换到 openai_compatible 时自动填入默认 URL
                if (e.target.value === "openai_compatible") {
                  setBaseUrl("https://api.openai.com/v1");
                  setModel("gpt-4o-mini");
                }
              }}
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[16px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
            >
              {providers.map(p => (
                <option key={p.provider_id} value={p.provider_id}>
                  {p.provider_id === "mock" ? "Mock（本地测试，无需 API Key）" :
                   p.provider_id === "openai_compatible" ? "OpenAI 兼容（OpenAI / 国内模型）" :
                   p.provider_id}
                </option>
              ))}
            </select>
            <p className="text-[12px] text-[#a39e98] mt-1">
              {providerId === "mock"
                ? "返回确定性 JSON，用于开发和测试，不需要 API Key。"
                : "使用真实 LLM 进行角色提取和场景合成。支持 OpenAI 及所有 OpenAI 兼容接口。"}
            </p>
          </div>

          {/* API Key（仅 openai_compatible） */}
          {providerId === "openai_compatible" && (
            <div>
              <label className="block text-[14px] font-medium mb-1">API Key</label>
              <div className="relative">
                <input
                  type={showApiKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={config?.has_api_key ? "已配置（留空保持不变）" : "sk-..."}
                  className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 pr-20 text-[16px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
                />
                <button
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-[12px] text-[#0075de] hover:underline"
                >
                  {showApiKey ? "隐藏" : "显示"}
                </button>
              </div>
              <p className="text-[12px] text-[#a39e98] mt-1">
                仅保存在服务器内存中，重启后需重新配置。如需持久化，请设置环境变量 OPENAI_API_KEY。
              </p>
            </div>
          )}

          {/* Base URL（仅 openai_compatible） */}
          {providerId === "openai_compatible" && (
            <div>
              <label className="block text-[14px] font-medium mb-1">API 地址</label>
              <input
                type="text"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://api.openai.com/v1"
                className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[16px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
              />
              <p className="text-[12px] text-[#a39e98] mt-1">
                OpenAI 默认 https://api.openai.com/v1。国内模型填对应的兼容地址。
              </p>
            </div>
          )}

          {/* 模型选择 */}
          {providerId === "openai_compatible" && (
            <div>
              <label className="block text-[14px] font-medium mb-1">模型</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="gpt-4o-mini"
                  className="flex-1 rounded-[4px] border border-[#dddddd] px-3 py-2 text-[16px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
                />
              </div>
              {currentProvider && currentProvider.models.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {currentProvider.models.map(m => (
                    <button
                      key={m}
                      onClick={() => setModel(m)}
                      className={`rounded-[9999px] px-3 py-1 text-[12px] font-medium transition-colors ${
                        model === m ? "bg-[#0075de] text-white" : "bg-[rgba(0,0,0,0.05)] text-[#615d59] hover:bg-[rgba(0,0,0,0.08)]"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 保存按钮 */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-6 py-2.5 text-[16px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] disabled:opacity-50 transition-all"
            >
              <Save size={16} />
              {saving ? "保存中..." : "保存配置"}
            </button>
            {saved && (
              <span className="inline-flex items-center gap-1 text-[14px] text-[#2a9d99]">
                <CheckCircle size={14} />
                已保存
              </span>
            )}
          </div>

          {/* 当前状态 */}
          {config && (
            <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-4">
              <h3 className="text-[14px] font-semibold mb-2">当前配置</h3>
              <div className="space-y-1 text-[14px] text-[#615d59]">
                <p>供应商：<span className="font-medium text-[rgba(0,0,0,0.95)]">{config.provider_id}</span></p>
                {config.provider_id === "openai_compatible" && (
                  <>
                    <p>API 地址：<span className="font-medium text-[rgba(0,0,0,0.95)]">{config.base_url}</span></p>
                    <p>模型：<span className="font-medium text-[rgba(0,0,0,0.95)]">{config.model}</span></p>
                    <p>API Key：<span className="font-medium text-[rgba(0,0,0,0.95)]">{config.has_api_key ? "已配置" : "未配置"}</span></p>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
