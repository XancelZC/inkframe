import { useEffect, useState } from "react";
import { Plus, FileText, Settings, Search, Trash2, X } from "lucide-react";

interface ProjectSummary {
  id: string;
  title: string;
  source_language: string | null;
  created_at: string;
}

interface Props {
  onNewProject: () => void;
  onSelectProject: (id: string) => void;
  onSettings: () => void;
}

export default function Home({ onNewProject, onSelectProject, onSettings }: Props) {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<ProjectSummary | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadProjects = () => {
    fetch("/api/projects")
      .then((res) => res.json())
      .then((data: ProjectSummary[]) => {
        setProjects(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => { loadProjects(); }, []);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await fetch(`/api/projects/${deleteTarget.id}`, { method: "DELETE" });
      if (res.ok) {
        setProjects(prev => prev.filter(p => p.id !== deleteTarget.id));
        setDeleteTarget(null);
      }
    } finally {
      setDeleting(false);
    }
  };

  const filteredProjects = projects.filter(p =>
    p.title.toLowerCase().includes(search.toLowerCase()) ||
    p.id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[1200px] flex items-center justify-between">
          <h1 className="text-[26px] font-bold tracking-[-0.625px]">InkFrame</h1>
          <div className="flex gap-2">
            <button onClick={onSettings}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[rgba(0,0,0,0.05)] px-3 py-2 text-[14px] font-medium hover:bg-[rgba(0,0,0,0.08)] transition-all">
              <Settings size={16} />
              LLM 设置
            </button>
            <button onClick={onNewProject}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[16px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] transition-all">
              <Plus size={16} />
              新建项目
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-[22px] font-bold tracking-[-0.25px]">项目列表</h2>
          {projects.length > 0 && (
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#a39e98]" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="搜索项目..."
                className="rounded-[4px] border border-[#dddddd] pl-8 pr-3 py-1.5 text-[14px] outline-none focus:border-[#097fe8] transition-all w-56"
              />
              {search && (
                <button onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-[#a39e98] hover:text-[rgba(0,0,0,0.95)]">
                  <X size={14} />
                </button>
              )}
            </div>
          )}
        </div>

        {loading ? (
          <p className="text-[16px] text-[#615d59]">加载中...</p>
        ) : projects.length === 0 ? (
          <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-12 text-center">
            <FileText size={48} className="mx-auto mb-4 text-[#a39e98]" />
            <p className="text-[16px] text-[#615d59] mb-4">还没有项目，创建一个开始体验吧。</p>
            <button onClick={onNewProject}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[16px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] transition-all">
              <Plus size={16} />
              新建项目
            </button>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-12 text-center">
            <Search size={48} className="mx-auto mb-4 text-[#a39e98]" />
            <p className="text-[16px] text-[#615d59]">没有匹配的项目</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredProjects.map((project) => (
              <div key={project.id}
                className="group rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-white p-5 shadow-[rgba(0,0,0,0.04)_0px_4px_18px,rgba(0,0,0,0.027)_0px_2.025px_7.85px,rgba(0,0,0,0.02)_0px_0.8px_2.93px,rgba(0,0,0,0.01)_0px_0.175px_1.04px] hover:shadow-[rgba(0,0,0,0.01)_0px_1px_3px,rgba(0,0,0,0.02)_0px_3px_7px,rgba(0,0,0,0.02)_0px_7px_15px,rgba(0,0,0,0.04)_0px_14px_28px,rgba(0,0,0,0.05)_0px_23px_52px] transition-shadow">
                <div onClick={() => onSelectProject(project.id)} className="cursor-pointer">
                  <h3 className="text-[16px] font-semibold mb-1">{project.title}</h3>
                  <p className="text-[14px] text-[#615d59]">
                    {project.source_language === "zh" ? "中文" : project.source_language === "en" ? "英文" : "未知"} ·{" "}
                    {new Date(project.created_at).toLocaleDateString("zh-CN")}
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-[rgba(0,0,0,0.1)] flex justify-end">
                  <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(project); }}
                    className="opacity-0 group-hover:opacity-100 inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[12px] text-[#d44] hover:bg-[#fde8e8] transition-all">
                    <Trash2 size={12} />
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* 删除确认弹窗 */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="rounded-[12px] bg-white p-6 w-[400px] shadow-2xl">
            <h3 className="text-[18px] font-semibold mb-2">确认删除</h3>
            <p className="text-[14px] text-[#615d59] mb-1">
              确定要删除项目 <span className="font-semibold text-[rgba(0,0,0,0.95)]">「{deleteTarget.title}」</span> 吗？
            </p>
            <p className="text-[13px] text-[#d44] mb-6">此操作不可撤销，所有数据将被永久删除。</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteTarget(null)}
                className="rounded-[4px] px-4 py-2 text-[14px] font-medium bg-[rgba(0,0,0,0.05)] hover:bg-[rgba(0,0,0,0.08)] transition-colors">
                取消
              </button>
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
