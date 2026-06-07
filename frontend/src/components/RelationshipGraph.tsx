import { useEffect, useMemo } from "react";
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

export default function RelationshipGraph({ characters, onNodeClick }: Props) {
  const characterNameById = useMemo(
    () => new Map(characters.map((char) => [char.id, char.name])),
    [characters],
  );

  const { initialNodes, initialEdges, relationshipRows } = useMemo(() => {
    const angleStep = (2 * Math.PI) / Math.max(characters.length, 1);
    const radius = 180;

    const nodes: Node[] = characters.map((char, i) => ({
      id: char.id,
      position: {
        x: 250 + radius * Math.cos(angleStep * i - Math.PI / 2),
        y: 200 + radius * Math.sin(angleStep * i - Math.PI / 2),
      },
      data: {
        label: (
          <div className="text-center">
            <div className="text-[14px] font-semibold">{char.name}</div>
            {char.aliases.length > 0 && (
              <div className="text-[11px] text-[#a39e98] max-w-[160px] truncate" title={char.aliases.join("、")}>
                别名：{char.aliases.join("、")}
              </div>
            )}
            {char.description && (
              <div className="text-[11px] text-[#615d59] max-w-[160px] leading-tight"
                style={{
                  display: "-webkit-box",
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                }}
                title={char.description}>
                {char.description}
              </div>
            )}
          </div>
        ),
      },
      style: {
        background: "#ffffff",
        border: "1px solid rgba(0,0,0,0.1)",
        borderRadius: "8px",
        padding: "8px 12px",
        boxShadow: "rgba(0,0,0,0.04) 0px 4px 18px",
        cursor: "pointer",
      },
    }));

    const edgeMap = new Map<string, { source: string; target: string; labels: string[] }>();
    const rows: { source: string; target: string; text: string }[] = [];

    characters.forEach((char) => {
      char.relationships.forEach((rel) => {
        if (!rel.target_character_id) return;

        const key = [char.id, rel.target_character_id].sort().join("-");
        const label = rel.description ? `${rel.type}：${rel.description}` : rel.type;
        const row = {
          source: char.name,
          target: characterNameById.get(rel.target_character_id) ?? rel.target_character_id,
          text: label,
        };
        rows.push(row);

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
  }, [characterNameById, characters]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialEdges, initialNodes, setEdges, setNodes]);

  if (characters.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-[#a39e98]">
        暂无人物可展示
      </div>
    );
  }

  return (
    <div className="rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4]">
      <div className="h-[500px]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => onNodeClick?.(node.id)}
          nodesDraggable
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={20} size={1} color="rgba(0,0,0,0.05)" />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      {relationshipRows.length > 0 && (
        <div className="border-t border-[rgba(0,0,0,0.1)] bg-white px-4 py-3">
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
