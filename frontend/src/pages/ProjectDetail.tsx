import { useEffect, useState, useRef } from "react";
import { ArrowLeft, Play, ChevronDown, ChevronRight, Users, FileText, AlertTriangle, CheckCircle, Download, Shield } from "lucide-react";

interface ProjectDetail {
  id: string;
  title: string;
  source_language: string | null;
  created_at: string;
  raw_text: string | null;
}

interface StageResult {
  chapters: { id: string; title: string | null; paragraphs: { id: string; text: string; start_offset: number; end_offset: number }[] }[];
  detected_language: string;
}

interface Character {
  id: string;
  name: string;
  aliases: string[];
  description: string | null;
  relationships: { target_character_id: string; type: string; description: string | null }[];
}

interface CharacterTable { characters: Character[] }

interface SourceReference {
  chapter_id: string;
  paragraph_ids: string[];
  start_offset: number;
  end_offset: number;
  quote: string;
}

interface SceneElement {
  id: string;
  type: "dialogue" | "action" | "transition" | "narration";
  content: string;
  character_id?: string;
  character_ids?: string[];
  parenthetical?: string;
  inferred: boolean;
  confidence: number;
  source_reference?: SourceReference | null;
}

interface Scene {
  id: string;
  chapter_id: string;
  title: string | null;
  location: string | null;
  time_of_day: string | null;
  timeline_order: number;
  elements: SceneElement[];
}

interface Screenplay {
  metadata: { project_id: string; title: string; source_language: string };
  characters: Character[];
  acts: { id: string; title: string; scenes: Scene[] }[];
}

interface ValidationEntry {
  severity: "error" | "warning" | "info";
  code: string;
  message: string;
  scene_id?: string | null;
  element_id?: string | null;
}

interface ValidationLog {
  entries: ValidationEntry[];
  error_count: number;
  warning_count: number;
  info_count: number;
}

interface Props {
  projectId: string;
  onBack: () => void;
}

type Tab = "source" | "characters" | "screenplay" | "yaml" | "validation";

export default function ProjectDetail({ projectId, onBack }: Props) {
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [stageResult, setStageResult] = useState<StageResult | null>(null);
  const [showStageResult, setShowStageResult] = useState(false);
  const [characters, setCharacters] = useState<CharacterTable | null>(null);
  const [screenplay, setScreenplay] = useState<Screenplay | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("source");
  const [highlightedPara, setHighlightedPara] = useState<string | null>(null);
  const [highlightedElement, setHighlightedElement] = useState<string | null>(null);
  const [validationLog, setValidationLog] = useState<ValidationLog | null>(null);
  const [validationFilter, setValidationFilter] = useState<"all" | "error" | "warning" | "info">("all");
  const screenplayRef = useRef<HTMLDivElement>(null);

  const loadAll = () => {
    fetch(`/api/projects/${projectId}`).then(r => r.json()).then(d => { setProject(d); setLoading(false); }).catch(() => setLoading(false));
    fetch(`/api/projects/${projectId}/stages/preprocessing`).then(r => r.ok ? r.json() : null).then(d => { if (d) setStageResult(d); }).catch(() => {});
    fetch(`/api/projects/${projectId}/characters`).then(r => r.ok ? r.json() : null).then(d => { if (d) setCharacters(d); }).catch(() => {});
    fetch(`/api/projects/${projectId}/screenplay`).then(r => r.ok ? r.json() : null).then(d => { if (d) setScreenplay(d); }).catch(() => {});
    fetch(`/api/projects/${projectId}/validation`).then(r => r.ok ? r.json() : null).then(d => { if (d) setValidationLog(d); }).catch(() => {});
  };

  useEffect(() => { loadAll(); }, [projectId]);

  const handleRunStage = async (stage: string) => {
    setProcessing(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/process?from_stage=${stage}`, { method: "POST" });
      if (res.ok) loadAll();
    } finally { setProcessing(false); }
  };

  const handleSaveScreenplay = async () => {
    if (!screenplay) return;
    await fetch(`/api/projects/${projectId}/screenplay`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(screenplay),
    });
  };

  const handleElementEdit = (sceneIdx: number, elIdx: number, field: string, value: string) => {
    if (!screenplay) return;
    const updated = { ...screenplay };
    (updated.acts[0].scenes[sceneIdx].elements[elIdx] as unknown as Record<string, unknown>)[field] = value;
    setScreenplay({ ...updated });
  };

  const handleExportYaml = async () => {
    const res = await fetch(`/api/projects/${projectId}/export`);
    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${project?.title ?? "screenplay"}.yaml`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  if (loading) return <div className="min-h-screen bg-white text-[rgba(0,0,0,0.95)]"><header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4"><p className="text-[16px] text-[#615d59]">Loading...</p></header></div>;
  if (!project) return <div className="min-h-screen bg-white text-[rgba(0,0,0,0.95)]"><header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4"><p className="text-[16px] text-[#d44]">Project not found</p></header></div>;

  const totalParagraphs = stageResult?.chapters.reduce((s, c) => s + c.paragraphs.length, 0) ?? 0;
  const allScenes = screenplay?.acts.flatMap(a => a.scenes) ?? [];
  const charMap = new Map(characters?.characters.map(c => [c.id, c.name]) ?? []);

  const getElementIdsForPara = (paraId: string): string[] =>
    allScenes.flatMap(s => s.elements.filter(e => e.source_reference?.paragraph_ids?.includes(paraId)).map(e => e.id));

  return (
    <div className="min-h-screen bg-white text-[rgba(0,0,0,0.95)]">
      {/* Header */}
      <header className="border-b border-[rgba(0,0,0,0.1)] px-6 py-4">
        <div className="mx-auto max-w-[1400px] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={onBack} className="inline-flex items-center gap-1 rounded-[4px] px-2 py-1 text-[14px] text-[#615d59] hover:bg-[rgba(0,0,0,0.05)] transition-colors">
              <ArrowLeft size={16} /> Back
            </button>
            <div>
              <h1 className="text-[22px] font-bold tracking-[-0.25px]">{project.title}</h1>
              <p className="text-[14px] text-[#615d59]">{project.source_language?.toUpperCase()} · {new Date(project.created_at).toLocaleDateString()}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleRunStage("preprocessing")} disabled={processing} className="rounded-[4px] bg-[#0075de] px-3 py-1.5 text-[13px] font-semibold text-white hover:bg-[#005bab] disabled:opacity-50 transition-all">
              <Play size={12} className="inline mr-1" />Stage 0
            </button>
            <button onClick={() => handleRunStage("character_extraction")} disabled={processing || !stageResult} className="rounded-[4px] bg-[#0075de] px-3 py-1.5 text-[13px] font-semibold text-white hover:bg-[#005bab] disabled:opacity-50 transition-all">
              <Users size={12} className="inline mr-1" />Stage 1
            </button>
            <button onClick={() => handleRunStage("scene_synthesis")} disabled={processing || !characters} className="rounded-[4px] bg-[#0075de] px-3 py-1.5 text-[13px] font-semibold text-white hover:bg-[#005bab] disabled:opacity-50 transition-all">
              <FileText size={12} className="inline mr-1" />Stage 2
            </button>
            <button onClick={() => handleRunStage("validation")} disabled={processing || !screenplay} className="rounded-[4px] bg-[#0075de] px-3 py-1.5 text-[13px] font-semibold text-white hover:bg-[#005bab] disabled:opacity-50 transition-all">
              <Shield size={12} className="inline mr-1" />Stage 3
            </button>
            {screenplay && (
              <>
                <button onClick={handleSaveScreenplay} className="rounded-[4px] bg-[rgba(0,0,0,0.05)] px-3 py-1.5 text-[13px] font-medium hover:bg-[rgba(0,0,0,0.08)] transition-all">
                  Save
                </button>
                <button onClick={handleExportYaml} className="rounded-[4px] bg-[rgba(0,0,0,0.05)] px-3 py-1.5 text-[13px] font-medium hover:bg-[rgba(0,0,0,0.08)] transition-all">
                  <Download size={12} className="inline mr-1" />Export
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Stage 0 summary */}
      {stageResult && (
        <div className="mx-auto max-w-[1400px] px-6 pt-4">
          <button onClick={() => setShowStageResult(!showStageResult)} className="inline-flex items-center gap-2 text-[14px] font-semibold mb-2">
            {showStageResult ? <ChevronDown size={14} /> : <ChevronRight size={14} />}Stage 0
          </button>
          <div className="flex gap-2 mb-2">
            <span className="rounded-[9999px] bg-[#f2f9ff] px-2 py-0.5 text-[12px] font-semibold text-[#097fe8]">{stageResult.chapters.length}ch</span>
            <span className="rounded-[9999px] bg-[#f2f9ff] px-2 py-0.5 text-[12px] font-semibold text-[#097fe8]">{totalParagraphs}p</span>
            <span className="rounded-[9999px] bg-[#f2f9ff] px-2 py-0.5 text-[12px] font-semibold text-[#097fe8]">{stageResult.detected_language === "zh" ? "ZH" : "EN"}</span>
          </div>
          {showStageResult && <pre className="rounded-[8px] bg-[#f6f5f4] border border-[rgba(0,0,0,0.1)] p-4 max-h-[200px] overflow-auto text-[13px] font-mono">{JSON.stringify(stageResult, null, 2)}</pre>}
        </div>
      )}

      {/* Tabs */}
      <div className="mx-auto max-w-[1400px] px-6 pt-4">
        <div className="flex gap-1 border-b border-[rgba(0,0,0,0.1)]">
          {(["source", "characters", "screenplay", "yaml", "validation"] as Tab[]).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-[13px] font-medium border-b-2 transition-colors capitalize ${activeTab === tab ? "border-[#0075de] text-[#0075de]" : "border-transparent text-[#615d59] hover:text-[rgba(0,0,0,0.95)]"}`}>
              {tab === "source" ? "Source" : tab === "characters" ? `Characters${characters ? ` (${characters.characters.length})` : ""}` : tab === "screenplay" ? "Editor" : tab === "yaml" ? "YAML" : `Validation${validationLog ? ` (${validationLog.entries.length})` : ""}`}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <main className="mx-auto max-w-[1400px] px-6 py-6">
        {/* SOURCE TAB */}
        {activeTab === "source" && (
          <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-6 max-h-[700px] overflow-y-auto">
            {project.raw_text ? (
              <div className="space-y-3">
                {stageResult ? stageResult.chapters.map(ch => (
                  <div key={ch.id}>
                    {ch.title && <h3 className="text-[14px] font-semibold mb-2 text-[#615d59]">{ch.title}</h3>}
                    {ch.paragraphs.map(p => (
                      <p key={p.id} onMouseEnter={() => setHighlightedPara(p.id)} onMouseLeave={() => setHighlightedPara(null)}
                        className={`text-[16px] leading-[1.6] mb-2 cursor-default rounded-[4px] px-1 transition-colors ${highlightedPara === p.id ? "bg-[#0075de]/10" : ""}`}>
                        {p.text}
                      </p>
                    ))}
                  </div>
                )) : (
                  <pre className="whitespace-pre-wrap text-[16px] leading-[1.5]">{project.raw_text}</pre>
                )}
              </div>
            ) : <p className="text-[16px] text-[#a39e98]">No text content</p>}
          </div>
        )}

        {/* CHARACTERS TAB */}
        {activeTab === "characters" && (
          <div>
            {!characters ? (
              <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-12 text-center">
                <Users size={48} className="mx-auto mb-4 text-[#a39e98]" />
                <p className="text-[16px] text-[#615d59]">Run Stage 1 to extract characters.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {characters.characters.map(char => (
                  <div key={char.id} className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-white p-5 shadow-[rgba(0,0,0,0.04)_0px_4px_18px,rgba(0,0,0,0.027)_0px_2.025px_7.85px,rgba(0,0,0,0.02)_0px_0.8px_2.93px,rgba(0,0,0,0.01)_0px_0.175px_1.04px]">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-[16px] font-semibold">{char.name}</h3>
                        {char.aliases.length > 0 && <p className="text-[14px] text-[#615d59]">Aliases: {char.aliases.join(", ")}</p>}
                        {char.description && <p className="text-[14px] mt-1">{char.description}</p>}
                      </div>
                      <span className="rounded-[9999px] bg-[#f6f5f4] px-2 py-1 text-[12px] text-[#615d59]">{char.id}</span>
                    </div>
                    {char.relationships.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-[rgba(0,0,0,0.1)]">
                        <p className="text-[12px] font-semibold text-[#615d59] mb-1">Relationships</p>
                        {char.relationships.map((rel, i) => <p key={i} className="text-[14px] text-[#615d59]">{rel.type}: {rel.description ?? rel.target_character_id}</p>)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* SPLIT EDITOR TAB */}
        {activeTab === "screenplay" && (
          <div>
            {!screenplay ? (
              <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-12 text-center">
                <FileText size={48} className="mx-auto mb-4 text-[#a39e98]" />
                <p className="text-[16px] text-[#615d59]">Run Stage 2 to generate screenplay.</p>
              </div>
            ) : (
              <div className="flex gap-4 h-[700px]">
                {/* Left: Source text (read-only) */}
                <div className="w-1/2 rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-4 overflow-y-auto">
                  <h3 className="text-[14px] font-semibold mb-3 text-[#615d59]">Source Text</h3>
                  {stageResult?.chapters.map(ch => (
                    <div key={ch.id} className="mb-4">
                      {ch.title && <p className="text-[12px] font-semibold text-[#a39e98] mb-2">{ch.title}</p>}
                      {ch.paragraphs.map(p => {
                        const elIds = getElementIdsForPara(p.id);
                        const isHighlighted = highlightedPara === p.id || elIds.includes(highlightedElement ?? "");
                        return (
                          <p key={p.id}
                            onMouseEnter={() => setHighlightedPara(p.id)}
                            onMouseLeave={() => setHighlightedPara(null)}
                            className={`text-[15px] leading-[1.6] mb-2 rounded-[4px] px-1 cursor-default transition-colors ${isHighlighted ? "bg-[#0075de]/10" : ""}`}>
                            {p.text}
                          </p>
                        );
                      })}
                    </div>
                  ))}
                </div>

                {/* Right: Screenplay editor */}
                <div ref={screenplayRef} className="w-1/2 rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-white p-4 overflow-y-auto">
                  <h3 className="text-[14px] font-semibold mb-3 text-[#615d59]">Screenplay</h3>
                  {allScenes.map((scene, si) => (
                    <div key={scene.id} className="mb-6">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="rounded-[9999px] bg-[#f2f9ff] px-2 py-0.5 text-[11px] font-semibold text-[#097fe8]">{scene.id}</span>
                        <span className="text-[14px] font-semibold">{scene.title ?? "Untitled Scene"}</span>
                        {scene.location && <span className="text-[12px] text-[#615d59]">@ {scene.location}</span>}
                        {scene.time_of_day && <span className="text-[12px] text-[#a39e98]">{scene.time_of_day}</span>}
                      </div>
                      <div className="space-y-2">
                        {scene.elements.map((el, ei) => {
                          const isHighlighted = highlightedElement === el.id;
                          const isLinked = highlightedPara && el.source_reference?.paragraph_ids?.includes(highlightedPara);
                          return (
                            <div key={el.id}
                              onMouseEnter={() => setHighlightedElement(el.id)}
                              onMouseLeave={() => setHighlightedElement(null)}
                              className={`rounded-[8px] border p-3 transition-colors ${isHighlighted || isLinked ? "border-[#0075de] bg-[#0075de]/5" : "border-[rgba(0,0,0,0.1)]"} ${el.inferred ? "border-l-2 border-l-[#dd5b00]" : ""} ${el.confidence < 0.7 ? "border-l-2 border-l-[#d44]" : ""}`}>
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`rounded-[4px] px-1.5 py-0.5 text-[11px] font-semibold ${el.type === "dialogue" ? "bg-[#e6f7f6] text-[#2a9d99]" : el.type === "action" ? "bg-[#f2f9ff] text-[#097fe8]" : el.type === "narration" ? "bg-[#fff3e8] text-[#dd5b00]" : "bg-[#f6f5f4] text-[#615d59]"}`}>
                                  {el.type}
                                </span>
                                {el.character_id && <span className="text-[12px] font-medium text-[#615d59]">{charMap.get(el.character_id) ?? el.character_id}</span>}
                                {el.parenthetical && <span className="text-[12px] text-[#a39e98] italic">({el.parenthetical})</span>}
                                {el.inferred && <span title="AI inferred" className="inline-flex items-center"><AlertTriangle size={12} className="text-[#dd5b00]" /></span>}
                                {el.confidence < 0.7 && <span title={`Confidence: ${el.confidence}`} className="inline-flex items-center"><AlertTriangle size={12} className="text-[#d44]" /></span>}
                                {el.confidence >= 0.7 && !el.inferred && <span className="inline-flex items-center"><CheckCircle size={12} className="text-[#2a9d99]" /></span>}
                                <span className="text-[11px] text-[#a39e98] ml-auto">{Math.round(el.confidence * 100)}%</span>
                              </div>
                              <textarea
                                value={el.content}
                                onChange={e => handleElementEdit(si, ei, "content", e.target.value)}
                                className="w-full text-[14px] leading-[1.5] bg-transparent border-none outline-none resize-none"
                                rows={Math.max(1, Math.ceil(el.content.length / 50))}
                              />
                              {el.source_reference && (
                                <p className="text-[11px] text-[#a39e98] mt-1 truncate">Source: {el.source_reference.quote}</p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* YAML TAB */}
        {activeTab === "yaml" && (
          <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-6 max-h-[700px] overflow-y-auto">
            {!screenplay ? (
              <p className="text-[16px] text-[#a39e98]">Run Stage 2 to generate screenplay.</p>
            ) : (
              <pre className="whitespace-pre-wrap text-[14px] leading-[1.5] font-mono">{JSON.stringify(screenplay, null, 2)}</pre>
            )}
          </div>
        )}

        {/* VALIDATION TAB */}
        {activeTab === "validation" && (
          <div>
            {!validationLog ? (
              <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4] p-12 text-center">
                <Shield size={48} className="mx-auto mb-4 text-[#a39e98]" />
                <p className="text-[16px] text-[#615d59]">Run Stage 3 to validate consistency.</p>
              </div>
            ) : (
              <>
                {/* Summary badges */}
                <div className="flex gap-2 mb-4">
                  {validationLog.error_count > 0 && (
                    <span className="rounded-[9999px] bg-[#fde8e8] px-3 py-1 text-[12px] font-semibold text-[#d44]">
                      {validationLog.error_count} errors
                    </span>
                  )}
                  {validationLog.warning_count > 0 && (
                    <span className="rounded-[9999px] bg-[#fff3e8] px-3 py-1 text-[12px] font-semibold text-[#dd5b00]">
                      {validationLog.warning_count} warnings
                    </span>
                  )}
                  {validationLog.info_count > 0 && (
                    <span className="rounded-[9999px] bg-[#f2f9ff] px-3 py-1 text-[12px] font-semibold text-[#097fe8]">
                      {validationLog.info_count} info
                    </span>
                  )}
                  {validationLog.entries.length === 0 && (
                    <span className="rounded-[9999px] bg-[#e6f7f6] px-3 py-1 text-[12px] font-semibold text-[#2a9d99]">
                      All checks passed
                    </span>
                  )}
                </div>

                {/* Filter */}
                <div className="flex gap-1 mb-4">
                  {(["all", "error", "warning", "info"] as const).map(f => (
                    <button key={f} onClick={() => setValidationFilter(f)}
                      className={`rounded-[4px] px-3 py-1 text-[12px] font-medium transition-colors capitalize ${validationFilter === f ? "bg-[#0075de] text-white" : "bg-[rgba(0,0,0,0.05)] text-[#615d59] hover:bg-[rgba(0,0,0,0.08)]"}`}>
                      {f}
                    </button>
                  ))}
                </div>

                {/* Entries */}
                <div className="space-y-2">
                  {validationLog.entries
                    .filter(e => validationFilter === "all" || e.severity === validationFilter)
                    .map((entry, i) => (
                      <div key={i} className={`rounded-[8px] border p-3 ${
                        entry.severity === "error" ? "border-[#d44]/30 bg-[#fde8e8]/30" :
                        entry.severity === "warning" ? "border-[#dd5b00]/30 bg-[#fff3e8]/30" :
                        "border-[#097fe8]/30 bg-[#f2f9ff]/30"
                      }`}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`rounded-[4px] px-1.5 py-0.5 text-[11px] font-semibold ${
                            entry.severity === "error" ? "bg-[#fde8e8] text-[#d44]" :
                            entry.severity === "warning" ? "bg-[#fff3e8] text-[#dd5b00]" :
                            "bg-[#f2f9ff] text-[#097fe8]"
                          }`}>
                            {entry.severity}
                          </span>
                          <span className="text-[12px] text-[#615d59] font-mono">{entry.code}</span>
                          {entry.scene_id && <span className="text-[11px] text-[#a39e98]">{entry.scene_id}</span>}
                          {entry.element_id && <span className="text-[11px] text-[#a39e98]">{entry.element_id}</span>}
                        </div>
                        <p className="text-[14px]">{entry.message}</p>
                      </div>
                    ))}
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
