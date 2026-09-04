import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Sparkles, FileText, ArrowRight, Layers, HelpCircle, CheckCircle } from 'lucide-react';

export const CreateCase: React.FC = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'NATURAL_LANGUAGE' | 'STRUCTURED'>('NATURAL_LANGUAGE');
  const [rawText, setRawText] = useState('');
  const [title, setTitle] = useState('');
  const [problem, setProblem] = useState('');
  const [proposedDecision, setProposedDecision] = useState('');
  const [context, setContext] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const samplePrompt = `Should we migrate our backend databases from self-hosted MySQL to Solution X Distributed Cloud?
Our main problems are query latency spikes during peak promotions and high DevOps maintenance costs.
Proposed Decision: Migrate all production checkouts to Solution X.
Requirements: Keep total migration budget under $100k and maintain 99.99% uptime.
Evidence: Vendor load test shows 40% latency reduction.
Assumptions: Engineering team can complete schema migration in 1 month without extra contractor hires.`;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      let payload: any = {};
      if (mode === 'NATURAL_LANGUAGE') {
        if (!rawText.trim()) {
          alert('Please enter your decision case text.');
          return;
        }
        payload = { raw_text: rawText, title: title || undefined };
      } else {
        if (!problem.trim() || !proposedDecision.trim()) {
          alert('Problem and Proposed Decision are required.');
          return;
        }
        payload = {
          title: title || 'Untitled Decision Case',
          problem,
          proposed_decision: proposedDecision,
          context,
        };
      }

      const res = await apiClient.createCase(payload);
      navigate(`/cases/${res.case_id}`);
    } catch (err: any) {
      alert(`Case creation failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      <div>
        <div className="flex items-center gap-2 text-xs font-mono uppercase text-indigo-400 mb-1">
          <Layers className="w-4 h-4" />
          Universal Case Ingestion
        </div>
        <h1 className="text-2xl font-bold text-white">Create & Decompose Decision Case</h1>
        <p className="text-sm text-slate-400 mt-1">
          Enter free-form natural language text or structured problem fields. The Natural Language Decomposer will automatically extract atomic claims, assumptions, requirements, and risks.
        </p>
      </div>

      {/* Mode Switcher */}
      <div className="flex items-center gap-3 bg-slate-900 p-1.5 rounded-xl border border-slate-800 w-fit">
        <button
          type="button"
          onClick={() => setMode('NATURAL_LANGUAGE')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-medium transition-all ${
            mode === 'NATURAL_LANGUAGE'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Natural Language AI Decomposer (Recommended)
        </button>
        <button
          type="button"
          onClick={() => setMode('STRUCTURED')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-medium transition-all ${
            mode === 'STRUCTURED'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <FileText className="w-4 h-4" />
          Structured Manual Fields
        </button>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">Case Title (Optional)</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Migration to Solution X Architecture"
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {mode === 'NATURAL_LANGUAGE' ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-mono text-slate-400">
                Decision Narrative / Unstructured Meeting Notes:
              </label>
              <button
                type="button"
                onClick={() => setRawText(samplePrompt)}
                className="text-[11px] font-mono text-indigo-400 hover:underline"
              >
                Insert Sample Case
              </button>
            </div>
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Describe your decision, the problem you are solving, the rationale, requirements, assumptions, and any known risks..."
              rows={8}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-sans leading-relaxed"
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Problem Statement *</label>
              <textarea
                value={problem}
                onChange={(e) => setProblem(e.target.value)}
                placeholder="What is the core issue or bottleneck?"
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Proposed Decision *</label>
              <textarea
                value={proposedDecision}
                onChange={(e) => setProposedDecision(e.target.value)}
                placeholder="What specific action or solution are you proposing?"
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Background Context</label>
              <textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Additional organizational, technical, or financial context..."
                rows={2}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        )}

        <div className="pt-4 border-t border-slate-800 flex items-center justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold text-sm shadow-lg shadow-indigo-500/25 transition-all disabled:opacity-50"
          >
            {submitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Decomposing Case...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Decompose & Open Case Workspace
                <ArrowRight className="w-4 h-4 ml-1" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
