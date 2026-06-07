import { useEffect, useMemo, useState } from "react";
import { Maximize2, Minimize2 } from "lucide-react";
import {
  Background,
  Controls,
  MarkerType,
  Position,
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

interface Relation {
  source: string;
  target: string;
  type: string;
}

function sortIds(ids: string[], degreeById: Map<string, number>, nameById: Map<string, string>) {
  return [...ids].sort((a, b) => {
    const degreeDelta = (degreeById.get(b) ?? 0) - (degreeById.get(a) ?? 0);
    return degreeDelta || (nameById.get(a) ?? a).localeCompare(nameById.get(b) ?? b, "zh-CN");
  });
}

function buildRelationshipLayout(characters: Character[], relations: Relation[]): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  const ids = characters.map((char) => char.id);
  if (ids.length === 0) return positions;

  const nameById = new Map(characters.map((char) => [char.id, char.name]));
  const adjacency = new Map(ids.map((id) => [id, [] as string[]]));
  const degreeById = new Map(ids.map((id) => [id, 0]));

  relations.forEach((rel) => {
    adjacency.get(rel.source)?.push(rel.target);
    adjacency.get(rel.target)?.push(rel.source);
    degreeById.set(rel.source, (degreeById.get(rel.source) ?? 0) + 1);
    degreeById.set(rel.target, (degreeById.get(rel.target) ?? 0) + 1);
  });

  const visited = new Set<string>();
  const components: string[][] = [];
  ids.forEach((id) => {
    if (visited.has(id)) return;
    const queue = [id];
    const component: string[] = [];
    visited.add(id);

    while (queue.length > 0) {
      const current = queue.shift()!;
      component.push(current);
      sortIds(adjacency.get(current) ?? [], degreeById, nameById).forEach((next) => {
        if (visited.has(next)) return;
        visited.add(next);
        queue.push(next);
      });
    }

    components.push(component);
  });

  const relatedComponents = components
    .filter((component) => component.some((id) => (degreeById.get(id) ?? 0) > 0))
    .sort((a, b) => b.length - a.length);
  const isolatedIds = sortIds(
    components
      .filter((component) => component.every((id) => (degreeById.get(id) ?? 0) === 0))
      .flat(),
    degreeById,
    nameById,
  );

  if (relatedComponents.length === 0) {
    const columns = Math.ceil(Math.sqrt(ids.length));
    sortIds(ids, degreeById, nameById).forEach((id, index) => {
      positions.set(id, {
        x: (index % columns) * 260,
        y: Math.floor(index / columns) * 150,
      });
    });
    return positions;
  }

  let blockY = 0;
  let widestBlock = 0;
  relatedComponents.forEach((component) => {
    const root = sortIds(component, degreeById, nameById)[0];
    const componentSet = new Set(component);
    const levelById = new Map<string, number>([[root, 0]]);
    const queue = [root];

    while (queue.length > 0) {
      const current = queue.shift()!;
      const level = levelById.get(current) ?? 0;
      sortIds(adjacency.get(current) ?? [], degreeById, nameById).forEach((next) => {
        if (!componentSet.has(next) || levelById.has(next)) return;
        levelById.set(next, level + 1);
        queue.push(next);
      });
    }

    const levels = Array.from(levelById.entries()).reduce<string[][]>((acc, [id, level]) => {
      if (!acc[level]) acc[level] = [];
      acc[level].push(id);
      return acc;
    }, []);

    levels.forEach((levelIds) => {
      levelIds.sort((a, b) => (nameById.get(a) ?? a).localeCompare(nameById.get(b) ?? b, "zh-CN"));
    });

    for (let levelIndex = 1; levelIndex < levels.length; levelIndex += 1) {
      const previousOrder = new Map(levels[levelIndex - 1].map((id, index) => [id, index]));
      levels[levelIndex].sort((a, b) => {
        const barycenter = (id: string) => {
          const neighborIndexes = (adjacency.get(id) ?? [])
            .map((neighbor) => previousOrder.get(neighbor))
            .filter((index): index is number => index !== undefined);
          if (neighborIndexes.length === 0) return Number.MAX_SAFE_INTEGER;
          return neighborIndexes.reduce((sum, index) => sum + index, 0) / neighborIndexes.length;
        };
        const barycenterDelta = barycenter(a) - barycenter(b);
        return barycenterDelta || (nameById.get(a) ?? a).localeCompare(nameById.get(b) ?? b, "zh-CN");
      });
    }

    const maxRows = Math.max(...levels.map((level) => level.length));
    const blockHeight = Math.max(150, maxRows * 150);
    levels.forEach((levelIds, levelIndex) => {
      const startY = blockY + (blockHeight - levelIds.length * 150) / 2;
      levelIds.forEach((id, rowIndex) => {
        positions.set(id, {
          x: levelIndex * 300,
          y: startY + rowIndex * 150,
        });
      });
    });

    widestBlock = Math.max(widestBlock, (levels.length - 1) * 300);
    blockY += blockHeight + 190;
  });

  if (isolatedIds.length > 0) {
    const isolatedX = widestBlock + 420;
    isolatedIds.forEach((id, index) => {
      positions.set(id, {
        x: isolatedX + (index % 2) * 240,
        y: Math.floor(index / 2) * 130,
      });
    });
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
    const characterIds = new Set(characters.map((char) => char.id));
    const relations: Relation[] = [];
    characters.forEach((char) => {
      char.relationships.forEach((rel) => {
        if (!rel.target_character_id || !characterIds.has(rel.target_character_id)) return;
        relations.push({
          source: char.id,
          target: rel.target_character_id,
          type: rel.type || "关系",
        });
      });
    });

    const positions = buildRelationshipLayout(characters, relations);

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
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
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

    const edgeMap = new Map<string, { labels: Set<string> }>();
    const rows: { source: string; target: string; text: string }[] = [];

    relations.forEach((rel) => {
      const key = [rel.source, rel.target].sort().join("-");
      rows.push({
        source: characterNameById.get(rel.source) ?? rel.source,
        target: characterNameById.get(rel.target) ?? rel.target,
        text: rel.type,
      });

      const edge = edgeMap.get(key);
      if (edge) {
        edge.labels.add(rel.type);
      } else {
        edgeMap.set(key, { labels: new Set([rel.type]) });
      }
    });

    const edges: Edge[] = Array.from(edgeMap.entries()).map(([key, edge]) => {
      const [a, b] = key.split("-");
      const aPosition = positions.get(a) ?? { x: 0, y: 0 };
      const bPosition = positions.get(b) ?? { x: 0, y: 0 };
      const source = aPosition.x <= bPosition.x ? a : b;
      const target = source === a ? b : a;

      return {
        id: key,
        source,
        target,
        type: "straight",
        label: Array.from(edge.labels).join("/"),
        labelStyle: { fontSize: 11, fill: "#3f3a36", fontWeight: 500 },
        labelBgStyle: { fill: "#ffffff", stroke: "rgba(0,0,0,0.12)", strokeWidth: 1 },
        labelBgPadding: [6, 3] as [number, number],
        style: { stroke: "rgba(0,0,0,0.22)", strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "rgba(0,0,0,0.22)" },
        animated: false,
        interactionWidth: 16,
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
