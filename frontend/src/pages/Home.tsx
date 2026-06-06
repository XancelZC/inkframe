import { useEffect, useState } from "react";
import { Plus, Settings, Search, Trash2, X, FolderOpen, ChevronRight, ChevronDown, FileText, ArrowUpDown } from "lucide-react";

interface NovelSummary {
  id: string;
  title: string;
  language: string;
  created_at: string;
  updated_at: string;
  chapter_count: number;
  chapters: Chapter[];
}

interface Chapter {
  id: string;
  title: string;
  created_at: string;
}

interface NovelWithChapters extends NovelSummary {
  chapters: Chapter[];
  expanded: boolean;
}

interface Props {
  onNewNovel: () => void;
  onSelectNovel: (id: string) => void;
  onSelectChapter: (chapterId: string) => void;
  onSettings: () => void;
}

type SortMode = "time_desc" | "time_asc" | "alpha_asc" | "alpha_desc";

const SORT_LABELS: Record<SortMode, string> = {
  time_desc: "最新创建",
  time_asc: "最早创建",
  alpha_asc: "名称 A→Z",
  alpha_desc: "名称 Z→A",
};

export default function Home({ onNewNovel, onSelectNovel, onSelectChapter, onSettings }: Props) {
  const [novels, setNovels] = useState<NovelWithChapters[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("time_desc");
  const [showSortMenu, setShowSortMenu] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<NovelSummary | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadNovels = () => {
    fetch("/api/novels")
      .then(res => res.json())
      .then((data: NovelSummary[]) => {
        setNovels(data.map(n => ({ ...n, chapters: n.chapters || [], expanded: false })));
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => { loadNovels(); }, []);

  const toggleExpand = async (novelId: string) => {
    const novel = novels.find(n => n.id === novelId);
    if (!novel) return;

    if (novel.expanded) {
      setNovels(prev => prev.map(n => n.id === novelId ? { ...n, expanded: false } : n));
    } else {
      // 加载章节
      if (novel.chapters.length === 0) {
        const res = await fetch(`/api/novels/${novelId}`);
        const data = await res.json();
        setNovels(prev => prev.map(n => n.id === novelId ? { ...n, chapters: data.chapters || [], expanded: true } : n));
      } else {
        setNovels(prev => prev.map(n => n.id === novelId ? { ...n, expanded: true } : n));
      }
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await fetch(`/api/novels/${deleteTarget.id}`, { method: "DELETE" });
      if (res.ok) {
        setNovels(prev => prev.filter(n => n.id !== deleteTarget.id));
        setDeleteTarget(null);
      }
    } finally {
      setDeleting(false);
    }
  };

  // 排序
  const sortedNovels = [...novels].sort((a, b) => {
    switch (sortMode) {
      case "time_desc": return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      case "time_asc": return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      case "alpha_asc": return a.title.localeCompare(b.title, "zh");
      case "alpha_desc": return b.title.localeCompare(a.title, "zh");
    }
  });

  // 搜索过滤（匹配小说标题或章节标题）
  const filteredNovels = search.trim()
    ? sortedNovels.filter(n => {
        const q = search.toLowerCase();
        const novelMatch = n.title.toLowerCase().includes(q);
        const chapterMatch = n.chapters.some(c => c.title.toLowerCase().includes(q));
        return novelMatch || chapterMatch;
      })
    : sortedNovels;

  // 搜索时自动展开有匹配章节的小说
  useEffect(() => {
    if (!search.trim()) return;
    setNovels(prev => prev.map(n => {
      const q = search.toLowerCase();
      const chapterMatch = n.chapters.some(c => c.title.toLowerCase().includes(q));
      return chapterMatch ? { ...n, expanded: true } : n;
    }));
  }, [search]);

  return (
    <div className="min-h-screen bg-white text-[rgba(0,0,0,0.95)]">
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[960px] flex items-center justify-between">
          <h1 className="text-[26px] font-bold tracking-[-0.625px]">InkFrame</h1>
          <div className="flex gap-2">
            <button onClick={onSettings}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[rgba(0,0,0,0.05)] px-3 py-2 text-[14px] font-medium hover:bg-[rgba(0,0,0,0.08)] transition-all">
              <Settings size={16} />
              LLM 设置
            </button>
            <button onClick={onNewNovel}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[14px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] transition-all">
              <Plus size={16} />
              新建小说
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[960px] px-6 py-6">
        {/* 搜索 + 排序 */}
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#a39e98]" />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="搜索小说..."
              className="w-full rounded-[4px] border border-[#dddddd] pl-8 pr-3 py-1.5 text-[14px] outline-none focus:border-[#097fe8] transition-all" />
            {search && (
              <button onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-[#a39e98] hover:text-[rgba(0,0,0,0.95)]">
                <X size={14} />
              </button>
            )}
          </div>
          <div className="relative">
            <button onClick={() => setShowSortMenu(!showSortMenu)}
              className="inline-flex items-center gap-1.5 rounded-[4px] border border-[#dddddd] px-3 py-1.5 text-[13px] text-[#615d59] hover:bg-[#f6f5f4] transition-colors">
              <ArrowUpDown size={14} />
              {SORT_LABELS[sortMode]}
            </button>
            {showSortMenu && (
              <div className="absolute right-0 top-full mt-1 w-36 rounded-[8px] border border-[rgba(0,0,0,0.1)] bg-white shadow-lg z-50">
                {(Object.entries(SORT_LABELS) as [SortMode, string][]).map(([key, label]) => (
                  <button key={key} onClick={() => { setSortMode(key); setShowSortMenu(false); }}
                    className={`w-full text-left px-3 py-2 text-[13px] hover:bg-[#f6f5f4] transition-colors first:rounded-t-[8px] last:rounded-b-[8px] ${sortMode === key ? "text-[#0075de] font-medium" : ""}`}>
                    {label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 内容 */}
        {loading ? (
          <p className="text-[14px] text-[#615d59] py-8 text-center">加载中...</p>
        ) : novels.length === 0 ? (
          <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-12 text-center">
            <FolderOpen size={48} className="mx-auto mb-4 text-[#a39e98]" />
            <p className="text-[16px] text-[#615d59] mb-4">还没有小说，创建一本开始体验吧。</p>
            <button onClick={onNewNovel}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[14px] font-semibold text-white hover:bg-[#005bab] transition-all">
              <Plus size={16} /> 新建小说
            </button>
          </div>
        ) : filteredNovels.length === 0 ? (
          <p className="text-[14px] text-[#a39e98] py-8 text-center">没有匹配的小说</p>
        ) : (
          <div className="border border-[rgba(0,0,0,0.1)] rounded-[8px] overflow-hidden">
            {filteredNovels.map((novel, ni) => (
              <div key={novel.id} className={ni > 0 ? "border-t border-[rgba(0,0,0,0.1)]" : ""}>
                {/* 小说行 */}
                <div className="flex items-center gap-2 px-4 py-3 hover:bg-[#f6f5f4] transition-colors group">
                  <button onClick={() => toggleExpand(novel.id)} className="flex-shrink-0 text-[#a39e98] hover:text-[rgba(0,0,0,0.95)] transition-colors">
                    {novel.expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  </button>
                  <FolderOpen size={16} className="flex-shrink-0 text-[#0075de]" />
                  <div className="flex-1 min-w-0 cursor-pointer" onClick={() => onSelectNovel(novel.id)}>
                    <span className="text-[14px] font-medium truncate">{novel.title}</span>
                    <span className="ml-2 text-[12px] text-[#a39e98]">
                      {novel.language === "zh" ? "中文" : "英文"} · {novel.chapter_count} 章
                    </span>
                  </div>
                  <span className="text-[12px] text-[#a39e98] flex-shrink-0">
                    {new Date(novel.created_at).toLocaleDateString("zh-CN")}
                  </span>
                  <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(novel); }}
                    className="opacity-0 group-hover:opacity-100 flex-shrink-0 rounded-[4px] p-1 text-[#a39e98] hover:text-[#d44] hover:bg-[#fde8e8] transition-all">
                    <Trash2 size={13} />
                  </button>
                </div>

                {/* 章节列表（展开时） */}
                {novel.expanded && (
                  <div className="bg-[#fafafa]">
                    {novel.chapters.length === 0 ? (
                      <div className="px-12 py-3 text-[13px] text-[#a39e98]">暂无章节</div>
                    ) : (
                      novel.chapters.map((chapter) => {
                        const isMatch = search.trim() && chapter.title.toLowerCase().includes(search.toLowerCase());
                        return (
                          <div key={chapter.id}
                            onClick={() => onSelectChapter(chapter.id)}
                            className={`flex items-center gap-2 pl-12 pr-4 py-2.5 hover:bg-[#f0f0f0] cursor-pointer transition-colors ${isMatch ? "bg-[#f2f9ff]" : ""}`}>
                            <FileText size={14} className={`flex-shrink-0 ${isMatch ? "text-[#0075de]" : "text-[#a39e98]"}`} />
                            <span className={`flex-1 text-[13px] truncate ${isMatch ? "font-medium text-[#0075de]" : ""}`}>{chapter.title}</span>
                            <span className="text-[12px] text-[#a39e98] flex-shrink-0">
                              {new Date(chapter.created_at).toLocaleDateString("zh-CN")}
                            </span>
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>

      {/* 删除确认 */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="rounded-[12px] bg-white p-6 w-[400px] shadow-2xl">
            <h3 className="text-[18px] font-semibold mb-2">确认删除</h3>
            <p className="text-[14px] text-[#615d59] mb-1">
              确定要删除小说 <span className="font-semibold">「{deleteTarget.title}」</span> 吗？
            </p>
            <p className="text-[13px] text-[#d44] mb-6">此操作将删除小说及其所有章节，不可撤销。</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteTarget(null)}
                className="rounded-[4px] px-4 py-2 text-[14px] font-medium bg-[rgba(0,0,0,0.05)] hover:bg-[rgba(0,0,0,0.08)] transition-colors">取消</button>
              <button onClick={handleDelete} disabled={deleting}
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
