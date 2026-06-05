import { useState, useEffect } from "react";
import { Eye, EyeOff } from "lucide-react";

interface Props {
  value: string;
  maskedValue: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

function maskKey(key: string): string {
  if (!key) return "";
  if (key.length < 12) return "*****";
  return `${key.slice(0, 5)}*****${key.slice(-6)}`;
}

export default function MaskedInput({ value, maskedValue, onChange, placeholder }: Props) {
  const [showPlain, setShowPlain] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState("");

  // 当外部 value 变化时重置
  useEffect(() => {
    if (!editing) setEditValue(value);
  }, [value, editing]);

  const handleFocus = () => {
    setEditing(true);
    setEditValue(value);
    setShowPlain(true);
  };

  const handleBlur = () => {
    setEditing(false);
    onChange(editValue);
    setShowPlain(false);
  };

  const displayValue = editing
    ? editValue
    : (maskedValue || (value ? maskKey(value) : ""));

  return (
    <div className="relative">
      <input
        type={showPlain || editing ? "text" : "text"}
        value={displayValue}
        onChange={e => setEditValue(e.target.value)}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder={placeholder}
        className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 pr-16 text-[14px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
        style={!editing && value ? { color: "#615d59", letterSpacing: "0.5px" } : undefined}
      />
      <button
        type="button"
        onMouseDown={e => { e.preventDefault(); setShowPlain(!showPlain); }}
        className="absolute right-2 top-1/2 -translate-y-1/2 text-[#a39e98] hover:text-[#615d59] transition-colors"
      >
        {showPlain ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
}

export { maskKey };
