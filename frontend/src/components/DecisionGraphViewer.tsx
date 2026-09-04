import React, { useState } from 'react';
import { GraphData, GraphNode, GraphEdge } from '../types';
import { Network, ZoomIn, ZoomOut, Filter, Info, ShieldCheck, AlertTriangle, Layers } from 'lucide-react';

interface DecisionGraphViewerProps {
  graph: GraphData;
}

export const DecisionGraphViewer: React.FC<DecisionGraphViewerProps> = ({ graph }) => {
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const nodeTypes = ['ALL', 'CLAIM', 'EVIDENCE', 'ASSUMPTION', 'REQUIREMENT', 'RISK', 'ALTERNATIVE'];

  const filteredNodes = selectedType === 'ALL'
    ? graph.nodes
    : graph.nodes.filter((n) => n.node_type === selectedType);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'DECISION':
      case 'CASE':
        return 'bg-purple-500/20 border-purple-500 text-purple-300';
      case 'CLAIM':
        return 'bg-blue-500/20 border-blue-500 text-blue-300';
      case 'EVIDENCE':
        return 'bg-emerald-500/20 border-emerald-500 text-emerald-300';
      case 'ASSUMPTION':
        return 'bg-amber-500/20 border-amber-500 text-amber-300';
      case 'REQUIREMENT':
      case 'CONSTRAINT':
        return 'bg-indigo-500/20 border-indigo-500 text-indigo-300';
      case 'RISK':
        return 'bg-red-500/20 border-red-500 text-red-300';
      case 'ALTERNATIVE':
        return 'bg-teal-500/20 border-teal-300 text-teal-300';
      default:
        return 'bg-slate-700/30 border-slate-600 text-slate-300';
    }
  };

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/80 border border-slate-800 rounded-xl p-3">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-indigo-400" />
          <span className="font-semibold text-sm text-white">Decision Justification Graph</span>
          <span className="text-xs text-slate-500 font-mono">
            ({graph.nodes.length} nodes, {graph.edges.length} edges)
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {nodeTypes.map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                selectedType === type
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Main Graph Grid / Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Nodes Board */}
        <div className="lg:col-span-2 bg-slate-950/60 border border-slate-800 rounded-2xl p-6 min-h-[480px]">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {filteredNodes.length === 0 ? (
              <div className="col-span-2 text-center text-slate-500 py-12">
                No graph nodes matching selected filter.
              </div>
            ) : (
              filteredNodes.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                const relatedEdges = graph.edges.filter(
                  (e) => e.source === node.id || e.target === node.id
                );

                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${getNodeColor(
                      node.node_type
                    )} ${
                      isSelected
                        ? 'ring-2 ring-indigo-400 scale-[1.02] shadow-lg shadow-indigo-500/20'
                        : 'hover:border-slate-600 hover:bg-slate-900/60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-black/40 border border-current/20">
                        {node.node_type}
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        ID: {node.id}
                      </span>
                    </div>
                    <div className="text-sm font-medium text-slate-200 line-clamp-2">
                      {node.label}
                    </div>

                    <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-slate-400">
                      <span>{relatedEdges.length} connections</span>
                      <span>Conf: {(node.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Node Inspector & Relationship Explorer */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800 mb-4">
            <Info className="w-4 h-4 text-indigo-400" />
            <h3 className="text-xs font-mono uppercase text-slate-300">Node Inspector & Provenance</h3>
          </div>

          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {selectedNode.node_type}
                </span>
                <h4 className="text-base font-semibold text-white mt-2">
                  {selectedNode.label}
                </h4>
                <p className="text-xs font-mono text-slate-400 mt-1">
                  Node Identifier: <code className="text-indigo-400">{selectedNode.id}</code>
                </p>
              </div>

              {/* Edge Relationships */}
              <div>
                <h5 className="text-xs font-mono uppercase text-slate-400 mb-2">
                  Justification Relationships
                </h5>
                <div className="space-y-2">
                  {graph.edges
                    .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((edge, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono flex items-center justify-between"
                      >
                        <span className="text-slate-400">
                          {edge.source === selectedNode.id ? 'Outgoing' : 'Incoming'}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-bold">
                          {edge.relation}
                        </span>
                        <span className="text-slate-300">
                          {edge.source === selectedNode.id ? edge.target : edge.source}
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              {/* Properties */}
              {Object.keys(selectedNode.properties).length > 0 && (
                <div>
                  <h5 className="text-xs font-mono uppercase text-slate-400 mb-2">Properties</h5>
                  <pre className="text-[11px] font-mono bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 overflow-x-auto">
                    {JSON.stringify(selectedNode.properties, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-center p-4">
              <Layers className="w-8 h-8 mb-2 opacity-30" />
              Click any node in the graph to inspect its semantic dependencies, edge weights, and provenance.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
