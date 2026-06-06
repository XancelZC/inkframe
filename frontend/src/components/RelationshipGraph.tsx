import { useMemo } from "react";
import { ReactFlow, Background, Controls, type Node, type Edge } from "@xyflow/react";
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
  const { nodes, edges } = useMemo(() => {
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

    const edgeSet = new Set<string>();
    const edges: Edge[] = [];

    characters.forEach((char) => {
      char.relationships.forEach((rel) => {
        const key = [char.id, rel.target_character_id].sort().join("-");
        if (!edgeSet.has(key) && rel.target_character_id) {
          edgeSet.add(key);
          edges.push({
            id: key,
            source: char.id,
            target: rel.target_character_id,
            label: rel.type,
            labelStyle: { fontSize: 11, fill: "#615d59" },
            labelBgStyle: { fill: "#ffffff", stroke: "rgba(0,0,0,0.1)", strokeWidth: 1 },
            labelBgPadding: [4, 2] as [number, number],
            style: { stroke: "rgba(0,0,0,0.15)" },
            animated: false,
          });
        }
      });
    });

    return { nodes, edges };
  }, [characters]);

  if (characters.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-[#a39e98]">
        No characters to display
      </div>
    );
  }

  return (
    <div className="h-[500px] rounded-[12px] border border-[rgba(0,0,0,0.1)] bg-[#f6f5f4]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={(_, node) => onNodeClick?.(node.id)}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={20} size={1} color="rgba(0,0,0,0.05)" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
