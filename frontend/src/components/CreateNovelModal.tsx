import { useState } from "react";
import { X, Loader2 } from "lucide-react";

interface Props {
  onCreated: (novelId: string) => void;
  onClose: () => void;
}

export default function CreateNovelModal({ onCreated, onClose }: Props) {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("zh");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!title.trim()) { setError("请输入小说标题"); return; }
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch(`/api/novels?title=${encodeURIComponent(title.trim())}&language=${language}`, {
        method: "POST",
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "创建失败");
      }
      const data = await res.json();
      onCreated(data.id);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="rounded-[12px] bg-white w-[420px] shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(0,0,0,0.1)]">
          <h2 className="text-[18px] font-semibold">新建小说</h2>
          <button onClick={onClose} className="text-[#615d59] hover:text-[rgba(0,0,0,0.95)] transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-[13px] font-medium mb-1.5">小说标题</label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") handleSubmit(); }}
              placeholder="例如：骆驼祥子"
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-[13px] font-medium mb-1.5">语言</label>
            <select
              value={language}
              onChange={e => setLanguage(e.target.value)}
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
            >
              <option value="zh">中文</option>
              <option value="en">英文</option>
            </select>
          </div>

          {error && (
            <p className="rounded-[4px] bg-[#fde8e8] px-3 py-2 text-[13px] text-[#d44]">{error}</p>
          )}
        </div>

        <div className="flex justify-end gap-3 px-6 py-4 border-t border-[rgba(0,0,0,0.1)]">
          <button onClick={onClose}
            className="rounded-[4px] px-4 py-2 text-[14px] font-medium bg-[rgba(0,0,0,0.05)] hover:bg-[rgba(0,0,0,0.08)] transition-colors">
            取消
          </button>
          <button onClick={handleSubmit} disabled={submitting}
            className="rounded-[4px] px-4 py-2 text-[14px] font-semibold text-white bg-[#0075de] hover:bg-[#005bab] disabled:opacity-50 transition-colors inline-flex items-center gap-2">
            {submitting && <Loader2 size={14} className="animate-spin" />}
            创建
          </button>
        </div>
      </div>
    </div>
  );
}
