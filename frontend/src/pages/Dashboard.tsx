import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CaseResponse } from '../types';
import { apiClient } from '../api/client';
import { PlusCircle, Scale, Clock, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [cases, setCases] = useState<CaseResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listCases();
      setCases(data);
    } catch (err) {
      console.error('Failed to load cases', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (state: string) => {
    switch (state) {
      case 'CLOSED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'VERDICT_READY':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'ANALYZING':
      case 'INVESTIGATING':
      case 'DEBATING':
      case 'JUDGING':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Hero Welcome */}
      <div className="bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900 border border-slate-800 rounded-3xl p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono uppercase text-indigo-400 mb-2">
            <Scale className="w-4 h-4" />
            Decision Intelligence Control Plane
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Autonomous Decision Validation Court
          </h1>
          <p className="text-sm text-slate-300 mt-2 max-w-2xl leading-relaxed">
            Transform human decisions into structured decision justification graphs. Investigate evidence, conduct adversarial cross-examinations, and deliver calibrated judicial verdicts.
          </p>
        </div>

        <Link
          to="/create"
          className="flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-xl shadow-indigo-500/20 transition-all shrink-0"
        >
          <PlusCircle className="w-5 h-5" />
          Create New Decision Case
        </Link>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs font-mono uppercase text-slate-400">Total Cases Evaluated</div>
          <div className="text-3xl font-bold text-white mt-1 font-mono">{cases.length}</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs font-mono uppercase text-slate-400">Autonomous Agents Ready</div>
          <div className="text-3xl font-bold text-emerald-400 mt-1 font-mono">11 Agents</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs font-mono uppercase text-slate-400">Adjudication Method</div>
          <div className="text-3xl font-bold text-purple-400 mt-1 font-mono">Evidence Graph DAG</div>
        </div>
      </div>

      {/* Cases List Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-400" />
            Decision Case Portfolio
          </h2>
          <span className="text-xs font-mono text-slate-500">{cases.length} cases registered</span>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500 text-sm font-mono">
            Loading decision cases...
          </div>
        ) : cases.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <Scale className="w-10 h-10 mx-auto mb-3 opacity-30" />
            No decision cases found. Click "Create New Decision Case" above to evaluate your first decision.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {cases.map((c) => (
              <Link
                key={c.case_id}
                to={`/cases/${c.case_id}`}
                className="group bg-slate-950/60 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 p-5 rounded-xl transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                <div className="space-y-1 min-w-0 flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-indigo-400 font-semibold">{c.case_id}</span>
                    <span className={`text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full border ${getStatusBadge(c.state)}`}>
                      {c.state}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">v{c.version}</span>
                  </div>
                  <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors truncate">
                    {c.title}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-1">
                    <span className="text-slate-500">Proposed Decision:</span> {c.proposed_decision}
                  </p>
                </div>

                <div className="flex items-center gap-4 text-xs font-mono text-slate-400 shrink-0">
                  <div className="hidden sm:block text-right">
                    <div>{c.data?.claims?.length || 0} Claims</div>
                    <div className="text-slate-500">{c.data?.evidence?.length || 0} Evidence</div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
