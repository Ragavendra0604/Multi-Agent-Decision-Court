import React from 'react';
import { ArgumentItem, CrossExamTurnItem } from '../types';
import { ShieldAlert, ShieldCheck, Swords, Scale, AlertOctagon, CheckCircle2 } from 'lucide-react';

interface AdversarialDebateViewProps {
  argumentsList: ArgumentItem[];
  crossExaminations: CrossExamTurnItem[];
}

export const AdversarialDebateView: React.FC<AdversarialDebateViewProps> = ({
  argumentsList,
  crossExaminations,
}) => {
  const prosArgs = argumentsList.filter((a) => a.side === 'PROSECUTION');
  const defArgs = argumentsList.filter((a) => a.side === 'DEFENSE');

  return (
    <div className="space-y-8">
      {/* Prosecution vs Defense Side-by-Side Counsel Chamber */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Prosecution Side */}
        <div className="bg-red-950/20 border border-red-500/30 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-red-500/20">
            <ShieldAlert className="w-5 h-5 text-red-400" />
            <h3 className="text-base font-bold text-red-300">Prosecution Counsel (Opposition)</h3>
          </div>

          {prosArgs.length === 0 ? (
            <div className="text-center text-slate-500 py-8 text-xs font-mono">
              Prosecution challenges will appear once the court session executes.
            </div>
          ) : (
            <div className="space-y-3">
              {prosArgs.map((arg, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/80 border border-red-500/20 rounded-xl p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-red-200">{arg.title}</h4>
                    <span className="text-[10px] font-mono text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                      Severity: {(arg.severity_or_strength * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">{arg.statement}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Defense Side */}
        <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-emerald-500/20">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-emerald-300">Defense Counsel (Advocate)</h3>
          </div>

          {defArgs.length === 0 ? (
            <div className="text-center text-slate-500 py-8 text-xs font-mono">
              Defense arguments will appear once the court session executes.
            </div>
          ) : (
            <div className="space-y-3">
              {defArgs.map((arg, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/80 border border-emerald-500/20 rounded-xl p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-emerald-200">{arg.title}</h4>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      Strength: {(arg.severity_or_strength * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">{arg.statement}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Cross-Examination Exchange Transcript */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Swords className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-white">Cross-Examination Transcript</h3>
          </div>
          <span className="text-xs font-mono text-slate-500">Module 20 Dynamic Debate</span>
        </div>

        {crossExaminations.length === 0 ? (
          <div className="text-center text-slate-500 py-10 text-xs font-mono">
            No cross-examination rounds executed yet.
          </div>
        ) : (
          <div className="space-y-4">
            {crossExaminations.map((turn) => (
              <div
                key={turn.turn_id}
                className="bg-slate-950/70 border border-slate-800 rounded-xl p-5 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold font-mono text-indigo-400">
                      Round {turn.round_number}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      Target: <code className="text-amber-400">{turn.target_claim_id}</code>
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full border ${
                      turn.resolution_state === 'RESOLVED'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    Status: {turn.resolution_state}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-red-950/30 border border-red-500/20 rounded-lg">
                    <span className="font-bold text-red-400 block mb-1">Prosecution Challenge:</span>
                    <p className="text-slate-200">{turn.challenge}</p>
                  </div>

                  <div className="p-3 bg-emerald-950/30 border border-emerald-500/20 rounded-lg">
                    <span className="font-bold text-emerald-400 block mb-1">Defense Rebuttal:</span>
                    <p className="text-slate-200">{turn.defense_response}</p>
                  </div>
                </div>

                {turn.unresolved_uncertainty && (
                  <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs font-mono text-amber-300">
                    <span className="font-bold">Unresolved Empirical Gap:</span> {turn.unresolved_uncertainty}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
