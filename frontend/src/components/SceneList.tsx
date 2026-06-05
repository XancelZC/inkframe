interface Scene {
  id: string;
  title: string | null;
  elements: { id: string; type: string; content: string }[];
}

interface Props {
  scenes: Scene[];
  onSceneClick?: (sceneId: string) => void;
  highlightedScene?: string | null;
}

export default function SceneList({ scenes, onSceneClick, highlightedScene }: Props) {
  if (scenes.length === 0) {
    return <p className="text-[14px] text-[#a39e98] p-4">暂无场景</p>;
  }

  return (
    <div className="space-y-1">
      {scenes.map((scene) => (
        <button
          key={scene.id}
          onClick={() => onSceneClick?.(scene.id)}
          className={`w-full text-left rounded-[4px] px-3 py-2 text-[13px] transition-colors ${
            highlightedScene === scene.id
              ? "bg-[#0075de]/10 text-[#0075de]"
              : "hover:bg-[rgba(0,0,0,0.05)] text-[rgba(0,0,0,0.95)]"
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-[#a39e98] font-mono">{scene.id}</span>
            <span className="font-medium truncate">{scene.title ?? "未命名"}</span>
            <span className="text-[11px] text-[#a39e98] ml-auto">{scene.elements.length} 元素</span>
          </div>
        </button>
      ))}
    </div>
  );
}
