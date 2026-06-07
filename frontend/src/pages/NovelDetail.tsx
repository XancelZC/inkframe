import { useEffect, useState, useRef } from "react";
import { ArrowLeft, Plus, FileText, Loader2, Trash2, X, Check, Pencil, Upload, Download } from "lucide-react";
import {
  appendImportFiles,
  collectDroppedTextFiles,
  naturalComparePath,
  textFilesFromFileList,
  type TextImportFile,
} from "../lib/importFiles";

interface Chapter {
  id: string;
  title: string;
  source_language: string | null;
  created_at: string;
  updated_at: string;
}

interface NovelDetail {
  id: string;
  title: string;
  language: string;
  created_at: string;
  updated_at: string;
  chapter_count: number;
  chapters: Chapter[];
}

interface Props {
  novelId: string;
  onBack: () => void;
  onSelectChapter: (chapterId: string) => void;
}

interface ChapterImportResult {
  created_count: number;
  failed_count: number;
  ignored_count: number;
  created_chapters: { id: string; title: string; path: string; process_error: string | null }[];
  failed_files: { path: string; reason: string }[];
}

export default function NovelDetail({ novelId, onBack, onSelectChapter }: Props) {
  const [novel, setNovel] = useState<NovelDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddChapter, setShowAddChapter] = useState(false);
  const [chapterTitle, setChapterTitle] = useState("");
  const [chapterText, setChapterText] = useState("");
  const [chapterFile, setChapterFile] = useState<File | null>(null);
  const [chapterImportFiles, setChapterImportFiles] = useState<TextImportFile[]>([]);
  const [autoProcessImported, setAutoProcessImported] = useState(false);
  const [draggingImport, setDraggingImport] = useState(false);
  const [chapterImportResult, setChapterImportResult] = useState<ChapterImportResult | null>(null);
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const [deleteTarget, setDeleteTarget] = useState<Chapter | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [editingNovelTitle, setEditingNovelTitle] = useState(false);
  const [novelTitleValue, setNovelTitleValue] = useState("");
  const [editingChapterId, setEditingChapterId] = useState<string | null>(null);
  const [chapterTitleValue, setChapterTitleValue] = useState("");

  const loadNovel = () => {
    fetch(`/api/novels/${novelId}`)
      .then(r => r.json())
      .then(d => { setNovel(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { loadNovel(); }, [novelId]);

  const handleSaveNovelTitle = async () => {
    if (!novelTitleValue.trim() || !novel) return;
    await fetch(`/api/novels/${novel.id}?title=${encodeURIComponent(novelTitleValue.trim())}`, { method: "PUT" });
    setEditingNovelTitle(false);
    loadNovel();
  };

  const handleSaveChapterTitle = async (chapterId: string) => {
    if (!chapterTitleValue.trim()) return;
    await fetch(`/api/projects/${chapterId}?title=${encodeURIComponent(chapterTitleValue.trim())}`, { method: "PUT" });
    setEditingChapterId(null);
    loadNovel();
  };

  const resetAddChapterForm = () => {
    setChapterTitle("");
    setChapterText("");
    setChapterFile(null);
    setChapterImportFiles([]);
    setAutoProcessImported(false);
    setDraggingImport(false);
    setChapterImportResult(null);
    setAddError("");
  };

  const closeAddChapter = () => {
    resetAddChapterForm();
    setShowAddChapter(false);
  };

  const setSelectedImportFiles = (entries: TextImportFile[]) => {
    const sorted = entries.sort((a, b) => naturalComparePath(a.relativePath, b.relativePath));
    setChapterImportFiles(sorted);
    setChapterFile(sorted[0]?.file ?? null);
    setChapterImportResult(null);
    if (sorted.length > 0) {
      setChapterText("");
      setAddError("");
      if (sorted.length === 1 && !chapterTitle.trim()) {
        setChapterTitle(sorted[0].file.name.replace(/\.(txt|md)$/i, ""));
      }
    } else {
      setAddError("没有找到可导入的 .txt 或 .md 文件");
    }
  };

  const handleImportDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDraggingImport(false);
    setSelectedImportFiles(await collectDroppedTextFiles(event.dataTransfer));
  };

  const handleAddChapter = async () => {
    const isBatchImport = chapterImportFiles.length > 0;
    if (!isBatchImport && !chapterTitle.trim()) { setAddError("请输入章节标题"); return; }
    if (!isBatchImport && !chapterText.trim() && !chapterFile) { setAddError("请粘贴文本或上传文件"); return; }
    setAdding(true);
    setAddError("");
    setChapterImportResult(null);
    try {
      const res = isBatchImport ? await importChapterFiles() : await createSingleChapter();
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "创建失败");
      }
      const data = await res.json();
      loadNovel();
      if (isBatchImport) {
        setChapterImportResult(data);
        if (data.failed_count === 0) {
          closeAddChapter();
        }
      } else {
        closeAddChapter();
      }
    } catch (e) {
      setAddError(e instanceof Error ? e.message : "创建失败");
    } finally {
      setAdding(false);
    }
  };

  const createSingleChapter = () => {
    const formData = new FormData();
    formData.append("title", chapterTitle.trim());
    if (chapterFile) {
      formData.append("file", chapterFile);
    } else if (chapterText.trim()) {
      formData.append("text", chapterText.trim());
    }
    return fetch(`/api/novels/${novelId}/chapters`, { method: "POST", body: formData });
  };

  const importChapterFiles = () => {
    const formData = new FormData();
    formData.append("auto_process", String(autoProcessImported));
    appendImportFiles(formData, chapterImportFiles);
    return fetch(`/api/novels/${novelId}/chapters/import`, { method: "POST", body: formData });
  };

  const handleExportYaml = async () => {
    const res = await fetch(`/api/novels/${novelId}/export`);
    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${novel?.title ?? "screenplay"}.yaml`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleDeleteChapter = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await fetch(`/api/projects/${deleteTarget.id}`, { method: "DELETE" });
      if (res.ok) {
        setDeleteTarget(null);
        loadNovel();
      }
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white text-[rgba(0,0,0,0.95)]">
        <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
          <p className="text-[16px] text-[#615d59]">加载中...</p>
        </header>
      </div>
    );
  }

  if (!novel) {
    return (
      <div className="min-h-screen bg-white text-[rgba(0,0,0,0.95)]">
        <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
          <p className="text-[16px] text-[#d44]">小说不存在</p>
        </header>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white text-[rgba(0,0,0,0.95)]">
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[1200px] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={onBack} className="inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[14px] text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-colors">
              <ArrowLeft size={16} /> 返回
            </button>
            <div className="flex items-center gap-2">
              {editingNovelTitle ? (
                <div className="flex items-center gap-2">
                  <input type="text" value={novelTitleValue} onChange={e => setNovelTitleValue(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter") handleSaveNovelTitle(); if (e.key === "Escape") setEditingNovelTitle(false); }}
                    className="rounded-[4px] border border-[#097fe8] px-2 py-1 text-[18px] font-bold outline-none" autoFocus />
                  <button onClick={handleSaveNovelTitle} className="text-[#2a9d99] hover:text-[#1a8a89]"><Check size={18} /></button>
                  <button onClick={() => setEditingNovelTitle(false)} className="text-[#a39e98] hover:text-[rgba(0,0,0,0.95)]"><X size={18} /></button>
                </div>
              ) : (
                <>
                  <h1 className="text-[22px] font-bold tracking-[-0.25px]">{novel.title}</h1>
                  <button onClick={() => { setNovelTitleValue(novel.title); setEditingNovelTitle(true); }}
                    className="text-[#a39e98] hover:text-[#615d59] transition-colors"><Pencil size={14} /></button>
                </>
              )}
              <span className="rounded-[4px] bg-[#f6f5f4] px-1.5 py-0.5 text-[11px] text-[#615d59]">
                {novel.language === "zh" ? "中文" : "英文"}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            {novel.chapters.length > 0 && (
              <button onClick={handleExportYaml}
                className="inline-flex items-center gap-2 rounded-[4px] bg-[rgba(0,0,0,0.05)] px-3 py-2 text-[14px] font-medium hover:bg-[rgba(0,0,0,0.08)] transition-all">
                <Download size={16} />
                导出全部 YAML
              </button>
            )}
            <button onClick={() => setShowAddChapter(true)}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[14px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] transition-all">
              <Plus size={16} />
              新建章节
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-6 py-8">
        {novel.chapters.length === 0 ? (
          <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-12 text-center">
            <FileText size={48} className="mx-auto mb-4 text-[#a39e98]" />
            <p className="text-[16px] text-[#615d59] mb-4">还没有章节，添加一个开始吧。</p>
            <button onClick={() => setShowAddChapter(true)}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[14px] font-semibold text-white hover:bg-[#005bab] transition-all">
              <Plus size={16} />
              新建章节
            </button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {novel.chapters.map((chapter, i) => (
              <div key={chapter.id}
                className="group rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-white p-5 shadow-[rgba(0,0,0,0.04)_0px_4px_18px,rgba(0,0,0,0.027)_0px_2.025px_7.85px,rgba(0,0,0,0.02)_0px_0.8px_2.93px,rgba(0,0,0,0.01)_0px_0.175px_1.04px] hover:shadow-[rgba(0,0,0,0.01)_0px_1px_3px,rgba(0,0,0,0.02)_0px_3px_7px,rgba(0,0,0,0.02)_0px_7px_15px,rgba(0,0,0,0.04)_0px_14px_28px,rgba(0,0,0,0.05)_0px_23px_52px] transition-shadow">
                <div onClick={() => onSelectChapter(chapter.id)} className="cursor-pointer">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 rounded-full bg-[#f2f9ff] flex items-center justify-center text-[12px] font-semibold text-[#097fe8]">
                      {i + 1}
                    </span>
                    {editingChapterId === chapter.id ? (
                      <div className="flex items-center gap-1 flex-1" onClick={e => e.stopPropagation()}>
                        <input type="text" value={chapterTitleValue} onChange={e => setChapterTitleValue(e.target.value)}
                          onKeyDown={e => { if (e.key === "Enter") handleSaveChapterTitle(chapter.id); if (e.key === "Escape") setEditingChapterId(null); }}
                          className="flex-1 rounded-[4px] border border-[#097fe8] px-1.5 py-0.5 text-[14px] font-semibold outline-none" autoFocus />
                        <button onClick={() => handleSaveChapterTitle(chapter.id)} className="text-[#2a9d99]"><Check size={14} /></button>
                        <button onClick={() => setEditingChapterId(null)} className="text-[#a39e98]"><X size={14} /></button>
                      </div>
                    ) : (
                      <h3 className="text-[16px] font-semibold flex-1 truncate">{chapter.title}</h3>
                    )}
                  </div>
                  <p className="text-[13px] text-[#a39e98]">
                    创建于 {new Date(chapter.created_at).toLocaleDateString("zh-CN")}
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-[rgba(0,0,0,0.1)] flex justify-end gap-1">
                  <button onClick={(e) => { e.stopPropagation(); setChapterTitleValue(chapter.title); setEditingChapterId(chapter.id); }}
                    className="opacity-0 group-hover:opacity-100 rounded-[4px] p-1.5 text-[#a39e98] hover:text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-all">
                    <Pencil size={12} />
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(chapter); }}
                    className="opacity-0 group-hover:opacity-100 rounded-[4px] p-1.5 text-[#a39e98] hover:text-[#d44] hover:bg-[#fde8e8] transition-all">
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* 新建章节弹窗 */}
      {showAddChapter && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={closeAddChapter}>
          <div className="rounded-[12px] bg-white w-[520px] shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(0,0,0,0.1)]">
              <h2 className="text-[18px] font-semibold">新建章节</h2>
              <button onClick={closeAddChapter} className="text-[#615d59] hover:text-[rgba(0,0,0,0.95)]">
                <X size={20} />
              </button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div className={chapterImportFiles.length > 0 ? "opacity-50" : ""}>
                <label className="block text-[13px] font-medium mb-1.5">章节标题</label>
                <input type="text" value={chapterTitle} onChange={e => setChapterTitle(e.target.value)}
                  placeholder="例如：第一章 祥子进城"
                  disabled={chapterImportFiles.length > 0}
                  className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] disabled:bg-[#f6f5f4] transition-all" autoFocus />
                {chapterImportFiles.length > 0 && (
                  <p className="mt-1 text-[12px] text-[#a39e98]">导入文件时会按文件名生成章节标题。</p>
                )}
              </div>
              <div className={chapterImportFiles.length > 0 ? "opacity-50" : ""}>
                <label className="block text-[13px] font-medium mb-1.5">小说文本</label>
                <textarea value={chapterText} onChange={e => { setChapterText(e.target.value); if (e.target.value) { setChapterFile(null); setChapterImportFiles([]); } }}
                  placeholder="粘贴章节文本..." rows={8}
                  disabled={chapterImportFiles.length > 0}
                  className="w-full rounded-[4px] border border-[#dddddd] px-3 py-2 text-[14px] outline-none focus:border-[#097fe8] disabled:bg-[#f6f5f4] transition-all resize-y" />
              </div>

              <div className="flex items-center gap-4">
                <div className="h-px flex-1 bg-[rgba(0,0,0,0.1)]" />
                <span className="text-[14px] text-[#a39e98]">或者</span>
                <div className="h-px flex-1 bg-[rgba(0,0,0,0.1)]" />
              </div>

              <div>
                <input ref={fileRef} type="file" accept=".txt,.md" multiple className="hidden"
                  onChange={e => {
                    setSelectedImportFiles(textFilesFromFileList(e.target.files ?? []));
                  }} />
                <div
                  onDragOver={(event) => {
                    event.preventDefault();
                    setDraggingImport(true);
                  }}
                  onDragLeave={() => setDraggingImport(false)}
                  onDrop={handleImportDrop}
                  className={`w-full rounded-[12px] border border-dashed p-4 text-center transition-colors ${
                    draggingImport ? "border-[#0075de] bg-[#f2f9ff]" : "border-[rgba(0,0,0,0.1)] bg-[#f6f5f4]"
                  }`}
                >
                  <Upload size={20} className="mx-auto mb-1.5 text-[#615d59]" />
                  <button
                    type="button"
                    onClick={() => fileRef.current?.click()}
                    className="rounded-[4px] bg-white px-3 py-1.5 text-[13px] font-medium text-[#615d59] hover:bg-[#ebeaea] transition-colors"
                  >
                    选择 .txt/.md 文件
                  </button>
                  <p className="mt-2 text-[12px] text-[#615d59]">也可以把文件或文件夹拖到这里</p>
                </div>
                {chapterImportFiles.length > 0 && (
                  <div className="mt-2 max-h-[120px] overflow-auto rounded-[6px] border border-[rgba(0,0,0,0.1)] bg-white">
                    {chapterImportFiles.slice(0, 20).map((entry) => (
                      <div key={entry.relativePath} className="flex items-center gap-2 px-3 py-1.5 text-[12px] text-[#615d59]">
                        <FileText size={12} className="text-[#a39e98]" />
                        <span className="truncate">{entry.relativePath}</span>
                      </div>
                    ))}
                    {chapterImportFiles.length > 20 && <p className="px-3 py-1.5 text-[12px] text-[#a39e98]">还有 {chapterImportFiles.length - 20} 个文件</p>}
                  </div>
                )}
              </div>

              {chapterImportFiles.length > 0 && (
                <label className="flex items-center gap-2 text-[13px] text-[#615d59]">
                  <input
                    type="checkbox"
                    checked={autoProcessImported}
                    onChange={(event) => setAutoProcessImported(event.target.checked)}
                    className="h-4 w-4"
                  />
                  导入后自动开始处理
                </label>
              )}

              {addError && <p className="rounded-[4px] bg-[#fde8e8] px-3 py-2 text-[13px] text-[#d44]">{addError}</p>}

              {chapterImportResult && (
                <div className="rounded-[8px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-3 text-[13px]">
                  <p className="font-medium">已导入 {chapterImportResult.created_count} 章，失败 {chapterImportResult.failed_count} 个。</p>
                  {chapterImportResult.failed_files.length > 0 && (
                    <div className="mt-2 space-y-1 text-[#d44]">
                      {chapterImportResult.failed_files.slice(0, 5).map((file) => (
                        <p key={file.path} className="truncate">{file.path}：{file.reason}</p>
                      ))}
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={closeAddChapter}
                    className="mt-3 rounded-[4px] bg-[#0075de] px-3 py-1.5 text-[13px] font-semibold text-white hover:bg-[#005bab] transition-colors"
                  >
                    完成
                  </button>
                </div>
              )}
            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-[rgba(0,0,0,0.1)]">
              <button onClick={closeAddChapter}
                className="rounded-[4px] px-4 py-2 text-[14px] font-medium bg-[rgba(0,0,0,0.05)] hover:bg-[rgba(0,0,0,0.08)] transition-colors">取消</button>
              <button onClick={handleAddChapter} disabled={adding}
                className="rounded-[4px] px-4 py-2 text-[14px] font-semibold text-white bg-[#0075de] hover:bg-[#005bab] disabled:opacity-50 transition-colors inline-flex items-center gap-2">
                {adding && <Loader2 size={14} className="animate-spin" />}
                {chapterImportFiles.length > 0 ? "导入章节" : "添加章节"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 删除章节确认 */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="rounded-[12px] bg-white p-6 w-[400px] shadow-2xl">
            <h3 className="text-[18px] font-semibold mb-2">确认删除</h3>
            <p className="text-[14px] text-[#615d59] mb-6">
              确定要删除章节「{deleteTarget.title}」吗？此操作不可撤销。
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteTarget(null)}
                className="rounded-[4px] px-4 py-2 text-[14px] font-medium bg-[rgba(0,0,0,0.05)] hover:bg-[rgba(0,0,0,0.08)] transition-colors">取消</button>
              <button onClick={handleDeleteChapter} disabled={deleting}
                className="rounded-[4px] px-4 py-2 text-[14px] font-semibold text-white bg-[#d44] hover:bg-[#b33] disabled:opacity-50 transition-colors">
                {deleting ? "删除中..." : "确认删除"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
