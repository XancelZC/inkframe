import { useEffect, useState } from "react";
import { ArrowLeft, Play } from "lucide-react";

interface ProjectDetail {
  id: string;
  title: string;
  source_language: string | null;
  created_at: string;
  raw_text: string | null;
}

interface Props {
  projectId: string;
  onBack: () => void;
}

export default function ProjectDetail({ projectId, onBack }: Props) {
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/projects/${projectId}`)
      .then((res) => res.json())
      .then((data: ProjectDetail) => {
        setProject(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [projectId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
        <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
          <div className="mx-auto max-w-[1200px]">
            <p className="text-[16px] text-[#615d59]">Loading...</p>
          </div>
        </header>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
        <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
          <div className="mx-auto max-w-[1200px]">
            <p className="text-[16px] text-[#d44]">Project not found</p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[1200px] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[14px] text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-colors"
            >
              <ArrowLeft size={16} />
              Back
            </button>
            <div>
              <h1 className="text-[22px] font-bold tracking-[-0.25px]">{project.title}</h1>
              <p className="text-[14px] text-[#615d59]">
                {project.source_language?.toUpperCase() ?? "Unknown"} ·{" "}
                {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <button className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[16px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] transition-all">
            <Play size={16} />
            Run Pipeline
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-6 py-8">
        <h2 className="text-[16px] font-semibold mb-4">Source Text</h2>
        <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-6 max-h-[600px] overflow-y-auto">
          {project.raw_text ? (
            <pre className="whitespace-pre-wrap text-[16px] leading-[1.5] font-[inherit]">
              {project.raw_text}
            </pre>
          ) : (
            <p className="text-[16px] text-[#a39e98]">No text content</p>
          )}
        </div>
      </main>
    </div>
  );
}
