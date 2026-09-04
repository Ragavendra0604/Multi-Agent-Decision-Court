import React from 'react';
import { CourtEvent, CaseState } from '../types';
import {
  Gavel,
  ShieldAlert,
  ShieldCheck,
  Search,
  Cpu,
  Swords,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileSearch,
  Sparkles,
  GitPullRequestDraft,
  Scale,
} from 'lucide-react';

interface LiveCourtRoomProps {
  caseId: string;
  state: CaseState;
  events: CourtEvent[];
  onStartCourt: () => void;
  isRunning: boolean;
}

export const LiveCourtRoom: React.FC<LiveCourtRoomProps> = ({
  caseId,
  state,
  events,
  onStartCourt,
  isRunning,
}) => {
  const phases = [
    { key: 'SUBMITTED', label: 'Submitted' },
    { key: 'ANALYZING', label: 'Case Analyst' },
    { key: 'INVESTIGATING', label: 'Parallel Audit' },
    { key: 'DEBATING', label: 'Adversarial Debate' },
    { key: 'RECONCILING', label: 'Reconciliation' },
    { key: 'JUDGING', label: 'Supreme Judge' },
    { key: 'VERDICT_READY', label: 'Verdict Ready' },
  ];

  const currentPhaseIndex = phases.findIndex((p) => p.key === state);

  const agents = [
    { name: 'Case Analyst', role: 'Scope & Boundary Framing', icon: FileSearch, state: state !== 'DRAFT' && state !== 'SUBMITTED' ? 'completed' : 'waiting' },
    { name: 'Claim Decomposer', role: 'Atomic Testable Claims', icon: GitPullRequestDraft, state: state !== 'DRAFT' && state !== 'SUBMITTED' ? 'completed' : 'waiting' },
    { name: 'Evidence Investigator', role: 'Support & Provenance Scoring', icon: Search, state: ['INVESTIGATING', 'DEBATING', 'RECONCILING', 'JUDGING', 'VERDICT_READY', 'HUMAN_REVIEW', 'CLOSED'].includes(state) ? 'completed' : isRunning ? 'active' : 'waiting' },
    { name: 'Logic Analyst', role: '10-Fallacy Audit & Reasoning Gaps', icon: Cpu, state: ['INVESTIGATING', 'DEBATING', 'RECONCILING', 'JUDGING', 'VERDICT_READY', 'HUMAN_REVIEW', 'CLOSED'].includes(state) ? 'completed' : isRunning ? 'active' : 'waiting' },
    { name: 'Requirement Validator', role: 'Constraint Compliance Matrix', icon: ShieldCheck, state: ['INVESTIGATING', 'DEBATING', 'RECONCILING', 'JUDGING', 'VERDICT_READY', 'HUMAN_REVIEW', 'CLOSED'].includes(state) ? 'completed' : isRunning ? 'active' : 'waiting' },
    { name: 'Assumption Auditor', role: 'Hidden & Explicit Assumptions', icon: AlertCircle, state: ['INVESTIGATING', 'DEBATING', 'RECONCILING', 'JUDGING', 'VERDICT_READY', 'HUMAN_REVIEW', 'CLOSED'].includes(state) ? 'completed' : isRunning ? 'active' : 'waiting' },
    { name: 'Prosecution Counsel', role: 'Counter-evidence & Failure Modes', icon: ShieldAlert, state: ['DEBATING', 'RECONCILING', 'JUDGING', 'VERDICT_READY', 'HUMAN_REVIEW', 'CLOSED'].includes(state) ? 'completed' : state === 'DEBATING' ? 'active' : 'waiting', color: 'text-red-400' },
    { name: 'Defense Counsel', role: 'Justification & Concessions', icon: ShieldCheck, state: ['DEBATING', 'RECONCILING', 'JUDGING', 'VERDICT_READY', 'HUMAN_REVIEW', 'CLOSED'].includes(state) ? 'completed' : state === 'DEBATING' ? 'active' : 'waiting', color: 'text-emerald-400' },
    { name: 'Cross Examiner', role: 'Adversarial Multi-Round Debate', icon: Swords, state: ['RECONCILING', 'JUDGING', 'VERDICT_READY', 'HUMAN_REVIEW', 'CLOSED'].includes(state) ? 'completed' : state === 'DEBATING' ? 'active' : 'waiting' },
    { name: 'Evidence Reconciliation', role: 'Authority & Recency Arbiter', icon: Scale, state: ['JUDGING', 'VERDICT_READY', 'HUMAN_REVIEW', 'CLOSED'].includes(state) ? 'completed' : state === 'RECONCILING' ? 'active' : 'waiting' },
    { name: 'Supreme Judge', role: 'Calibrated Verdict Adjudicator', icon: Gavel, state: ['VERDICT_READY', 'HUMAN_REVIEW', 'CLOSED'].includes(state) ? 'completed' : state === 'JUDGING' ? 'active' : 'waiting', color: 'text-amber-400' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner with Action Button */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Gavel className="w-5 h-5 text-amber-400" />
              Live Multi-Agent Court Room
            </h2>
            <span className="font-mono text-xs px-2.5 py-0.5 rounded-full border border-indigo-500/30 bg-indigo-500/20 text-indigo-300">
              State: {state}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time autonomous courtroom trial evaluating decision correctness vs justification.
          </p>
        </div>

        {state === 'DRAFT' || state === 'SUBMITTED' ? (
          <button
            onClick={onStartCourt}
            disabled={isRunning}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold shadow-lg shadow-indigo-500/25 transition-all disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Court In Session...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Summon Court & Begin Trial
              </>
            )}
          </button>
        ) : (
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Court Adjudication Active
          </div>
        )}
      </div>

      {/* Trial Phase Progress Indicator */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-xs font-mono uppercase text-slate-400 mb-4 tracking-wider">
          Courtroom Proceedings Timeline
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-7 gap-2">
          {phases.map((p, idx) => {
            const isDone = currentPhaseIndex >= idx;
            const isCurrent = currentPhaseIndex === idx || (isRunning && currentPhaseIndex + 1 === idx);
            return (
              <div
                key={p.key}
                className={`p-3 rounded-xl border text-center transition-all ${
                  isCurrent
                    ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300 font-semibold shadow-md shadow-indigo-500/10 animate-pulse'
                    : isDone
                    ? 'bg-slate-800/60 border-emerald-500/40 text-slate-300'
                    : 'bg-slate-950/40 border-slate-800/80 text-slate-600'
                }`}
              >
                <div className="text-[10px] font-mono text-slate-500 mb-1">0{idx + 1}</div>
                <div className="text-xs font-medium">{p.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Court Room Grid: Specialized Agents & Live Event Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Autonomous Agent Chamber */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-mono uppercase text-slate-400 tracking-wider">
              Autonomous Court Chamber (11 Specialized Agents)
            </h3>
            <span className="text-xs text-slate-500 font-mono">Parallel Execution DAG</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {agents.map((agent) => {
              const Icon = agent.icon;
              return (
                <div
                  key={agent.name}
                  className={`p-4 rounded-xl border transition-all flex items-start gap-3 ${
                    agent.state === 'active'
                      ? 'bg-indigo-950/40 border-indigo-500/60 ring-1 ring-indigo-500/30 shadow-lg shadow-indigo-500/10'
                      : agent.state === 'completed'
                      ? 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                      : 'bg-slate-950/40 border-slate-900 opacity-60'
                  }`}
                >
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                      agent.state === 'active'
                        ? 'bg-indigo-500 text-white animate-pulse'
                        : agent.state === 'completed'
                        ? 'bg-slate-800 text-slate-300'
                        : 'bg-slate-900 text-slate-600'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${agent.color || ''}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-1">
                      <h4 className="text-sm font-semibold text-white truncate">{agent.name}</h4>
                      {agent.state === 'completed' && (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      )}
                      {agent.state === 'active' && (
                        <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5 truncate">{agent.role}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Live Courtroom Stream Log */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col h-[520px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <h3 className="text-xs font-mono uppercase text-slate-400 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-indigo-400" />
              Live Court Stream
            </h3>
            <span className="text-[10px] font-mono text-slate-500">{events.length} events logged</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs font-mono">
            {events.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 text-center p-4">
                <Gavel className="w-8 h-8 mb-2 opacity-30" />
                Court awaiting trial initiation. Click 'Summon Court' above.
              </div>
            ) : (
              events.map((evt) => (
                <div key={evt.event_id} className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
                  <div className="flex items-center justify-between text-[10px] text-indigo-400 mb-1">
                    <span className="font-bold">[{evt.phase}]</span>
                    <span className="text-slate-500">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className="text-slate-300 text-xs font-sans leading-relaxed">{evt.message}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
