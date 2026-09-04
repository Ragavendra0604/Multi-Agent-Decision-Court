import React, { useState } from 'react';
import { VerdictData, VerdictStatus } from '../types';
import {
  Gavel,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  FileCheck,
  CheckCircle2,
  XCircle,
  Edit3,
  HelpCircle,
  TrendingUp,
  ArrowRight,
} from 'lucide-react';
import { apiClient } from '../api/client';

interface VerdictDashboardProps {
  caseId: string;
  verdict: VerdictData | null;
  onReviewSubmitted: () => void;
}

export const VerdictDashboard: React.FC<VerdictDashboardProps> = ({
  caseId,
  verdict,
  onReviewSubmitted,
}) => {
  const [reviewAction, setReviewAction] = useState<'ACCEPT' | 'MODIFY' | 'REJECT'>('ACCEPT');
  const [reviewNotes, setReviewNotes] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [reviewSuccess, setReviewSuccess] = useState<string | null>(null);

  if (!verdict) {
    return (
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-16 text-center text-slate-500">
        <Gavel className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <h3 className="text-base font-medium text-slate-400">No Verdict Available Yet</h3>
        <p className="text-xs text-slate-500 mt-1">
          Initiate court trial in the Live Court Room tab to adjudicate this decision.
        </p>
      </div>
    );
  }

  const getVerdictStyle = (status: VerdictStatus) => {
    switch (status) {
      case 'VALID':
        return 'bg-emerald-500/20 border-emerald-500 text-emerald-300';
      case 'PARTIALLY_VALID':
        return 'bg-blue-500/20 border-blue-500 text-blue-300';
      case 'INVALID':
        return 'bg-red-500/20 border-red-500 text-red-300';
      case 'HIGH_RISK':
        return 'bg-amber-500/20 border-amber-500 text-amber-300';
      case 'INSUFFICIENT_EVIDENCE':
      case 'INCONCLUSIVE':
      case 'REQUIRES_HUMAN_REVIEW':
      default:
        return 'bg-purple-500/20 border-purple-500 text-purple-300';
    }
  };

  const handleReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewNotes.trim()) {
      alert('Please provide review rationale notes.');
      return;
    }

    try {
      setSubmitting(true);
      await apiClient.submitReview(caseId, {
        action: reviewAction,
        notes: reviewNotes,
        override_reason: overrideReason || undefined,
      });
      setReviewSuccess(`Human decision review recorded: ${reviewAction}`);
      onReviewSubmitted();
    } catch (err: any) {
      alert(`Review submission failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Supreme Verdict Card */}
      <div className={`p-8 rounded-2xl border-2 ${getVerdictStyle(verdict.verdict)} shadow-xl`}>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider mb-2 opacity-80">
              <Gavel className="w-4 h-4" />
              Final Judicial Verdict
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight">{verdict.verdict}</h2>
            <p className="text-sm mt-2 opacity-90 max-w-3xl leading-relaxed">
              {verdict.summary_verdict_rationale}
            </p>
          </div>

          <div className="text-right shrink-0 bg-black/30 p-4 rounded-xl border border-current/20 font-mono">
            <div className="text-[11px] uppercase opacity-70">Judicial Confidence</div>
            <div className="text-2xl font-bold">{(verdict.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>
      </div>

      {/* Two Dimensions: Correctness vs Justification (Module 24/53) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-indigo-400">Dimension 1</span>
            <span className="text-xs font-mono text-slate-400">
              Conf: {(verdict.decision_correctness.confidence * 100).toFixed(0)}%
            </span>
          </div>
          <h3 className="text-lg font-bold text-white">Decision Correctness</h3>
          <div className="inline-block px-3 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 font-mono text-xs font-semibold">
            {verdict.decision_correctness.status}
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            {verdict.decision_correctness.summary ||
              'Evaluation of whether the proposed outcome is pragmatically viable and aligned with long-term goals.'}
          </p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-purple-400">Dimension 2</span>
            <span className="text-xs font-mono text-slate-400">
              Conf: {(verdict.decision_justification.confidence * 100).toFixed(0)}%
            </span>
          </div>
          <h3 className="text-lg font-bold text-white">Decision Justification</h3>
          <div className="inline-block px-3 py-1 rounded-lg bg-purple-500/20 text-purple-300 font-mono text-xs font-semibold">
            {verdict.decision_justification.status}
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            {verdict.decision_justification.summary ||
              'Rigorous audit of whether claims are backed by verified evidence without logical gaps or false premises.'}
          </p>
        </div>
      </div>

      {/* Decision Drivers & Recommended Next Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Drivers */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-indigo-400" />
            Critical Decision Drivers
          </h3>
          <ul className="space-y-2">
            {verdict.critical_decision_drivers.map((driver, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                {driver}
              </li>
            ))}
          </ul>
        </div>

        {/* Next Actions */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ArrowRight className="w-4 h-4 text-emerald-400" />
            Recommended Next Actions
          </h3>
          <ul className="space-y-2">
            {verdict.recommended_next_actions.map((act, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                <span className="font-mono text-[10px] text-emerald-400 font-bold mt-0.5">
                  0{idx + 1}.
                </span>
                {act}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Human-in-the-Loop Review Box (Module 36) */}
      <div className="bg-gradient-to-br from-slate-900 to-indigo-950/40 border border-indigo-500/30 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white">Human-in-the-Loop Judicial Review</h3>
          </div>
          <span className="text-xs font-mono text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded-full border border-indigo-500/20">
            Module 36 Governance
          </span>
        </div>

        {reviewSuccess ? (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-mono flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            {reviewSuccess}
          </div>
        ) : (
          <form onSubmit={handleReview} className="space-y-4">
            <div className="flex items-center gap-3">
              {(['ACCEPT', 'MODIFY', 'REJECT'] as const).map((action) => (
                <button
                  type="button"
                  key={action}
                  onClick={() => setReviewAction(action)}
                  className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all ${
                    reviewAction === action
                      ? action === 'ACCEPT'
                        ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/20'
                        : action === 'MODIFY'
                        ? 'bg-amber-600 text-white shadow-lg shadow-amber-500/20'
                        : 'bg-red-600 text-white shadow-lg shadow-red-500/20'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {action} VERDICT
                </button>
              ))}
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Reviewer Evaluation Notes:
              </label>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Enter executive sign-off reasoning or decision modifications..."
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {reviewAction !== 'ACCEPT' && (
              <div>
                <label className="block text-xs font-mono text-amber-400 mb-1">
                  Human Override Justification:
                </label>
                <input
                  type="text"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="Explain why the AI Court recommendations were modified or overridden..."
                  className="w-full bg-slate-950 border border-amber-500/30 rounded-xl p-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs font-mono transition-colors disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Record Human Sign-Off & Close Case'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
