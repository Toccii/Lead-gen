export type LeadStatus =
  | "nuovo"
  | "inviata"
  | "risposto"
  | "follow_up_inviato"
  | "chiuso_senza_risposta"
  | "opt_out";

export interface Campaign {
  id: number;
  name: string;
  is_active: boolean;
  industries: string[];
  company_size_min: number | null;
  company_size_max: number | null;
  revenue_min: string | null;
  revenue_max: string | null;
  geography: string[];
  target_roles: string[];
  keywords: string[];
  max_leads_per_cycle: number;
  email_tone_of_voice: string | null;
  followup_offer_text: string | null;
  followup_delay_business_days: number;
  close_after_days: number;
  created_at: string;
  updated_at: string;
}

export interface Lead {
  id: number;
  campaign_id: number;
  company_name: string;
  contact_first_name: string | null;
  contact_last_name: string | null;
  role_title: string | null;
  email: string | null;
  website: string | null;
  linkedin_company_url: string | null;
  industry: string | null;
  company_size: number | null;
  source: string;
  status: LeadStatus;
  legal_basis: string;
  created_at: string;
}

export interface ExecutionLog {
  id: number;
  job_type: string;
  campaign_id: number | null;
  status: "running" | "success" | "failed" | "partial";
  started_at: string;
  finished_at: string | null;
  summary: Record<string, unknown>;
}

export interface DashboardMetrics {
  total_leads: number;
  emails_sent_this_week: number;
  response_rate: number;
  funnel: Record<string, number>;
}
