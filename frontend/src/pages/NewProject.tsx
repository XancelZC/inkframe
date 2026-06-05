import { useState, useRef } from "react";
import { ArrowLeft, Upload } from "lucide-react";

interface Props {
  onBack: () => void;
  onCreated: (projectId: string) => void;
}

export default function NewProject({ onBack, onCreated }: Props) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [language, setLanguage] = useState<"auto" | "zh" | "en">("auto");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError("Title is required");
      return;
    }
    if (!text.trim() && !file) {
      setError("Please paste text or upload a file");
      return;
    }

    setSubmitting(true);
    setError(null);

    const formData = new FormData();
    formData.append("title", title.trim());
    if (language !== "auto") {
      formData.append("source_language", language);
    }
    if (file) {
      formData.append("file", file);
    } else if (text.trim()) {
      formData.append("text", text.trim());
    }

    try {
      const res = await fetch("/api/projects", { method: "POST", body: formData });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to create project");
      }
      const data = await res.json();
      onCreated(data.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[1200px] flex items-center gap-4">
          <button
            onClick={onBack}
            className="inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[14px] text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-colors"
          >
            <ArrowLeft size={16} />
            Back
          </button>
          <h1 className="text-[22px] font-bold tracking-[-0.25px]">New Project</h1>
        </div>
      </header>

      <main className="mx-auto max-w-[720px] px-6 py-8">
        <div className="space-y-6">
          {/* Title */}
          <div>
            <label className="block text-[14px] font-medium mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="My Novel"
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[16px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
            />
          </div>

          {/* Language */}
          <div>
            <label className="block text-[14px] font-medium mb-1">Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as "auto" | "zh" | "en")}
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[16px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all"
            >
              <option value="auto">Auto-detect</option>
              <option value="zh">Chinese</option>
              <option value="en">English</option>
            </select>
          </div>

          {/* Text input */}
          <div>
            <label className="block text-[14px] font-medium mb-1">Novel Text</label>
            <textarea
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                if (e.target.value) setFile(null);
              }}
              placeholder="Paste your novel text here..."
              rows={12}
              className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[16px] outline-none focus:border-[#097fe8] focus:shadow-[0_0_0_2px_rgba(9,127,232,0.15)] transition-all resize-y"
            />
          </div>

          {/* Divider */}
          <div className="flex items-center gap-4">
            <div className="h-px flex-1 bg-[rgba(0,0,0,0.1)]" />
            <span className="text-[14px] text-[#a39e98]">or</span>
            <div className="h-px flex-1 bg-[rgba(0,0,0,0.1)]" />
          </div>

          {/* File upload */}
          <div>
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.md"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0] ?? null;
                setFile(f);
                if (f) setText("");
              }}
            />
            <button
              onClick={() => fileRef.current?.click()}
              className="w-full rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-6 text-center hover:bg-[#ebeaea] transition-colors"
            >
              <Upload size={24} className="mx-auto mb-2 text-[#615d59]" />
              <p className="text-[16px] text-[#615d59]">
                {file ? file.name : "Upload a .txt file"}
              </p>
            </button>
          </div>

          {/* Error */}
          {error && (
            <p className="rounded-[4px] bg-[#fde8e8] px-3 py-2 text-[14px] text-[#d44]">
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full rounded-[4px] bg-[#0075de] px-4 py-3 text-[16px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] disabled:opacity-50 transition-all"
          >
            {submitting ? "Creating..." : "Create Project"}
          </button>
        </div>
      </main>
    </div>
  );
}
