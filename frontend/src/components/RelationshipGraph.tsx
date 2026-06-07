import { useEffect, useMemo, useState } from "react";
import { Maximize2, Minimize2 } from "lucide-react";
import {
  Background,
  Controls,
  MarkerType,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

interface Character {
  id: string;
  name: string;
  aliases: string[];
  description: string | null;
  relationships: { target_character_id: string; type: string; description: string | null }[];
}

interface Props {
  characters: Character[];
  onNodeClick?: (characterId: string) => void;
}

function buildRelationshipLayout(characters: Character[]): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  if (characters.length === 0) return positions;

  const degreeById = new Map(characters.map((char) => [char.id, 0]));
  characters.forEach((char) => {
    char.relationships.forEach((rel) => {
      if (!rel.target_character_id || !degreeById.has(rel.target_character_id)) return;
      degreeById.set(char.id, (degreeById.get(char.id) ?? 0) + 1);
      degreeById.set(rel.target_character_id, (degreeById.get(rel.target_character_id) ?? 0) + 1);
    });
  });

  const ordered = [...characters].sort((a, b) => {
    const degreeDelta = (degreeById.get(b.id) ?? 0) - (degreeById.get(a.id) ?? 0);
    return degreeDelta || a.name.localeCompare(b.name, "zh-CN");
  });

  const hasRelationships = ordered.some((char) => (degreeById.get(char.id) ?? 0) > 0);
  if (!hasRelationships) {
    const columns = Math.ceil(Math.sqrt(ordered.length));
    ordered.forEach((char, index) => {
      positions.set(char.id, {
        x: (index % columns) * 260,
        y: Math.floor(index / columns) * 150,
      });
    });
    return positions;
  }

  positions.set(ordered[0].id, { x: 0, y: 0 });

  const rest = ordered.slice(1);
  let cursor = 0;
  let ring = 0;
  while (cursor < rest.length) {
    const capacity = ring === 0 ? 8 : 12 + ring * 4;
    const radius = 280 + ring * 220;
    const items = rest.slice(cursor, cursor + capacity);
    items.forEach((char, index) => {
      const angle = (2 * Math.PI * index) / items.length - Math.PI / 2;
      positions.set(char.id, {
        x: Math.round(radius * Math.cos(angle)),
        y: Math.round(radius * Math.sin(angle)),
      });
    });
    cursor += items.length;
    ring += 1;
  }

  return positions;
}

export default function RelationshipGraph({ characters, onNodeClick }: Props) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const graphKey = useMemo(
    () => characters
      .map((char) => [
        char.id,
        char.name,
        char.aliases.join(","),
        char.description ?? "",
        char.relationships.map((rel) => `${rel.target_character_id}-${rel.type}-${rel.description ?? ""}`).join(","),
      ].join(":"))
      .join("|"),
    [characters],
  );

  const characterNameById = useMemo(
    () => new Map(characters.map((char) => [char.id, char.name])),
    [graphKey],
  );

  const { initialNodes, initialEdges, relationshipRows } = useMemo(() => {
    const positions = buildRelationshipLayout(characters);

    const nodes: Node[] = characters.map((char) => ({
      id: char.id,
      position: positions.get(char.id) ?? { x: 0, y: 0 },
      data: {
        label: (
          <div className="text-center">
            <div className="text-[14px] font-semibold">{char.name}</div>
            {char.aliases.length > 0 && (
              <div className="max-w-[170px] truncate text-[11px] text-[#a39e98]" title={char.aliases.join("、")}>
                别名：{char.aliases.join("、")}
              </div>
            )}
            {char.description && (
              <div
                className="max-w-[170px] text-[11px] leading-tight text-[#615d59]"
                style={{
                  display: "-webkit-box",
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                }}
                title={char.description}
              >
                {char.description}
              </div>
            )}
          </div>
        ),
      },
      draggable: true,
      selectable: true,
      style: {
        background: "#ffffff",
        border: "1px solid rgba(0,0,0,0.12)",
        borderRadius: "8px",
        padding: "9px 12px",
        boxShadow: "rgba(0,0,0,0.06) 0px 6px 20px",
        cursor: "grab",
        minWidth: 130,
      },
    }));

    const edgeMap = new Map<string, { source: string; target: string; labels: string[] }>();
    const rows: { source: string; target: string; text: string }[] = [];

    characters.forEach((char) => {
      char.relationships.forEach((rel) => {
        if (!rel.target_character_id) return;

        const key = [char.id, rel.target_character_id].sort().join("-");
        const label = rel.description ? `${rel.type}：${rel.description}` : rel.type;
        rows.push({
          source: char.name,
          target: characterNameById.get(rel.target_character_id) ?? rel.target_character_id,
          text: label,
        });

        const edge = edgeMap.get(key);
        if (edge) {
          edge.labels.push(label);
        } else {
          edgeMap.set(key, { source: char.id, target: rel.target_character_id, labels: [label] });
        }
      });
    });

    const edges: Edge[] = Array.from(edgeMap.entries()).map(([key, edge]) => {
      const label = edge.labels.join("；");
      return {
        id: key,
        source: edge.source,
        target: edge.target,
        label,
        labelStyle: { fontSize: 11, fill: "#3f3a36", fontWeight: 500 },
        labelBgStyle: { fill: "#ffffff", stroke: "rgba(0,0,0,0.12)", strokeWidth: 1 },
        labelBgPadding: [6, 3] as [number, number],
        style: { stroke: "rgba(0,0,0,0.22)", strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "rgba(0,0,0,0.22)" },
        animated: false,
      };
    });

    return { initialNodes: nodes, initialEdges: edges, relationshipRows: rows };
  }, [characterNameById, graphKey]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [graphKey, setEdges, setNodes]);

  if (characters.length === 0) {
    return (
      <div className="flex h-[400px] items-center justify-center text-[#a39e98]">
        暂无人物可展示
      </div>
    );
  }

  const graphHeightClass = isFullscreen ? "h-[calc(100vh-180px)]" : "h-[560px]";

  return (
    <div className={isFullscreen ? "fixed inset-4 z-50 rounded-[8px] border border-[rgba(0,0,0,0.12)] bg-[#f6f5f4] shadow-2xl" : "rounded-[8px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4]"}>
      <div className="flex items-center justify-between border-b border-[rgba(0,0,0,0.08)] bg-white px-4 py-2">
        <div className="text-[13px] font-semibold text-[#615d59]">人物关系图</div>
        <button
          type="button"
          onClick={() => setIsFullscreen(prev => !prev)}
          className="inline-flex h-8 w-8 items-center justify-center rounded-[4px] text-[#615d59] hover:bg-[#f0f0f0] hover:text-[rgba(0,0,0,0.9)]"
          title={isFullscreen ? "退出全屏" : "全屏查看"}
          aria-label={isFullscreen ? "退出全屏" : "全屏查看"}
        >
          {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
      </div>

      <div className={`${graphHeightClass} overflow-hidden`}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => onNodeClick?.(node.id)}
          nodesDraggable
          nodesConnectable={false}
          elementsSelectable
          panOnDrag
          panOnScroll
          zoomOnScroll
          zoomOnPinch
          selectionOnDrag={false}
          minZoom={0.2}
          maxZoom={2}
          defaultEdgeOptions={{ selectable: false }}
          fitView
          fitViewOptions={{ padding: 0.24, minZoom: 0.35, maxZoom: 1 }}
          proOptions={{ hideAttribution: true }}
          className="[&_.react-flow__pane]:cursor-grab [&_.react-flow__pane.dragging]:cursor-grabbing [&_.react-flow__node.dragging]:cursor-grabbing"
        >
          <Background gap={24} size={1} color="rgba(0,0,0,0.06)" />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>

      {relationshipRows.length > 0 && (
        <div className="max-h-[180px] overflow-auto border-t border-[rgba(0,0,0,0.1)] bg-white px-4 py-3">
          <h4 className="mb-2 text-[13px] font-semibold text-[#615d59]">关系说明</h4>
          <div className="grid gap-2 sm:grid-cols-2">
            {relationshipRows.map((row, index) => (
              <div key={`${row.source}-${row.target}-${index}`} className="rounded-[6px] bg-[#f6f5f4] px-3 py-2 text-[12px] leading-[1.45] text-[#3f3a36]">
                <span className="font-semibold">{row.source}</span>
                <span className="mx-1 text-[#a39e98]">→</span>
                <span className="font-semibold">{row.target}</span>
                <span className="mx-1 text-[#a39e98]">/</span>
                <span>{row.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
