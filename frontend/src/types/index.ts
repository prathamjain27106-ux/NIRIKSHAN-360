/* =================================================================
   NIRIKSHAN 360 — TypeScript Interfaces
   Maps to Django models & API responses
   ================================================================= */

// ── Auth & Users ──
export type UserRole = 'ADMIN' | 'BUREAU_HEAD' | 'ANALYST' | 'NODAL_OFFICER' | 'AUDITOR';
export type CellType = 'RB' | 'PGRC' | 'ANTI_RAGGING' | 'ICC' | 'SCHOLARSHIP' | '';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  cell: CellType;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

// ── Complaints ──
export type ComplaintStatus =
  | 'SUBMITTED'
  | 'TRIAGED'
  | 'ROUTED'
  | 'UNDER_REVIEW'
  | 'AWAITING_REPLY'
  | 'RESOLVED'
  | 'ESCALATED'
  | 'CLOSED';

export type UrgencyLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type ComplaintCategory =
  | 'FEE_REFUND'
  | 'CERTIFICATE_WITHHOLDING'
  | 'RAGGING'
  | 'SEXUAL_HARASSMENT'
  | 'SCHOLARSHIP_ISSUE'
  | 'APPROVAL_VIOLATION'
  | 'FACULTY_ISSUE'
  | 'INFRASTRUCTURE'
  | 'ADMISSION_IRREGULARITY'
  | 'OTHER';

export type LanguageCode = 'en' | 'hi' | 'hinglish';

export interface Complaint {
  id: string;              // UUID primary key
  tracking_id?: string;    // public case reference, e.g. NIR-2026-00001
  title: string;
  description: string;
  category: ComplaintCategory;
  urgency: UrgencyLevel;
  status: ComplaintStatus;
  language: LanguageCode;
  cell: CellType;
  state: string;           // Indian state
  institution_id: string;
  institution_name: string;
  complainant_encrypted: string;  // AES-GCM encrypted
  complainant_encrypted_display?: string;
  created_at?: string;
  submitted_at?: string;    // legacy demo-data field
  updated_at: string;
  sla_deadline: string;
  sla_breached?: boolean;
  is_overdue?: boolean;
  sla_hours_remaining?: number | null;
  routing_confidence: number;  // 0–100
  needs_human_review: boolean;
  triage_method?: string;
  triage_reasons?: string[];
  assigned_to: string | null;
  assigned_to_username?: string | null;
  is_duplicate_flagged: boolean;
  duplicate_of: string | null;
  evidence_count: number;
  evidence_references?: string[];
  timeline: TimelineEvent[];
}

export interface ComplaintSubmission {
  title: string;
  description: string;
  category: ComplaintCategory;
  institution_name: string;
  state: string;
  language: LanguageCode;
  complainant_name: string;
  complainant_contact: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  action: string;
  actor: string;
  detail: string;
  type: 'submission' | 'triage' | 'routing' | 'review' | 'escalation' | 'resolution' | 'reply' | 'system' | 'override' | 'duplicate';
}

export interface DuplicateCandidate {
  complaint: Complaint;
  similarity_score: number;
  similarity_explanation: string;
  common_terms: string[];
  days_apart: number;
  factors: {
    institution_similarity: number;
    category_similarity: number;
    date_similarity: number;
    text_similarity: number;
  };
}

export interface TriagePreviewResult {
  category: ComplaintCategory;
  priority: UrgencyLevel;
  destination_cell: CellType;
  confidence_score: number;
  reasons: string[];
  triage_method: string;
  needs_human_review: boolean;
  confidence_threshold: number;
  language_detected: string;
}

// ── Institutions ──
export interface Institution {
  id: string;
  name: string;
  aicte_id: string;
  state: string;
  city: string;
  type: 'Engineering' | 'Pharmacy' | 'Management' | 'Architecture' | 'Applied Arts';
  total_complaints: number;
  open_complaints: number;
  resolved_complaints: number;
  compliance_score: number;    // 0–100
  norm_check_status: 'COMPLIANT' | 'PARTIALLY_COMPLIANT' | 'NON_COMPLIANT' | 'INSUFFICIENT_DATA';
  last_inspection: string | null;
  student_count: number;
  established_year: number;
}

export interface NormCheckResult {
  id?: string;
  norm: string;
  category: string;
  status: 'PASS' | 'FAIL' | 'INSUFFICIENT_EVIDENCE' | 'NOT_APPLICABLE';
  finding?: 'SUPPORTED' | 'CONTRADICTED' | 'INSUFFICIENT_EVIDENCE';
  detail: string;
  source: string;
  source_url?: string;
  verified_at?: string | null;
  excerpt?: string;
  field_name?: string;
  reported_value?: string;
  required_norm?: string;
}

export interface ComplianceRadarData {
  institution_id: string;
  institution_name: string;
  dimensions: {
    label: string;
    value: number;    // 0–100
    benchmark: number;
  }[];
}

// ── Case Graph ──
export interface GraphNode {
  id: string;
  label: string;
  type: 'complaint' | 'institution' | 'person' | 'cell' | 'category';
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
  weight?: number;
}

export interface CaseGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  fallback: boolean;    // true if using SQL fallback instead of Neo4j
  engine?: 'neo4j' | 'postgres';
}

// ── Audit ──
export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  actor_role: UserRole;
  action: string;
  target_type: string;
  target_id: string;
  detail: string;
  ip_address: string;
}

// ── Institution Reply ──
export interface InstitutionReply {
  id: string;
  complaint_id: string;
  institution_id: string;
  submitted_by: string;
  submitted_at: string;
  content: string;
  attachments: string[];
  status: 'PENDING_REVIEW' | 'ACCEPTED' | 'REJECTED';
}

// ── Dashboard Analytics ──
export interface DashboardMetrics {
  total_complaints: number;
  pending_triage: number;
  sla_breaches: number;
  resolved_30d: number;
  avg_resolution_days: number;
  complaints_by_cell: Record<string, number>;
  complaints_by_status: Record<string, number>;
  complaints_by_urgency: Record<string, number>;
  monthly_trend: { month: string; received: number; resolved: number }[];
  state_distribution: Record<string, number>;
  sla_performance: { cell: string; within_sla: number; breached: number }[];
}

export interface SystemicPulseAnomaly {
  rule: string;
  confidence_percentage: number;
  current_count: number;
  total_count: number;
  details: string;
  action: string;
}

export interface SystemicPulseAnalysis {
  rule: string;
  supporting_counts: { total_cases: number; unreviewed_cases: number };
  confidence_parameters: {
    unreviewed_ratio: number;
    threshold: number;
    sample_size: number;
  };
  anomalies: SystemicPulseAnomaly[];
}

// ── API Responses ──
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  message?: string;
  [key: string]: unknown;
}

// ── Filters ──
export interface ComplaintFilters {
  status?: ComplaintStatus;
  urgency?: UrgencyLevel;
  cell?: CellType;
  category?: ComplaintCategory;
  state?: string;
  institution?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  needs_review?: boolean;
  page?: number;
}
