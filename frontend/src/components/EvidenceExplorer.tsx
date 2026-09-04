import React, { useState } from 'react';
import { EvidenceItem } from '../types';
import { FileText, Upload, ShieldCheck, Tag, Calendar, User, CheckCircle, AlertTriangle } from 'lucide-react';
import { apiClient } from '../api/client';

interface EvidenceExplorerProps {
  caseId: string;
  evidence: EvidenceItem[];
  onEvidenceUploaded: () => void;
}

export const EvidenceExplorer: React.FC<EvidenceExplorerProps> = ({
  caseId,
  evidence,
  onEvidenceUploaded,
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      await apiClient.uploadDocument(caseId, file);
      setUploadSuccess(`Ingested "${file.name}" into Evidence Pool.`);
      onEvidenceUploaded();
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Box */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Upload className="w-5 h-5 text-indigo-400" />
            Ingest Searchable Evidence Documents
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Upload PDF, DOCX, TXT, or JSON benchmark/financial reports. Automatically chunked, sanitized against prompt injection, and indexed with BM25.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="cursor-pointer flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors">
            {uploading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Ingesting...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload Document
              </>
            )}
            <input
              type="file"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
              accept=".pdf,.docx,.doc,.txt,.json,.csv"
            />
          </label>
        </div>
      </div>

      {uploadSuccess && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 font-mono flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-400" />
          {uploadSuccess}
        </div>
      )}

      {/* Evidence Catalog Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono uppercase text-slate-400 tracking-wider">
            Verifiable Evidence Records ({evidence.length} items)
          </h3>
          <span className="text-xs text-slate-500 font-mono">Module 6 Provenance</span>
        </div>

        {evidence.length === 0 ? (
          <div className="bg-slate-950/40 border border-slate-900 rounded-2xl p-12 text-center text-slate-500">
            <FileText className="w-10 h-10 mx-auto mb-3 opacity-30" />
            No external evidence records attached yet. Upload documents or enter evidence during case creation.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {evidence.map((ev) => (
              <div
                key={ev.evidence_id}
                className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    {ev.source_type}
                  </span>
                  <span className="text-xs font-mono text-slate-400">
                    ID: {ev.evidence_id}
                  </span>
                </div>

                <p className="text-sm text-slate-200 leading-relaxed font-sans">
                  "{ev.content}"
                </p>

                {ev.source_reference && (
                  <div className="text-xs text-slate-400 flex items-center gap-1.5 font-mono">
                    <FileText className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Provenance: {ev.source_reference}</span>
                  </div>
                )}

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
                  <div className="flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Reliability: {(ev.reliability * 100).toFixed(0)}%</span>
                  </div>
                  <div>Strength: {(ev.strength * 100).toFixed(0)}%</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
