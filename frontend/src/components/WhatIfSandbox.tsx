import React, { useState } from 'react';
import { SensitivityData } from '../types';
import { Sliders, Play, AlertCircle, ArrowRight, CheckCircle, ShieldAlert } from 'lucide-react';
import { apiClient } from '../api/client';

interface WhatIfSandboxProps {
  caseId: string;
}

export const WhatIfSandbox: React.FC<WhatIfSandboxProps> = ({ caseId }) => {
  const [customCondition, setCustomCondition] = useState('');
  const [loading, setLoading] = useState(false);
  const [sensitivityResult, setSensitivityResult] = useState<SensitivityData | null>(null);

  const presetScenarios = [
    'What if operational cloud egress cost increases by 100%?',
    'What if engineering staff requires 3 months of paid retraining?',
    'What if vendor SLA availability drops from 99.99% to 99.5%?',
    'What if migration budget is slashed from $100k to $50k?',
  ];

  const handleRunWhatIf = async (conditionToRun: string) => {
    if (!conditionToRun.trim()) return;
    try {
      setLoading(true);
      const res = await apiClient.runWhatIf(caseId, conditionToRun);
      setSensitivityResult(res.sensitivity_analysis);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}. Please ensure court session has executed.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Sandbox Header */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800 mb-4">
          <Sliders className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-base font-bold text-white">Sensitivity & What-If Stress Testing</h3>
            <p className="text-xs text-slate-400">
              Module 23: Explore decision fragility thresholds and simulated alternative pivots.
            </p>
          </div>
        </div>

        {/* Input Box */}
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={customCondition}
            onChange={(e) => setCustomCondition(e.target.value)}
            placeholder="Type custom hypothesis (e.g. What if cross-region latency spikes by 50ms?)..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={() => handleRunWhatIf(customCondition)}
            disabled={loading || !customCondition.trim()}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs font-mono transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shrink-0"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5" />
            )}
            Simulate What-If
          </button>
        </div>

        {/* Preset Pills */}
        <div className="mt-4">
          <span className="text-[11px] font-mono text-slate-500 block mb-2">Preset Stress-Tests:</span>
          <div className="flex flex-wrap gap-2">
            {presetScenarios.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setCustomCondition(preset);
                  handleRunWhatIf(preset);
                }}
                className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 hover:border-indigo-500/50 hover:text-white transition-colors text-left"
              >
                {preset}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results Display */}
      {sensitivityResult && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <span className="text-xs font-mono uppercase text-indigo-400">Simulation Output</span>
              <h4 className="text-base font-bold text-white mt-0.5">Stress-Test Evaluation</h4>
            </div>
            <div className="text-right font-mono text-xs">
              <span className="text-slate-400">Robustness Score: </span>
              <span className="text-emerald-400 font-bold">
                {(sensitivityResult.robustness_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Fragile Assumptions & Thresholds */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-2">
              <span className="text-xs font-mono font-bold text-amber-400 flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" />
                Most Fragile Assumptions
              </span>
              <ul className="space-y-1 text-xs text-slate-300">
                {sensitivityResult.most_fragile_assumptions.map((a, i) => (
                  <li key={i}>• {a}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 space-y-2">
              <span className="text-xs font-mono font-bold text-red-400 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4" />
                Critical Tipping Thresholds
              </span>
              <ul className="space-y-1 text-xs text-slate-300">
                {sensitivityResult.critical_cost_or_risk_thresholds.map((t, i) => (
                  <li key={i}>• {t}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Scenarios */}
          <div className="space-y-3">
            <h5 className="text-xs font-mono uppercase text-slate-400">Simulated Scenarios</h5>
            {sensitivityResult.scenarios.map((scen) => (
              <div
                key={scen.scenario_id}
                className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{scen.scenario_title}</span>
                  <span className="font-mono text-[10px] px-2.5 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/30">
                    Impact: {scen.verdict_impact}
                  </span>
                </div>
                <p className="text-slate-300">
                  <span className="text-slate-400 font-mono">Hypothesis:</span> {scen.condition_tested}
                </p>
                {scen.tipping_point_threshold && (
                  <p className="text-amber-300 font-mono">
                    <span className="text-slate-400">Tipping Point:</span> {scen.tipping_point_threshold}
                  </p>
                )}
                {scen.recommended_pivot && (
                  <div className="pt-2 border-t border-slate-900 flex items-center gap-2 text-emerald-400 font-mono">
                    <ArrowRight className="w-3.5 h-3.5" />
                    <span>Recommended Pivot: {scen.recommended_pivot}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
