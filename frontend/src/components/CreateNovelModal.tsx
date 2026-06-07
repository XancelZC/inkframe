import { useRef, useState } from "react";
import { X, Loader2, Upload, FileText } from "lucide-react";
import {
  appendImportFiles,
  collectDroppedTextFiles,
  naturalComparePath,
  textFilesFromFileList,
  type TextImportFile,
} from "../lib/importFiles";

interface Props {
  onCreated: (novelId: string) => void;
  onClose: () => void;
}

interface ImportResult {
  novel: { id: string; title: string };
  created_count: number;
  failed_count: number;
  ignored_count: number;
  created_chapters: { id: string; title: string; path: string; process_error: string | null }[];
  failed_files: { path: string; reason: string }[];
}

export default function CreateNovelModal({ onCreated, onClose }: Props) {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("zh");
  const [files, setFiles] = useState<TextImportFile[]>([]);
  const [autoProcess, setAutoProcess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const setSelectedFiles = (entries: TextImportFile[]) => {
    setFiles(entries.sort((a, b) => naturalComparePath(a.relativePath, b.relativePath)));
    setImportResult(null);
    setError(entries.length ? "" : "没有找到可导入的 .txt 或 .md 文件");
  };

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDragging(false);
    setSelectedFiles(await collectDroppedTextFiles(event.dataTransfer));
  };

  const handleSubmit = async () => {
    if (!title.trim()) { setError("请输入小说标题"); return; }
    setSubmitting(true);
    setError("");
    setImportResult(null);
    try {
      const res = files.length > 0
        ? await importNovel()
        : await fetch(`/api/novels?title=${encodeURIComponent(title.trim())}&language=${language}`, {
            method: "POST",
          });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "创建失败");
      }
      const data = await res.json();
      if (files.length > 0) {
        setImportResult(data);
        if (data.failed_count === 0) {
          onCreated(data.novel.id);
          onClose();
        }
      } else {
        onCreated(data.id);
        onClose();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  const importNovel = () => {
    const formData = new FormData();
    formData.append("title", title.trim());
    formData.append("language", language);
    formData.append("auto_process", String(autoProcess));
    appendImportFiles(formData, files);
    return fetch("/api/novels/import", { method: "POST", body: formData });
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

          <div>
            <label className="block text-[13px] font-medium mb-1.5">导入文本</label>
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.md"
              multiple
              className="hidden"
              onChange={(event) => setSelectedFiles(textFilesFromFileList(event.target.files ?? []))}
            />
            <div
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              className={`rounded-[8px] border border-dashed p-4 text-center transition-colors ${
                dragging ? "border-[#0075de] bg-[#f2f9ff]" : "border-[#dddddd] bg-[#f6f5f4]"
              }`}
            >
              <Upload size={22} className="mx-auto mb-2 text-[#615d59]" />
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="rounded-[4px] bg-white px-3 py-1.5 text-[13px] font-medium text-[#615d59] hover:bg-[#ebeaea] transition-colors"
              >
                选择 .txt/.md 文件
              </button>
              <p className="mt-2 text-[12px] text-[#615d59]">也可以把文件或文件夹拖到这里</p>
            </div>
            {files.length > 0 && (
              <div className="mt-2 max-h-[120px] overflow-auto rounded-[6px] border border-[rgba(0,0,0,0.1)] bg-white">
                {files.slice(0, 20).map((entry) => (
                  <div key={entry.relativePath} className="flex items-center gap-2 px-3 py-1.5 text-[12px] text-[#615d59]">
                    <FileText size={12} className="text-[#a39e98]" />
                    <span className="truncate">{entry.relativePath}</span>
                  </div>
                ))}
                {files.length > 20 && <p className="px-3 py-1.5 text-[12px] text-[#a39e98]">还有 {files.length - 20} 个文件</p>}
              </div>
            )}
          </div>

          {files.length > 0 && (
            <label className="flex items-center gap-2 text-[13px] text-[#615d59]">
              <input
                type="checkbox"
                checked={autoProcess}
                onChange={(event) => setAutoProcess(event.target.checked)}
                className="h-4 w-4"
              />
              导入后自动开始处理
            </label>
          )}

          {error && (
            <p className="rounded-[4px] bg-[#fde8e8] px-3 py-2 text-[13px] text-[#d44]">{error}</p>
          )}

          {importResult && (
            <div className="rounded-[8px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-3 text-[13px]">
              <p className="font-medium">已导入 {importResult.created_count} 章，失败 {importResult.failed_count} 个。</p>
              {importResult.failed_files.length > 0 && (
                <div className="mt-2 space-y-1 text-[#d44]">
                  {importResult.failed_files.slice(0, 5).map((file) => (
                    <p key={file.path} className="truncate">{file.path}：{file.reason}</p>
                  ))}
                </div>
              )}
              <button
                type="button"
                onClick={() => {
                  onCreated(importResult.novel.id);
                  onClose();
                }}
                className="mt-3 rounded-[4px] bg-[#0075de] px-3 py-1.5 text-[13px] font-semibold text-white hover:bg-[#005bab] transition-colors"
              >
                打开小说
              </button>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 px-6 py-4 border-t border-[rgba(0,0,0,0.1)]">
          <button onClick={onClose}
            className="rounded-[4px] px-4 py-2 text-[14px] font-medium bg-[rgba(0,0,0,0.05)] hover:bg-[rgba(0,0,0,0.08)] transition-colors">
            取消
          </button>
          <button onClick={handleSubmit} disabled={submitting || importResult !== null}
            className="rounded-[4px] px-4 py-2 text-[14px] font-semibold text-white bg-[#0075de] hover:bg-[#005bab] disabled:opacity-50 transition-colors inline-flex items-center gap-2">
            {submitting && <Loader2 size={14} className="animate-spin" />}
            {files.length > 0 ? "创建并导入" : "创建"}
          </button>
        </div>
      </div>
    </div>
  );
}
