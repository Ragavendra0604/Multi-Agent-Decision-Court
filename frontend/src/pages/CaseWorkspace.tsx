import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { CaseResponse, VerdictData, CourtEvent, ArgumentItem, CrossExamTurnItem } from '../types';
import { apiClient } from '../api/client';
import { LiveCourtRoom } from '../components/LiveCourtRoom';
import { DecisionGraphViewer } from '../components/DecisionGraphViewer';
import { EvidenceExplorer } from '../components/EvidenceExplorer';
import { AdversarialDebateView } from '../components/AdversarialDebateView';
import { VerdictDashboard } from '../components/VerdictDashboard';
import { WhatIfSandbox } from '../components/WhatIfSandbox';
import {
  Gavel,
  Network,
  FileText,
  Swords,
  Sliders,
  Award,
  ArrowLeft,
  Activity,
  Layers,
  History,
} from 'lucide-react';

export const CaseWorkspace: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const [caseData, setCaseData] = useState<CaseResponse | null>(null);
  const [verdict, setVerdict] = useState<VerdictData | null>(null);
  const [events, setEvents] = useState<CourtEvent[]>([]);
  const [argumentsList, setArgumentsList] = useState<ArgumentItem[]>([]);
  const [crossExams, setCrossExams] = useState<CrossExamTurnItem[]>([]);
  const [activeTab, setActiveTab] = useState<string>('court');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (caseId) {
      loadCase();
      loadVerdict();
      loadFindings();
      setupWebSocket();
    }
  }, [caseId]);

  const loadCase = async () => {
    if (!caseId) return;
    try {
      setLoading(true);
      const res = await apiClient.getCase(caseId);
      setCaseData(res);
    } catch (err) {
      console.error('Failed to load case', err);
    } finally {
      setLoading(false);
    }
  };

  const loadVerdict = async () => {
    if (!caseId) return;
    try {
      const res = await apiClient.getVerdict(caseId);
      setVerdict(res.verdict);
    } catch {
      // Verdict might not exist yet
      setVerdict(null);
    }
  };

  const loadFindings = async () => {
    if (!caseId) return;
    try {
      const res = await apiClient.getFindings(caseId);
      setArgumentsList(res.arguments || []);
      setCrossExams(res.cross_examinations || []);
    } catch (err) {
      console.error('Failed to load findings', err);
    }
  };

  const setupWebSocket = () => {
    if (!caseId) return;
    try {
      const socket = new WebSocket(`ws://localhost:8000/api/cases/${caseId}/ws`);
      socket.onmessage = (msg) => {
        try {
          const data: CourtEvent = JSON.parse(msg.data);
          setEvents((prev) => [...prev, data]);
          if (data.phase === 'VERDICT_READY') {
            loadCase();
            loadVerdict();
            loadFindings();
            setIsRunning(false);
          }
        } catch (e) {
          console.error('WS parse error', e);
        }
      };
      socket.onerror = (err) => {
        console.warn('WebSocket status:', err);
      };
    } catch (e) {
      console.warn('WS connection failed', e);
    }
  };

  const handleStartCourt = async () => {
    if (!caseId) return;
    try {
      setIsRunning(true);
      const res = await apiClient.startCourt(caseId);
      setVerdict(res.verdict);
      loadCase();
      loadFindings();
      setActiveTab('verdict');
    } catch (err: any) {
      alert(`Court execution error: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  if (loading || !caseData) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-24 text-center text-slate-500 font-mono">
        <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        Loading Decision Case Workspace...
      </div>
    );
  }

  const tabs = [
    { id: 'court', label: 'Live Court Room', icon: Gavel },
    { id: 'graph', label: 'Decision Graph', icon: Network },
    { id: 'evidence', label: 'Evidence & Documents', icon: FileText },
    { id: 'debate', label: 'Adversarial Debate', icon: Swords },
    { id: 'whatif', label: 'What-If Sandbox', icon: Sliders },
    { id: 'verdict', label: 'Verdict & Report', icon: Award },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Back Link & Case Header */}
      <div className="space-y-3">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Portfolio
        </Link>

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
          <div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs text-indigo-400 font-bold bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20">
                {caseData.case_id}
              </span>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full border border-slate-700 bg-slate-800 text-slate-300">
                State: {caseData.state}
              </span>
              <span className="text-xs font-mono text-slate-500">Version {caseData.version}</span>
            </div>
            <h1 className="text-2xl font-bold text-white mt-1">{caseData.title}</h1>
            <p className="text-xs text-slate-400 mt-1 max-w-3xl line-clamp-2">
              <span className="text-slate-500">Proposed Decision:</span> {caseData.proposed_decision}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right text-xs font-mono text-slate-400 hidden sm:block">
              <div>{caseData.data?.claims?.length || 0} Claims Extracted</div>
              <div className="text-slate-500">{caseData.data?.evidence?.length || 0} Evidence Items</div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 overflow-x-auto pb-px">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-mono font-medium border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
              {tab.id === 'verdict' && verdict && (
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'court' && (
          <LiveCourtRoom
            caseId={caseId!}
            state={caseData.state}
            events={events}
            onStartCourt={handleStartCourt}
            isRunning={isRunning}
          />
        )}

        {activeTab === 'graph' && <DecisionGraphViewer graph={caseData.graph} />}

        {activeTab === 'evidence' && (
          <EvidenceExplorer
            caseId={caseId!}
            evidence={caseData.data?.evidence || []}
            onEvidenceUploaded={() => {
              loadCase();
              loadFindings();
            }}
          />
        )}

        {activeTab === 'debate' && (
          <AdversarialDebateView
            argumentsList={argumentsList}
            crossExaminations={crossExams}
          />
        )}

        {activeTab === 'whatif' && <WhatIfSandbox caseId={caseId!} />}

        {activeTab === 'verdict' && (
          <VerdictDashboard
            caseId={caseId!}
            verdict={verdict}
            onReviewSubmitted={() => {
              loadCase();
              loadVerdict();
            }}
          />
        )}
      </div>
    </div>
  );
};
