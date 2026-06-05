import { useEffect, useState } from "react";
import { ArrowLeft, Play, ChevronDown, ChevronRight } from "lucide-react";

interface ProjectDetail {
  id: string;
  title: string;
  source_language: string | null;
  created_at: string;
  raw_text: string | null;
}

interface StageResult {
  chapters: { id: string; title: string | null; paragraphs: { id: string; text: string }[] }[];
  detected_language: string;
}

interface Props {
  projectId: string;
  onBack: () => void;
}

export default function ProjectDetail({ projectId, onBack }: Props) {
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [stageResult, setStageResult] = useState<StageResult | null>(null);
  const [showStageResult, setShowStageResult] = useState(false);

  useEffect(() => {
    fetch(`/api/projects/${projectId}`)
      .then((res) => res.json())
      .then((data: ProjectDetail) => {
        setProject(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));

    // Try loading existing stage result
    fetch(`/api/projects/${projectId}/stages/preprocessing`)
      .then((res) => {
        if (res.ok) return res.json();
        return null;
      })
      .then((data: StageResult | null) => {
        if (data) setStageResult(data);
      })
      .catch(() => {});
  }, [projectId]);

  const handleRunPipeline = async () => {
    setProcessing(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/process`, { method: "POST" });
      if (res.ok) {
        // Reload stage result
        const stageRes = await fetch(`/api/projects/${projectId}/stages/preprocessing`);
        if (stageRes.ok) {
          const stageData = await stageRes.json();
          setStageResult(stageData);
        }
      }
    } finally {
      setProcessing(false);
    }
  };

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

  const totalParagraphs = stageResult?.chapters.reduce((sum, ch) => sum + ch.paragraphs.length, 0) ?? 0;

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
          <button
            onClick={handleRunPipeline}
            disabled={processing}
            className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[16px] font-semibold text-white hover:bg-[#005bab] active:scale-[0.96] disabled:opacity-50 transition-all"
          >
            <Play size={16} />
            {processing ? "Processing..." : "Run Pipeline"}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-6 py-8">
        {/* Stage 0 Result */}
        {stageResult && (
          <div className="mb-8">
            <button
              onClick={() => setShowStageResult(!showStageResult)}
              className="inline-flex items-center gap-2 text-[16px] font-semibold mb-4"
            >
              {showStageResult ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              Stage 0: Preprocessing
            </button>
            <div className="flex gap-4 mb-4">
              <div className="rounded-[4px] bg-[#f2f9ff] px-3 py-1 text-[14px] font-semibold text-[#097fe8]">
                {stageResult.chapters.length} chapters
              </div>
              <div className="rounded-[4px] bg-[#f2f9ff] px-3 py-1 text-[14px] font-semibold text-[#097fe8]">
                {totalParagraphs} paragraphs
              </div>
              <div className="rounded-[4px] bg-[#f2f9ff] px-3 py-1 text-[14px] font-semibold text-[#097fe8]">
                {stageResult.detected_language === "zh" ? "Chinese" : "English"}
              </div>
            </div>
            {showStageResult && (
              <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-6 max-h-[400px] overflow-y-auto">
                <pre className="whitespace-pre-wrap text-[14px] leading-[1.5] font-mono">
                  {JSON.stringify(stageResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Source Text */}
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
