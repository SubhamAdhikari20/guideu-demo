export interface ScamReport {
  id: number;
  service_type: string;
  region: string;
  season: string | null;
  quoted_price_npr: number;
  benchmark_price_npr: number | null;
  overcharge_ratio: number;
  scam_severity: string;
  was_flagged_by_app: boolean;
  ml_scam_probability: number | null;
  status: 'SUBMITTED' | 'VERIFIED' | 'DISMISSED';
  verified_by_moderator: boolean;
  description: string;
  created_at: string;
}
