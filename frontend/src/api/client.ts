import axios from 'axios';
import { CaseResponse, VerdictData, SensitivityData } from '../types';

const API_BASE = 'http://localhost:8000/api';

export const apiClient = {
  async getHealth() {
    const res = await axios.get(`${API_BASE}/health`);
    return res.data;
  },

  async listCases(): Promise<CaseResponse[]> {
    const res = await axios.get(`${API_BASE}/cases`);
    return res.data;
  },

  async getCase(caseId: string): Promise<CaseResponse> {
    const res = await axios.get(`${API_BASE}/cases/${caseId}`);
    return res.data;
  },

  async createCase(payload: { raw_text?: string; title?: string; problem?: string; proposed_decision?: string; context?: string }): Promise<CaseResponse> {
    const res = await axios.post(`${API_BASE}/cases`, payload);
    return res.data;
  },

  async uploadDocument(caseId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post(`${API_BASE}/cases/${caseId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async startCourt(caseId: string) {
    const res = await axios.post(`${API_BASE}/cases/${caseId}/court/start?background=true`);
    return res.data;
  },

  async getFindings(caseId: string) {
    const res = await axios.get(`${API_BASE}/cases/${caseId}/findings`);
    return res.data;
  },

  async getVerdict(caseId: string): Promise<{ verdict: VerdictData }> {
    const res = await axios.get(`${API_BASE}/cases/${caseId}/verdict`);
    return res.data;
  },

  async submitReview(caseId: string, payload: { action: string; notes: string; override_reason?: string }) {
    const res = await axios.post(`${API_BASE}/cases/${caseId}/review`, payload);
    return res.data;
  },

  async runWhatIf(caseId: string, condition: string): Promise<{ sensitivity_analysis: SensitivityData }> {
    const res = await axios.post(`${API_BASE}/cases/${caseId}/what-if`, { condition });
    return res.data;
  },

  async getAuditLogs(caseId: string) {
    const res = await axios.get(`${API_BASE}/audit/${caseId}`);
    return res.data;
  },

  getExportMarkdownUrl(caseId: string): string {
    return `${API_BASE}/cases/${caseId}/export/markdown`;
  },

  getExportHtmlUrl(caseId: string): string {
    return `${API_BASE}/cases/${caseId}/export/html`;
  },

  downloadMarkdown(caseId: string) {
    const url = `${API_BASE}/cases/${caseId}/export/markdown`;
    window.open(url, '_blank');
  },

  openPrintableHtml(caseId: string) {
    const url = `${API_BASE}/cases/${caseId}/export/html`;
    window.open(url, '_blank');
  },
};
