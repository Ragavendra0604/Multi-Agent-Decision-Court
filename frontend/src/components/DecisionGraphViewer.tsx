import React, { useState, useMemo, useRef } from 'react';
import { GraphData, GraphNode, GraphEdge } from '../types';
import {
  Network,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  LayoutGrid,
  GitBranch,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info,
  Maximize2,
  Minimize2,
  Sparkles,
} from 'lucide-react';

interface DecisionGraphViewerProps {
  graph: GraphData;
}

export const DecisionGraphViewer: React.FC<DecisionGraphViewerProps> = ({ graph }) => {
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [viewMode, setViewMode] = useState<'canvas' | 'cards'>('canvas');
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [simulatedInvalidNodeId, setSimulatedInvalidNodeId] = useState<string | null>(null);

  const nodeTypes = ['ALL', 'DECISION', 'CLAIM', 'EVIDENCE', 'ASSUMPTION', 'REQUIREMENT', 'RISK', 'ALTERNATIVE'];

  // Calculate connected edges and node IDs for highlight
  const { connectedNodeIds, connectedEdgeIds } = useMemo(() => {
    if (!selectedNode) return { connectedNodeIds: new Set<string>(), connectedEdgeIds: new Set<string>() };
    const nodeSet = new Set<string>([selectedNode.id]);
    const edgeSet = new Set<string>();

    graph.edges.forEach((e) => {
      if (e.source === selectedNode.id || e.target === selectedNode.id) {
        nodeSet.add(e.source);
        nodeSet.add(e.target);
        edgeSet.add(`${e.source}->${e.target}`);
      }
    });
    return { connectedNodeIds: nodeSet, connectedEdgeIds: edgeSet };
  }, [selectedNode, graph.edges]);

  // Simulated Invalidation Cascades
  const invalidatedDescendants = useMemo(() => {
    if (!simulatedInvalidNodeId) return new Set<string>();
    const invalidated = new Set<string>([simulatedInvalidNodeId]);
    let changed = true;
    while (changed) {
      changed = false;
      graph.edges.forEach((e) => {
        if (invalidated.has(e.source) && !invalidated.has(e.target)) {
          invalidated.add(e.target);
          changed = true;
        }
      });
    }
    return invalidated;
  }, [simulatedInvalidNodeId, graph.edges]);

  const getNodeColor = (type: string, isInvalidated: boolean = false) => {
    if (isInvalidated) {
      return {
        bg: 'bg-red-950/80',
        border: 'border-red-500',
        text: 'text-red-300',
        svgFill: '#ef4444',
      };
    }
    switch (type) {
      case 'DECISION':
      case 'CASE':
        return { bg: 'bg-purple-950/60', border: 'border-purple-500', text: 'text-purple-300', svgFill: '#a855f7' };
      case 'CLAIM':
        return { bg: 'bg-blue-950/60', border: 'border-blue-500', text: 'text-blue-300', svgFill: '#3b82f6' };
      case 'EVIDENCE':
        return { bg: 'bg-emerald-950/60', border: 'border-emerald-500', text: 'text-emerald-300', svgFill: '#10b981' };
      case 'ASSUMPTION':
        return { bg: 'bg-amber-950/60', border: 'border-amber-500', text: 'text-amber-300', svgFill: '#f59e0b' };
      case 'REQUIREMENT':
      case 'CONSTRAINT':
        return { bg: 'bg-indigo-950/60', border: 'border-indigo-500', text: 'text-indigo-300', svgFill: '#6366f1' };
      case 'RISK':
        return { bg: 'bg-rose-950/60', border: 'border-rose-500', text: 'text-rose-300', svgFill: '#f43f5e' };
      case 'ALTERNATIVE':
        return { bg: 'bg-teal-950/60', border: 'border-teal-500', text: 'text-teal-300', svgFill: '#14b8a6' };
      default:
        return { bg: 'bg-slate-900', border: 'border-slate-700', text: 'text-slate-300', svgFill: '#64748b' };
    }
  };

  const getEdgeColor = (relation: string) => {
    switch (relation?.toUpperCase()) {
      case 'SUPPORTS':
        return '#10b981'; // emerald
      case 'CONTRADICTS':
      case 'REFUTES':
        return '#ef4444'; // red
      case 'ASSUMES':
        return '#f59e0b'; // amber
      case 'REQUIRES':
        return '#6366f1'; // indigo
      default:
        return '#64748b'; // slate
    }
  };

  // Structured Tier Coordinates for Dynamic Visual Layout
  const layoutNodes = useMemo(() => {
    const tierMap: Record<string, GraphNode[]> = {
      decision: [],
      claims: [],
      foundations: [],
    };

    graph.nodes.forEach((n) => {
      const t = n.node_type?.toUpperCase();
      if (t === 'DECISION' || t === 'CASE' || t === 'PROBLEM') {
        tierMap.decision.push(n);
      } else if (t === 'CLAIM') {
        tierMap.claims.push(n);
      } else {
        tierMap.foundations.push(n);
      }
    });

    const positions: Record<string, { x: number; y: number; node: GraphNode }> = {};
    const width = 860;

    // Row 1: Decision
    tierMap.decision.forEach((n, idx) => {
      const step = width / (tierMap.decision.length + 1);
      positions[n.id] = { x: step * (idx + 1), y: 70, node: n };
    });

    // Row 2: Claims
    tierMap.claims.forEach((n, idx) => {
      const step = width / (tierMap.claims.length + 1);
      positions[n.id] = { x: step * (idx + 1), y: 220, node: n };
    });

    // Row 3: Foundations (Evidence, Assumptions, Risks)
    tierMap.foundations.forEach((n, idx) => {
      const step = width / (tierMap.foundations.length + 1);
      positions[n.id] = { x: step * (idx + 1), y: 390, node: n };
    });

    return positions;
  }, [graph.nodes]);

  const filteredNodes = useMemo(() => {
    if (selectedType === 'ALL') return graph.nodes;
    return graph.nodes.filter((n) => n.node_type === selectedType);
  }, [graph.nodes, selectedType]);

  return (
    <div className="space-y-4">
      {/* Top Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 border border-indigo-500/30 rounded-xl">
            <Network className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-white">Decision Justification Graph</h3>
            <p className="text-xs text-slate-400 font-mono">
              {graph.nodes.length} nodes · {graph.edges.length} justification edges
            </p>
          </div>
        </div>

        {/* View Switcher & Filter Pills */}
        <div className="flex items-center gap-2">
          <div className="bg-slate-950 p-1 border border-slate-800 rounded-xl flex items-center gap-1">
            <button
              onClick={() => setViewMode('canvas')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                viewMode === 'canvas'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <GitBranch className="w-3.5 h-3.5" />
              Topology Canvas
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                viewMode === 'cards'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              Card Matrix
            </button>
          </div>

          <div className="flex items-center gap-1 border-l border-slate-800 pl-2">
            <button
              onClick={() => setZoomLevel((z) => Math.min(z + 0.15, 1.6))}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={() => setZoomLevel((z) => Math.max(z - 0.15, 0.65))}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={() => setZoomLevel(1)}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
              title="Reset Zoom"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Filter Chips Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        <span className="text-[11px] font-mono text-slate-500 uppercase mr-1">Filter:</span>
        {nodeTypes.map((type) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            className={`px-3 py-1 rounded-lg text-xs font-mono transition-all shrink-0 ${
              selectedType === type
                ? 'bg-indigo-600/30 border border-indigo-500 text-indigo-200 font-semibold shadow-sm'
                : 'bg-slate-900 border border-slate-800/80 text-slate-400 hover:text-slate-200'
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Canvas or Cards */}
        <div className="lg:col-span-2 bg-slate-950/70 border border-slate-800/90 rounded-2xl overflow-hidden min-h-[520px] flex flex-col relative shadow-2xl">
          {viewMode === 'canvas' ? (
            /* Interactive SVG Graph Canvas */
            <div className="flex-1 overflow-auto p-4 flex items-center justify-center">
              <svg
                width="880"
                height="500"
                viewBox="0 0 880 500"
                className="transition-transform duration-200 select-none"
                style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
              >
                <defs>
                  <marker
                    id="arrowhead"
                    markerWidth="8"
                    markerHeight="6"
                    refX="7"
                    refY="3"
                    orient="auto"
                  >
                    <polygon points="0 0, 8 3, 0 6" fill="#64748b" />
                  </marker>
                  <marker
                    id="arrowhead-active"
                    markerWidth="8"
                    markerHeight="6"
                    refX="7"
                    refY="3"
                    orient="auto"
                  >
                    <polygon points="0 0, 8 3, 0 6" fill="#818cf8" />
                  </marker>
                </defs>

                {/* Edges */}
                {graph.edges.map((edge) => {
                  const src = layoutNodes[edge.source];
                  const tgt = layoutNodes[edge.target];
                  if (!src || !tgt) return null;

                  const edgeKey = `${edge.source}->${edge.target}`;
                  const isHighlighted = connectedEdgeIds.has(edgeKey);
                  const strokeColor = isHighlighted ? '#818cf8' : getEdgeColor(edge.relation);
                  const isDimmed = selectedNode && !isHighlighted;

                  // Curvature bezier calculation
                  const midY = (src.y + tgt.y) / 2;
                  const pathD = `M ${src.x} ${src.y} C ${src.x} ${midY}, ${tgt.x} ${midY}, ${tgt.x} ${tgt.y}`;

                  return (
                    <g key={edgeKey} className="transition-opacity duration-200">
                      <path
                        d={pathD}
                        fill="none"
                        stroke={strokeColor}
                        strokeWidth={isHighlighted ? 2.5 : 1.5}
                        strokeDasharray={edge.relation === 'CONTRADICTS' ? '4,4' : undefined}
                        opacity={isDimmed ? 0.2 : 0.85}
                        markerEnd={isHighlighted ? 'url(#arrowhead-active)' : 'url(#arrowhead)'}
                      />
                      <text
                        x={(src.x + tgt.x) / 2}
                        y={midY - 4}
                        fill={strokeColor}
                        fontSize="9"
                        textAnchor="middle"
                        fontFamily="monospace"
                        opacity={isDimmed ? 0.15 : 0.9}
                      >
                        {edge.relation}
                      </text>
                    </g>
                  );
                })}

                {/* Nodes */}
                {Object.values(layoutNodes).map(({ x, y, node }) => {
                  const isSelected = selectedNode?.id === node.id;
                  const isConnected = connectedNodeIds.has(node.id);
                  const isInvalidated = invalidatedDescendants.has(node.id);
                  const isDimmed = selectedNode && !isConnected && !isSelected;
                  const color = getNodeColor(node.node_type, isInvalidated);

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${x}, ${y})`}
                      onClick={() => setSelectedNode(node)}
                      className="cursor-pointer transition-all duration-200 group"
                      opacity={isDimmed ? 0.25 : 1}
                    >
                      {/* Node Glow Circle */}
                      <circle
                        r={isSelected ? 26 : 21}
                        fill={color.svgFill}
                        fillOpacity={isSelected ? 0.35 : 0.18}
                        stroke={color.svgFill}
                        strokeWidth={isSelected ? 2.5 : 1.5}
                        className="transition-all duration-150 group-hover:scale-110"
                      />
                      <circle
                        r="6"
                        fill={color.svgFill}
                      />

                      {/* Node ID label */}
                      <text
                        y="-26"
                        textAnchor="middle"
                        fill="#cbd5e1"
                        fontSize="10"
                        fontWeight="600"
                        fontFamily="monospace"
                        className="pointer-events-none"
                      >
                        {node.id}
                      </text>

                      {/* Snippet label */}
                      <text
                        y="34"
                        textAnchor="middle"
                        fill="#94a3b8"
                        fontSize="9.5"
                        fontFamily="sans-serif"
                        className="pointer-events-none max-w-[120px]"
                      >
                        {node.label.length > 22 ? `${node.label.substring(0, 20)}...` : node.label}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          ) : (
            /* Card Grid View */
            <div className="p-6 overflow-y-auto max-h-[540px]">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {filteredNodes.map((node) => {
                  const isSelected = selectedNode?.id === node.id;
                  const isInvalidated = invalidatedDescendants.has(node.id);
                  const color = getNodeColor(node.node_type, isInvalidated);

                  return (
                    <div
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${color.bg} ${color.border} ${
                        isSelected
                          ? 'ring-2 ring-indigo-400 scale-[1.01] shadow-lg shadow-indigo-500/20'
                          : 'hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-mono text-[11px] font-bold text-slate-300">{node.id}</span>
                        <span className="font-mono text-[10px] px-2 py-0.5 rounded-full border border-slate-700 bg-slate-900/60 uppercase">
                          {node.node_type}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 line-clamp-2 leading-relaxed">{node.label}</p>
                      <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400 font-mono pt-2 border-t border-slate-800/80">
                        <span>Confidence</span>
                        <span className="font-semibold text-indigo-300">{(node.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Canvas Bottom Legend */}
          <div className="bg-slate-900/90 border-t border-slate-800 p-3 flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-400">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Claims
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Evidence
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Assumptions
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Risks
              </span>
            </div>
            <span className="text-slate-500">Click any node to inspect semantic justification chain</span>
          </div>
        </div>

        {/* Right Col: Deep Node Inspector & Invalidation Simulator */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 flex flex-col h-[520px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <h4 className="text-xs font-mono uppercase text-slate-400 flex items-center gap-2">
              <Info className="w-3.5 h-3.5 text-indigo-400" />
              Node Dependency Inspector
            </h4>
            {selectedNode && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                {selectedNode.node_type}
              </span>
            )}
          </div>

          {selectedNode ? (
            <div className="flex-1 overflow-y-auto space-y-4 pr-1 text-xs font-mono">
              <div>
                <div className="text-[10px] text-slate-500 mb-0.5">IDENTIFIER</div>
                <div className="font-bold text-white text-sm">{selectedNode.id}</div>
              </div>

              <div>
                <div className="text-[10px] text-slate-500 mb-0.5">STATEMENT / CONTENT</div>
                <p className="text-slate-200 font-sans text-xs bg-slate-950 p-3 rounded-xl border border-slate-800 leading-relaxed">
                  {selectedNode.label}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500">CONFIDENCE</div>
                  <div className="font-bold text-indigo-400 text-sm mt-0.5">
                    {(selectedNode.confidence * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500">STATUS</div>
                  <div className="font-bold text-emerald-400 text-sm mt-0.5 truncate">
                    {selectedNode.properties?.status || 'ACTIVE'}
                  </div>
                </div>
              </div>

              {/* Justification Relationships */}
              <div>
                <div className="text-[10px] text-slate-500 mb-1 uppercase">Justification Links</div>
                <div className="space-y-1.5">
                  {graph.edges
                    .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((edge, idx) => {
                      const isSource = edge.source === selectedNode.id;
                      const partnerId = isSource ? edge.target : edge.source;
                      return (
                        <div
                          key={idx}
                          className="p-2 rounded-lg bg-slate-950/80 border border-slate-800/80 flex items-center justify-between text-[11px]"
                        >
                          <span className="text-slate-400">
                            {isSource ? '→ Points To' : '← Influenced By'}:{' '}
                            <span className="text-indigo-300 font-bold">{partnerId}</span>
                          </span>
                          <span
                            className="font-mono text-[10px] px-1.5 py-0.5 rounded"
                            style={{ color: getEdgeColor(edge.relation) }}
                          >
                            {edge.relation}
                          </span>
                        </div>
                      );
                    })}
                </div>
              </div>

              {/* Invalidation Simulator */}
              <div className="pt-2 border-t border-slate-800">
                <button
                  onClick={() =>
                    setSimulatedInvalidNodeId(
                      simulatedInvalidNodeId === selectedNode.id ? null : selectedNode.id
                    )
                  }
                  className={`w-full py-2.5 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                    simulatedInvalidNodeId === selectedNode.id
                      ? 'bg-rose-600 text-white shadow-lg shadow-rose-600/30'
                      : 'bg-rose-950/40 border border-rose-500/40 text-rose-300 hover:bg-rose-900/50'
                  }`}
                >
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {simulatedInvalidNodeId === selectedNode.id
                    ? 'Clear Invalidation Simulation'
                    : 'Simulate Invalidation Impact'}
                </button>
                {simulatedInvalidNodeId === selectedNode.id && (
                  <p className="text-[10px] text-rose-400 mt-2 leading-relaxed">
                    ⚠️ Simulating breakdown: {invalidatedDescendants.size} downstream decision nodes highlighted in red.
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-600 text-center p-4">
              <Network className="w-8 h-8 mb-2 opacity-30" />
              Select any node in the topology canvas to inspect semantic relationships and simulate invalidation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
