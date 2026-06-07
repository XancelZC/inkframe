import { Clock, MapPin, Users } from "lucide-react";

interface Scene {
  id: string;
  chapter_id: string;
  title: string | null;
  location: string | null;
  time_of_day: string | null;
  timeline_order: number;
  elements: { type: string; character_id?: string }[];
}

interface Props {
  scenes: Scene[];
  onSceneClick?: (sceneId: string) => void;
  highlightedScene?: string | null;
}

export default function SceneTimeline({ scenes, onSceneClick, highlightedScene }: Props) {
  if (scenes.length === 0) {
    return (
      <div className="p-8 text-center text-[#a39e98]">
        暂无场景数据
      </div>
    );
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {scenes.map((scene, i) => {
        const characterCount = new Set(
          scene.elements.filter(e => e.character_id).map(e => e.character_id)
        ).size;

        return (
          <div key={scene.id} className="flex items-center gap-3 flex-shrink-0">
            <button
              onClick={() => onSceneClick?.(scene.id)}
              className={`min-h-[132px] w-[260px] rounded-[8px] border p-3 text-left transition-colors ${
                highlightedScene === scene.id
                  ? "border-[#0075de] bg-[#0075de]/5"
                  : "border-[rgba(0,0,0,0.1)] bg-white hover:border-[rgba(0,0,0,0.2)]"
              }`}
            >
              <div className="mb-2 flex items-start gap-1.5">
                <span className="rounded-[4px] bg-[#f2f9ff] px-1.5 py-0.5 text-[10px] font-semibold text-[#097fe8]">
                  {scene.id}
                </span>
                <span className="min-w-0 flex-1 break-words text-[13px] font-semibold leading-[1.35]">
                  {scene.title ?? "未命名"}
                </span>
              </div>
              {scene.location && (
                <div className="mb-1 flex items-start gap-1 text-[11px] leading-[1.35] text-[#615d59]">
                  <MapPin size={10} className="mt-0.5 flex-shrink-0" />
                  <span className="min-w-0 flex-1 break-words">{scene.location}</span>
                </div>
              )}
              {scene.time_of_day && (
                <div className="mb-1 flex items-center gap-1 text-[11px] text-[#a39e98]">
                  <Clock size={10} className="flex-shrink-0" />
                  <span className="break-words">{scene.time_of_day}</span>
                </div>
              )}
              {characterCount > 0 && (
                <div className="flex items-center gap-1 text-[11px] text-[#a39e98]">
                  <Users size={10} className="flex-shrink-0" />
                  <span>{characterCount} 个角色</span>
                </div>
              )}
            </button>
            {i < scenes.length - 1 && (
              <div className="w-4 h-px bg-[rgba(0,0,0,0.1)] flex-shrink-0" />
            )}
          </div>
        );
      })}
    </div>
  );
}
