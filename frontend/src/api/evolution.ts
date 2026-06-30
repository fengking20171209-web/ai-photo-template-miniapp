import { EvolutionRun, EvolutionCandidate, EvaluationRecord } from '../types/evolution';

const API_BASE = '/api/prompt-evolution';

export const createEvolutionRun = async (promptId: number, baseVersionId: number): Promise<EvolutionRun> => {
  const res = await fetch(`${API_BASE}/runs?prompt_id=${promptId}&base_version_id=${baseVersionId}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to create run');
  return res.json();
};

export const getEvolutionRuns = async (promptId: number): Promise<EvolutionRun[]> => {
  const res = await fetch(`${API_BASE}/runs/${promptId}`);
  if (!res.ok) throw new Error('Failed to fetch runs');
  return res.json();
};

export const getCandidates = async (runId: number): Promise<EvolutionCandidate[]> => {
  const res = await fetch(`${API_BASE}/runs/${runId}/candidates`);
  if (!res.ok) throw new Error('Failed to fetch candidates');
  return res.json();
};

export const promoteCandidate = async (candidateId: number, changeNote?: string): Promise<EvolutionCandidate> => {
  const res = await fetch(`${API_BASE}/candidates/${candidateId}/promote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ change_note: changeNote }),
  });
  if (!res.ok) throw new Error('Failed to promote');
  return res.json();
};

export const rejectCandidate = async (candidateId: number): Promise<EvolutionCandidate> => {
  const res = await fetch(`${API_BASE}/candidates/${candidateId}/reject`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to reject');
  return res.json();
};

export const createEvaluation = async (assetId: number, promptVersionId: number, score: number, feedback?: string): Promise<EvaluationRecord> => {
  const res = await fetch(`${API_BASE}/evaluations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ asset_id: assetId, prompt_version_id: promptVersionId, score, feedback }),
  });
  if (!res.ok) throw new Error('Failed to evaluate');
  return res.json();
};

export const getEvaluations = async (assetId: number): Promise<EvaluationRecord[]> => {
  const res = await fetch(`${API_BASE}/evaluations/asset/${assetId}`);
  if (!res.ok) throw new Error('Failed to fetch evaluations');
  return res.json();
};

export const getBaseVersion = async (versionId: number): Promise<any> => {
  const res = await fetch(`${API_BASE}/base-version/${versionId}`);
  if (!res.ok) throw new Error('Failed to fetch base version');
  return res.json();
};

