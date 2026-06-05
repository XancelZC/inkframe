import { useEffect, useState } from "react";
import { ArrowLeft, Play, ChevronDown, ChevronRight, Users } from "lucide-react";

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

interface Character {
  id: string;
  name: string;
  aliases: string[];
  description: string | null;
  relationships: { target_character_id: string; type: string; description: string | null }[];
}

interface CharacterTable {
  characters: Character[];
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
  const [characters, setCharacters] = useState<CharacterTable | null>(null);
  const [activeTab, setActiveTab] = useState<"source" | "characters">("source");

  useEffect(() => {
    fetch(`/api/projects/${projectId}`)
      .then((res) => res.json())
      .then((data: ProjectDetail) => {
        setProject(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));

    fetch(`/api/projects/${projectId}/stages/preprocessing`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data: StageResult | null) => { if (data) setStageResult(data); })
      .catch(() => {});

    fetch(`/api/projects/${projectId}/characters`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data: CharacterTable | null) => { if (data) setCharacters(data); })
      .catch(() => {});
  }, [projectId]);

  const handleRunStage = async (stage: string) => {
    setProcessing(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/process?from_stage=${stage}`, { method: "POST" });
      if (res.ok) {
        if (stage === "preprocessing") {
          const stageRes = await fetch(`/api/projects/${projectId}/stages/preprocessing`);
          if (stageRes.ok) setStageResult(await stageRes.json());
        } else if (stage === "character_extraction") {
          const charRes = await fetch(`/api/projects/${projectId}/characters`);
          if (charRes.ok) setCharacters(await charRes.json());
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
          <div className="mx-auto max-w-[1200px]"><p className="text-[16px] text-[#615d59]">Loading...</p></div>
        </header>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-[#ffffff] text-[rgba(0,0,0,0.95)]">
        <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
          <div className="mx-auto max-w-[1200px]"><p className="text-[16px] text-[#d44]">Project not found</p></div>
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
            <button onClick={onBack} className="inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[14px] text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-colors">
              <ArrowLeft size={16} /> Back
            </button>
            <div>
              <h1 className="text-[22px] font-bold tracking-[-0.25px]">{project.title}</h1>
              <p className="text-[14px] text-[#615d59]">
                {project.source_language?.toUpperCase() ?? "Unknown"} · {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleRunStage("preprocessing")} disabled={processing}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[14px] font-semibold text-white hover:bg-[#005bab] disabled:opacity-50 transition-all">
              <Play size={14} /> Stage 0
            </button>
            <button onClick={() => handleRunStage("character_extraction")} disabled={processing || !stageResult}
              className="inline-flex items-center gap-2 rounded-[4px] bg-[#0075de] px-4 py-2 text-[14px] font-semibold text-white hover:bg-[#005bab] disabled:opacity-50 transition-all">
              <Users size={14} /> Stage 1
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-6 py-8">
        {/* Stage 0 Result */}
        {stageResult && (
          <div className="mb-6">
            <button onClick={() => setShowStageResult(!showStageResult)} className="inline-flex items-center gap-2 text-[16px] font-semibold mb-3">
              {showStageResult ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              Stage 0: Preprocessing
            </button>
            <div className="flex gap-3 mb-3">
              <span className="rounded-[9999px] bg-[#f2f9ff] px-3 py-1 text-[12px] font-semibold text-[#097fe8]">{stageResult.chapters.length} chapters</span>
              <span className="rounded-[9999px] bg-[#f2f9ff] px-3 py-1 text-[12px] font-semibold text-[#097fe8]">{totalParagraphs} paragraphs</span>
              <span className="rounded-[9999px] bg-[#f2f9ff] px-3 py-1 text-[12px] font-semibold text-[#097fe8]">{stageResult.detected_language === "zh" ? "Chinese" : "English"}</span>
            </div>
            {showStageResult && (
              <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-4 max-h-[300px] overflow-y-auto">
                <pre className="whitespace-pre-wrap text-[14px] leading-[1.5] font-mono">{JSON.stringify(stageResult, null, 2)}</pre>
              </div>
            )}
          </div>
        )}

        {/* Tab selector */}
        <div className="flex gap-1 border-b border-[rgba(0,0,0,0.1)] mb-6">
          <button onClick={() => setActiveTab("source")}
            className={`px-4 py-2 text-[14px] font-medium border-b-2 transition-colors ${activeTab === "source" ? "border-[#0075de] text-[#0075de]" : "border-transparent text-[#615d59] hover:text-[rgba(0,0,0,0.95)]"}`}>
            Source Text
          </button>
          <button onClick={() => setActiveTab("characters")}
            className={`px-4 py-2 text-[14px] font-medium border-b-2 transition-colors ${activeTab === "characters" ? "border-[#0075de] text-[#0075de]" : "border-transparent text-[#615d59] hover:text-[rgba(0,0,0,0.95)]"}`}>
            Characters {characters ? `(${characters.characters.length})` : ""}
          </button>
        </div>

        {/* Tab content */}
        {activeTab === "source" && (
          <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-6 max-h-[600px] overflow-y-auto">
            {project.raw_text ? (
              <pre className="whitespace-pre-wrap text-[16px] leading-[1.5] font-[inherit]">{project.raw_text}</pre>
            ) : (
              <p className="text-[16px] text-[#a39e98]">No text content</p>
            )}
          </div>
        )}

        {activeTab === "characters" && (
          <div>
            {!characters ? (
              <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-12 text-center">
                <Users size={48} className="mx-auto mb-4 text-[#a39e98]" />
                <p className="text-[16px] text-[#615d59]">Run Stage 1 to extract characters.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {characters.characters.map((char) => (
                  <div key={char.id} className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-white p-5 shadow-[rgba(0,0,0,0.04)_0px_4px_18px,rgba(0,0,0,0.027)_0px_2.025px_7.85px,rgba(0,0,0,0.02)_0px_0.8px_2.93px,rgba(0,0,0,0.01)_0px_0.175px_1.04px]">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-[16px] font-semibold">{char.name}</h3>
                        {char.aliases.length > 0 && (
                          <p className="text-[14px] text-[#615d59]">Aliases: {char.aliases.join(", ")}</p>
                        )}
                        {char.description && (
                          <p className="text-[14px] text-[rgba(0,0,0,0.95)] mt-1">{char.description}</p>
                        )}
                      </div>
                      <span className="rounded-[9999px] bg-[#f6f5f4] px-2 py-1 text-[12px] text-[#615d59]">{char.id}</span>
                    </div>
                    {char.relationships.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-[rgba(0,0,0,0.1)]">
                        <p className="text-[12px] font-semibold text-[#615d59] mb-1">Relationships</p>
                        {char.relationships.map((rel, ri) => (
                          <p key={ri} className="text-[14px] text-[#615d59]">
                            {rel.type}: {rel.description ?? rel.target_character_id}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
