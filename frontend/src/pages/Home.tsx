import { useEffect, useState } from "react";
import { Plus, FileText, Settings } from "lucide-react";

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

  useEffect(() => {
    fetch("/api/projects")
      .then((res) => res.json())
      .then((data: ProjectSummary[]) => {
        setProjects(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[1200px] flex items-center justify-between">
          <h1 className="text-[26px] font-bold tracking-[-0.625px]">InkFrame</h1>
          <div className="flex gap-2">
            <button
              onClick={onSettings}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[rgba(0,0,0,0.05)] px-3 py-2 text-[14px] font-medium hover:bg-[rgba(0,0,0,0.08)] transition-all"
            >
              <Settings size={16} />
              LLM 设置
            </button>
            <button
              onClick={onNewProject}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[16px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] transition-all"
            >
              <Plus size={16} />
              新建项目
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-6 py-8">
        <h2 className="text-[22px] font-bold tracking-[-0.25px] mb-6">项目列表</h2>

        {loading ? (
          <p className="text-[16px] text-[#615d59]">加载中...</p>
        ) : projects.length === 0 ? (
          <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-12 text-center">
            <FileText size={48} className="mx-auto mb-4 text-[#a39e98]" />
            <p className="text-[16px] text-[#615d59] mb-4">
              还没有项目，创建一个开始体验吧。
            </p>
            <button
              onClick={onNewProject}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[16px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] transition-all"
            >
              <Plus size={16} />
              新建项目
            </button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <div
                key={project.id}
                onClick={() => onSelectProject(project.id)}
                className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-white p-5 shadow-[rgba(0,0,0,0.04)_0px_4px_18px,rgba(0,0,0,0.027)_0px_2.025px_7.85px,rgba(0,0,0,0.02)_0px_0.8px_2.93px,rgba(0,0,0,0.01)_0px_0.175px_1.04px] hover:shadow-[rgba(0,0,0,0.01)_0px_1px_3px,rgba(0,0,0,0.02)_0px_3px_7px,rgba(0,0,0,0.02)_0px_7px_15px,rgba(0,0,0,0.04)_0px_14px_28px,rgba(0,0,0,0.05)_0px_23px_52px] transition-shadow cursor-pointer"
              >
                <h3 className="text-[16px] font-semibold mb-1">{project.title}</h3>
                <p className="text-[14px] text-[#615d59]">
                  {project.source_language === "zh" ? "中文" : project.source_language === "en" ? "英文" : "未知"} ·{" "}
                  {new Date(project.created_at).toLocaleDateString("zh-CN")}
                </p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
