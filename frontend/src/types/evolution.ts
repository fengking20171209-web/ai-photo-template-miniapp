export interface EvolutionCandidate {
  id: number;
  run_id: number;
  variant_text: string;
  strategy: string;
  status: string;
  promoted_version_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface EvolutionRun {
  id: number;
  prompt_id: number;
  base_version_id: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface EvaluationRecord {
  id: number;
  asset_id: number;
  prompt_version_id: number;
  score: number;
  feedback?: string | null;
  created_at: string;
}
