import { useState, useRef, useEffect } from "react";
import { ChevronDown, Search, Plus } from "lucide-react";

interface Props {
  models: string[];
  value: string;
  onChange: (model: string) => void;
  onAddCustom?: (model: string) => void;
  placeholder?: string;
}

export default function ModelCombobox({ models, value, onChange, onAddCustom, placeholder = "选择模型" }: Props) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [customInput, setCustomInput] = useState("");
  const [showCustom, setShowCustom] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 点击外部关闭
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
        setShowCustom(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // 按前缀分组
  const filtered = models.filter(m => m.toLowerCase().includes(search.toLowerCase()));

  const grouped: Record<string, string[]> = {};
  for (const m of filtered) {
    // 按第一个 "-" 或 "." 前的前缀分组
    const match = m.match(/^([a-zA-Z0-9]+[-.])/);
    const group = match ? match[1].replace(/[-.]$/, "") : "其他";
    if (!grouped[group]) grouped[group] = [];
    grouped[group].push(m);
  }
  const groups = Object.entries(grouped);
  const showGroups = groups.length > 1;

  const handleSelect = (m: string) => {
    onChange(m);
    setOpen(false);
    setSearch("");
  };

  const handleAddCustom = () => {
    const trimmed = customInput.trim();
    if (trimmed && onAddCustom) {
      onAddCustom(trimmed);
      onChange(trimmed);
    }
    setCustomInput("");
    setShowCustom(false);
    setOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      {/* 触发器 */}
      <button
        type="button"
        onClick={() => { setOpen(!open); setTimeout(() => inputRef.current?.focus(), 0); }}
        className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] text-left outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all flex items-center justify-between"
      >
        <span className={value ? "text-[rgba(0,0,0,0.95)]" : "text-[#a39e98]"}>{value || placeholder}</span>
        <ChevronDown size={14} className={`text-[#615d59] transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {/* 下拉面板 */}
      {open && (
        <div className="absolute top-full left-0 right-0 mt-1 rounded-[8px] border border-[rgba(0,0,0,0.1)] bg-white shadow-[rgba(0,0,0,0.1)_0px_4px_12px] z-50 max-h-[320px] flex flex-col">
          {/* 搜索框 */}
          <div className="flex items-center gap-2 px-3 py-2 border-b border-[rgba(0,0,0,0.1)]">
            <Search size={14} className="text-[#a39e98] flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="搜索模型..."
              className="flex-1 text-[13px] outline-none bg-transparent"
            />
          </div>

          {/* 模型列表 */}
          <div className="overflow-y-auto flex-1">
            {models.length === 0 && !showCustom ? (
              <div className="px-3 py-4 text-center text-[13px] text-[#a39e98]">
                暂无模型，请先获取
              </div>
            ) : filtered.length === 0 && !showCustom ? (
              <div className="px-3 py-4 text-center text-[13px] text-[#a39e98]">
                无匹配模型
              </div>
            ) : showGroups ? (
              groups.map(([group, items]) => (
                <div key={group}>
                  <div className="px-3 py-1.5 text-[11px] font-semibold text-[#a39e98] uppercase bg-[#f6f5f4]">
                    {group}
                  </div>
                  {items.map(m => (
                    <button key={m} onClick={() => handleSelect(m)}
                      className={`w-full text-left px-3 py-2 text-[13px] hover:bg-[#f6f5f4] transition-colors ${m === value ? "bg-[#0075de]/10 text-[#0075de] font-medium" : ""}`}>
                      {m}
                    </button>
                  ))}
                </div>
              ))
            ) : (
              filtered.map(m => (
                <button key={m} onClick={() => handleSelect(m)}
                  className={`w-full text-left px-3 py-2 text-[13px] hover:bg-[#f6f5f4] transition-colors ${m === value ? "bg-[#0075de]/10 text-[#0075de] font-medium" : ""}`}>
                  {m}
                </button>
              ))
            )}
          </div>

          {/* 手动输入 */}
          <div className="border-t border-[rgba(0,0,0,0.1)]">
            {showCustom ? (
              <div className="flex items-center gap-2 px-3 py-2">
                <input
                  type="text"
                  value={customInput}
                  onChange={e => setCustomInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter") handleAddCustom(); }}
                  placeholder="输入模型 ID"
                  className="flex-1 text-[13px] outline-none bg-transparent"
                  autoFocus
                />
                <button onClick={handleAddCustom}
                  className="rounded-[4px] px-2 py-1 text-[12px] font-medium text-[#0075de] hover:bg-[#f2f9ff] transition-colors">
                  确认
                </button>
              </div>
            ) : (
              <button onClick={() => setShowCustom(true)}
                className="w-full flex items-center gap-2 px-3 py-2 text-[13px] text-[#0075de] hover:bg-[#f2f9ff] transition-colors">
                <Plus size={14} />
                手动输入模型 ID
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
