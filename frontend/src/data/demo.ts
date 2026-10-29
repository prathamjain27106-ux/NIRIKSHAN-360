/* =================================================================
   ⚠  NIRIKSHAN 360 — SYNTHETIC DEMO DATA
   
   This module contains FABRICATED fixture data used ONLY when the
   backend API endpoints are not yet available. Every screen that
   renders this data shows a visible "DEMO DATA" label.
   
   This data does NOT represent any real AICTE complaints, 
   institutions, or persons.
   ================================================================= */

import type {
  Complaint, Institution, NormCheckResult, ComplianceRadarData,
  CaseGraphData, AuditEvent, InstitutionReply, DashboardMetrics,
  ComplaintSubmission, TimelineEvent,
} from '../types';

// ── Indian States ──
export const indianStates = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh',
  'Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka',
  'Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram',
  'Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu',
  'Telangana','Tripura','Uttar Pradesh','Uttarakhand','West Bengal',
  'Delhi','Chandigarh','Puducherry','Jammu & Kashmir','Ladakh',
];

// ── Demo Institutions ──
export const demoInstitutions: Institution[] = [
  { id: 'INST-001', name: 'Vidya Bharati Engineering College', aicte_id: 'AICTE-1-4523871', state: 'Maharashtra', city: 'Pune', type: 'Engineering', total_complaints: 24, open_complaints: 5, resolved_complaints: 19, compliance_score: 78, norm_check_status: 'PARTIALLY_COMPLIANT', last_inspection: '2026-03-15', student_count: 2400, established_year: 2004 },
  { id: 'INST-002', name: 'Saraswati Institute of Technology', aicte_id: 'AICTE-1-5891023', state: 'Karnataka', city: 'Bangalore', type: 'Engineering', total_complaints: 18, open_complaints: 3, resolved_complaints: 15, compliance_score: 85, norm_check_status: 'COMPLIANT', last_inspection: '2026-06-20', student_count: 3200, established_year: 1998 },
  { id: 'INST-003', name: 'Rajput College of Pharmacy', aicte_id: 'AICTE-2-3456789', state: 'Rajasthan', city: 'Jaipur', type: 'Pharmacy', total_complaints: 31, open_complaints: 12, resolved_complaints: 19, compliance_score: 52, norm_check_status: 'NON_COMPLIANT', last_inspection: '2025-11-10', student_count: 800, established_year: 2010 },
  { id: 'INST-004', name: 'Lakshmi Devi School of Management', aicte_id: 'AICTE-3-7654321', state: 'Tamil Nadu', city: 'Chennai', type: 'Management', total_complaints: 9, open_complaints: 1, resolved_complaints: 8, compliance_score: 92, norm_check_status: 'COMPLIANT', last_inspection: '2026-08-05', student_count: 600, established_year: 2001 },
  { id: 'INST-005', name: 'National Polytechnic Institute', aicte_id: 'AICTE-1-9012345', state: 'Uttar Pradesh', city: 'Lucknow', type: 'Engineering', total_complaints: 42, open_complaints: 15, resolved_complaints: 27, compliance_score: 61, norm_check_status: 'PARTIALLY_COMPLIANT', last_inspection: '2026-01-22', student_count: 4500, established_year: 1995 },
  { id: 'INST-006', name: 'Bharati Architecture Academy', aicte_id: 'AICTE-4-1122334', state: 'Delhi', city: 'New Delhi', type: 'Architecture', total_complaints: 6, open_complaints: 2, resolved_complaints: 4, compliance_score: 88, norm_check_status: 'COMPLIANT', last_inspection: '2026-07-18', student_count: 350, established_year: 2008 },
  { id: 'INST-007', name: 'Guru Nanak Engineering Works', aicte_id: 'AICTE-1-5566778', state: 'Punjab', city: 'Amritsar', type: 'Engineering', total_complaints: 14, open_complaints: 4, resolved_complaints: 10, compliance_score: 73, norm_check_status: 'PARTIALLY_COMPLIANT', last_inspection: '2026-04-30', student_count: 1800, established_year: 2006 },
  { id: 'INST-008', name: 'Deccan College of Applied Arts', aicte_id: 'AICTE-5-9988776', state: 'Telangana', city: 'Hyderabad', type: 'Applied Arts', total_complaints: 3, open_complaints: 0, resolved_complaints: 3, compliance_score: 95, norm_check_status: 'COMPLIANT', last_inspection: '2026-09-01', student_count: 280, established_year: 2012 },
];

// ── Timeline Builder ──
function buildTimeline(id: string, status: string, cell: string): TimelineEvent[] {
  const base: TimelineEvent[] = [
    { id: `${id}-t1`, timestamp: '2026-10-01T09:15:00Z', action: 'Complaint Submitted', actor: 'Online Portal', detail: 'Complaint received via web form', type: 'submission' },
    { id: `${id}-t2`, timestamp: '2026-10-01T09:16:00Z', action: 'Auto-Triage', actor: 'System', detail: `Category and urgency assigned. Language: English. Routed to ${cell}.`, type: 'triage' },
  ];
  if (status !== 'SUBMITTED') {
    base.push({ id: `${id}-t3`, timestamp: '2026-10-02T11:30:00Z', action: `Routed to ${cell}`, actor: 'System', detail: `Assigned to ${cell} cell for processing`, type: 'routing' });
  }
  if (['UNDER_REVIEW', 'AWAITING_REPLY', 'RESOLVED', 'ESCALATED', 'CLOSED'].includes(status)) {
    base.push({ id: `${id}-t4`, timestamp: '2026-10-03T14:20:00Z', action: 'Under Review', actor: 'Analyst Priya S.', detail: 'Case picked up for investigation', type: 'review' });
  }
  if (status === 'ESCALATED') {
    base.push({ id: `${id}-t5`, timestamp: '2026-10-10T09:00:00Z', action: 'SLA Breach — Escalated', actor: 'System', detail: 'SLA deadline exceeded. Escalated to Bureau Head.', type: 'escalation' });
  }
  if (['RESOLVED', 'CLOSED'].includes(status)) {
    base.push({ id: `${id}-t5r`, timestamp: '2026-10-08T16:45:00Z', action: 'Resolved', actor: 'Analyst Priya S.', detail: 'Investigation complete. Action taken against institution.', type: 'resolution' });
  }
  return base;
}

// ── Demo Complaints ──
export const demoComplaints: Complaint[] = [
  { id: 'NIR-2026-00001', title: 'Fee refund not processed after cancellation', description: 'I cancelled my admission in July 2026 but the college has not refunded ₹85,000 despite multiple requests. They keep saying it is under process.', category: 'FEE_REFUND', urgency: 'HIGH', status: 'UNDER_REVIEW', language: 'en', cell: 'PGRC', state: 'Maharashtra', institution_id: 'INST-001', institution_name: 'Vidya Bharati Engineering College', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-10-01T09:15:00Z', updated_at: '2026-10-05T14:20:00Z', sla_deadline: '2026-10-16T09:15:00Z', routing_confidence: 94, needs_human_review: false, assigned_to: 'Analyst Priya S.', is_duplicate_flagged: false, duplicate_of: null, evidence_count: 3, timeline: buildTimeline('NIR-2026-00001', 'UNDER_REVIEW', 'PGRC') },
  { id: 'NIR-2026-00002', title: 'Ragging incident in hostel', description: 'Senior students are forcing freshers to do their assignments and threatening them. Multiple students are affected.', category: 'RAGGING', urgency: 'CRITICAL', status: 'ESCALATED', language: 'en', cell: 'ANTI_RAGGING', state: 'Karnataka', institution_id: 'INST-002', institution_name: 'Saraswati Institute of Technology', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-09-28T18:30:00Z', updated_at: '2026-10-10T09:00:00Z', sla_deadline: '2026-10-05T18:30:00Z', routing_confidence: 98, needs_human_review: false, assigned_to: 'Bureau Head Sharma', is_duplicate_flagged: false, duplicate_of: null, evidence_count: 7, timeline: buildTimeline('NIR-2026-00002', 'ESCALATED', 'ANTI_RAGGING') },
  { id: 'NIR-2026-00003', title: 'Scholarship amount not credited', description: 'मेरी Pragati scholarship की राशि पिछले 6 महीने से credit नहीं हुई है। College कह रहा है कि AICTE से पैसे नहीं आए।', category: 'SCHOLARSHIP_ISSUE', urgency: 'MEDIUM', status: 'ROUTED', language: 'hi', cell: 'SCHOLARSHIP', state: 'Uttar Pradesh', institution_id: 'INST-005', institution_name: 'National Polytechnic Institute', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-10-05T11:00:00Z', updated_at: '2026-10-06T10:00:00Z', sla_deadline: '2026-10-20T11:00:00Z', routing_confidence: 87, needs_human_review: false, assigned_to: null, is_duplicate_flagged: false, duplicate_of: null, evidence_count: 2, timeline: buildTimeline('NIR-2026-00003', 'ROUTED', 'SCHOLARSHIP') },
  { id: 'NIR-2026-00004', title: 'College running unapproved courses', description: 'The college is running MBA and MCA programs without AICTE approval. Students who enrolled are now worried about the validity of their degrees.', category: 'APPROVAL_VIOLATION', urgency: 'HIGH', status: 'UNDER_REVIEW', language: 'en', cell: 'RB', state: 'Rajasthan', institution_id: 'INST-003', institution_name: 'Rajput College of Pharmacy', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-10-03T14:45:00Z', updated_at: '2026-10-07T09:30:00Z', sla_deadline: '2026-10-18T14:45:00Z', routing_confidence: 72, needs_human_review: true, assigned_to: 'Analyst Ravi K.', is_duplicate_flagged: true, duplicate_of: 'NIR-2026-00012', evidence_count: 5, timeline: buildTimeline('NIR-2026-00004', 'UNDER_REVIEW', 'RB') },
  { id: 'NIR-2026-00005', title: 'Sexual harassment by faculty member', description: 'A professor has been making inappropriate comments and advances towards female students. Multiple students are affected but afraid to complain.', category: 'SEXUAL_HARASSMENT', urgency: 'CRITICAL', status: 'UNDER_REVIEW', language: 'en', cell: 'ICC', state: 'Tamil Nadu', institution_id: 'INST-004', institution_name: 'Lakshmi Devi School of Management', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-10-02T16:20:00Z', updated_at: '2026-10-04T11:15:00Z', sla_deadline: '2026-10-09T16:20:00Z', routing_confidence: 96, needs_human_review: false, assigned_to: 'Analyst Meera J.', is_duplicate_flagged: false, duplicate_of: null, evidence_count: 4, timeline: buildTimeline('NIR-2026-00005', 'UNDER_REVIEW', 'ICC') },
  { id: 'NIR-2026-00006', title: 'Certificate withheld after course completion', description: 'College refuses to give my degree certificate saying I owe library fine of ₹500. It has been 8 months since I completed my course.', category: 'CERTIFICATE_WITHHOLDING', urgency: 'MEDIUM', status: 'RESOLVED', language: 'en', cell: 'PGRC', state: 'Punjab', institution_id: 'INST-007', institution_name: 'Guru Nanak Engineering Works', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-08-15T10:30:00Z', updated_at: '2026-09-20T15:00:00Z', sla_deadline: '2026-08-30T10:30:00Z', routing_confidence: 91, needs_human_review: false, assigned_to: 'Analyst Priya S.', is_duplicate_flagged: false, duplicate_of: null, evidence_count: 2, timeline: buildTimeline('NIR-2026-00006', 'RESOLVED', 'PGRC') },
  { id: 'NIR-2026-00007', title: 'Faculty shortage in core departments', description: 'The college has only 3 faculty for the entire CS department with 480 students. Lab sessions are not conducted regularly.', category: 'FACULTY_ISSUE', urgency: 'MEDIUM', status: 'SUBMITTED', language: 'en', cell: 'RB', state: 'Uttar Pradesh', institution_id: 'INST-005', institution_name: 'National Polytechnic Institute', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-10-10T08:45:00Z', updated_at: '2026-10-10T08:45:00Z', sla_deadline: '2026-10-25T08:45:00Z', routing_confidence: 65, needs_human_review: true, assigned_to: null, is_duplicate_flagged: false, duplicate_of: null, evidence_count: 1, timeline: buildTimeline('NIR-2026-00007', 'SUBMITTED', 'RB') },
  { id: 'NIR-2026-00008', title: 'Infrastructure inadequacy — no library', description: 'The college does not have a proper library. Books listed in the prospectus are not available. Computer lab has only 10 working systems for 200 students.', category: 'INFRASTRUCTURE', urgency: 'LOW', status: 'TRIAGED', language: 'en', cell: 'RB', state: 'Maharashtra', institution_id: 'INST-001', institution_name: 'Vidya Bharati Engineering College', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-10-08T12:00:00Z', updated_at: '2026-10-09T09:30:00Z', sla_deadline: '2026-11-07T12:00:00Z', routing_confidence: 81, needs_human_review: false, assigned_to: null, is_duplicate_flagged: false, duplicate_of: null, evidence_count: 0, timeline: buildTimeline('NIR-2026-00008', 'TRIAGED', 'RB') },
  { id: 'NIR-2026-00009', title: 'Admission without valid entrance score', description: 'College ne bina proper entrance exam score ke admission de diya hai. Kuch students ka score bahut kam tha phir bhi unhe seat mil gayi.', category: 'ADMISSION_IRREGULARITY', urgency: 'HIGH', status: 'ROUTED', language: 'hinglish', cell: 'RB', state: 'Delhi', institution_id: 'INST-006', institution_name: 'Bharati Architecture Academy', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-10-06T15:30:00Z', updated_at: '2026-10-07T10:15:00Z', sla_deadline: '2026-10-21T15:30:00Z', routing_confidence: 58, needs_human_review: true, assigned_to: null, is_duplicate_flagged: false, duplicate_of: null, evidence_count: 1, timeline: buildTimeline('NIR-2026-00009', 'ROUTED', 'RB') },
  { id: 'NIR-2026-00010', title: 'Saksham scholarship eligibility dispute', description: 'I am a specially-abled student and applied for Saksham scholarship but was rejected saying my disability certificate is not valid. I have a government-issued certificate.', category: 'SCHOLARSHIP_ISSUE', urgency: 'MEDIUM', status: 'AWAITING_REPLY', language: 'en', cell: 'SCHOLARSHIP', state: 'Telangana', institution_id: 'INST-008', institution_name: 'Deccan College of Applied Arts', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-10-04T09:00:00Z', updated_at: '2026-10-09T14:30:00Z', sla_deadline: '2026-10-19T09:00:00Z', routing_confidence: 89, needs_human_review: false, assigned_to: 'Analyst Ravi K.', is_duplicate_flagged: false, duplicate_of: null, evidence_count: 4, timeline: buildTimeline('NIR-2026-00010', 'AWAITING_REPLY', 'SCHOLARSHIP') },
  { id: 'NIR-2026-00011', title: 'Ragging by seniors during orientation', description: 'During college orientation, seniors forced us to do push-ups and sing songs in front of everyone. Some students were made to strip.', category: 'RAGGING', urgency: 'CRITICAL', status: 'UNDER_REVIEW', language: 'en', cell: 'ANTI_RAGGING', state: 'Uttar Pradesh', institution_id: 'INST-005', institution_name: 'National Polytechnic Institute', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-10-07T20:00:00Z', updated_at: '2026-10-08T08:00:00Z', sla_deadline: '2026-10-14T20:00:00Z', routing_confidence: 97, needs_human_review: false, assigned_to: 'Analyst Meera J.', is_duplicate_flagged: false, duplicate_of: null, evidence_count: 6, timeline: buildTimeline('NIR-2026-00011', 'UNDER_REVIEW', 'ANTI_RAGGING') },
  { id: 'NIR-2026-00012', title: 'Unapproved pharmacy courses offered', description: 'The institution is offering D.Pharm and B.Pharm courses that are not listed in AICTE approved list for this academic year.', category: 'APPROVAL_VIOLATION', urgency: 'HIGH', status: 'UNDER_REVIEW', language: 'en', cell: 'RB', state: 'Rajasthan', institution_id: 'INST-003', institution_name: 'Rajput College of Pharmacy', complainant_encrypted: '[ENCRYPTED]', submitted_at: '2026-09-25T11:30:00Z', updated_at: '2026-10-05T16:00:00Z', sla_deadline: '2026-10-10T11:30:00Z', routing_confidence: 93, needs_human_review: false, assigned_to: 'Analyst Ravi K.', is_duplicate_flagged: false, duplicate_of: null, evidence_count: 4, timeline: buildTimeline('NIR-2026-00012', 'UNDER_REVIEW', 'RB') },
];

// ── Demo Norm Checks ──
export const demoNormChecks: NormCheckResult[] = [
  { norm: 'Faculty-Student Ratio', category: 'Faculty', status: 'FAIL', detail: 'Required 1:15, actual 1:48. Severe shortage in CS and ECE departments.', source: 'AICTE APH 2025-26, Section 4.2' },
  { norm: 'Laboratory Equipment', category: 'Infrastructure', status: 'FAIL', detail: 'Only 40% of required lab equipment available. Several labs non-functional.', source: 'AICTE APH 2025-26, Section 5.1' },
  { norm: 'Library Holdings', category: 'Infrastructure', status: 'INSUFFICIENT_EVIDENCE', detail: 'Institution did not submit library audit report for current year.', source: 'AICTE APH 2025-26, Section 5.3' },
  { norm: 'Anti-Ragging Committee', category: 'Governance', status: 'PASS', detail: 'Committee constituted with required members. Meets quarterly.', source: 'UGC Regulations 2009' },
  { norm: 'Grievance Redressal Cell', category: 'Governance', status: 'PASS', detail: 'SGRC and Ombudsman appointed as per regulations.', source: 'AICTE APH 2025-26, Section 7' },
  { norm: 'Fire Safety Compliance', category: 'Safety', status: 'FAIL', detail: 'Fire NOC expired. No fire drill conducted in last 12 months.', source: 'NBC 2016, Part 4' },
  { norm: 'Disclosure on Website', category: 'Transparency', status: 'PASS', detail: 'Mandatory disclosures published on institution website.', source: 'AICTE APH 2025-26, Section 8' },
  { norm: 'Fee Structure Approval', category: 'Finance', status: 'INSUFFICIENT_EVIDENCE', detail: 'Fee committee approval document not available for verification.', source: 'State Fee Regulation Act' },
];

// ── Demo Compliance Radar ──
export function demoComplianceRadar(institutionId: string): ComplianceRadarData {
  const inst = demoInstitutions.find(i => i.id === institutionId);
  return {
    institution_id: institutionId,
    institution_name: inst?.name || 'Unknown Institution',
    dimensions: [
      { label: 'Faculty Quality', value: 45, benchmark: 75 },
      { label: 'Infrastructure', value: 60, benchmark: 70 },
      { label: 'Governance', value: 82, benchmark: 80 },
      { label: 'Student Outcomes', value: 55, benchmark: 65 },
      { label: 'Safety & Compliance', value: 38, benchmark: 85 },
      { label: 'Financial Transparency', value: 70, benchmark: 75 },
      { label: 'Grievance Resolution', value: 65, benchmark: 70 },
    ],
  };
}

// ── Demo Case Graph ──
export const demoCaseGraph: CaseGraphData = {
  fallback: true,
  nodes: [
    { id: 'NIR-2026-00004', label: 'NIR-00004\nUnapproved courses', type: 'complaint' },
    { id: 'NIR-2026-00012', label: 'NIR-00012\nUnapproved pharmacy', type: 'complaint' },
    { id: 'NIR-2026-00001', label: 'NIR-00001\nFee refund', type: 'complaint' },
    { id: 'NIR-2026-00008', label: 'NIR-00008\nNo library', type: 'complaint' },
    { id: 'INST-003', label: 'Rajput College\nof Pharmacy', type: 'institution' },
    { id: 'INST-001', label: 'Vidya Bharati\nEngineering', type: 'institution' },
    { id: 'CELL-RB', label: 'Regulation\nBureau', type: 'cell' },
    { id: 'CELL-PGRC', label: 'PGRC', type: 'cell' },
  ],
  edges: [
    { source: 'NIR-2026-00004', target: 'INST-003', label: 'against' },
    { source: 'NIR-2026-00012', target: 'INST-003', label: 'against' },
    { source: 'NIR-2026-00004', target: 'NIR-2026-00012', label: 'potential duplicate' },
    { source: 'NIR-2026-00004', target: 'CELL-RB', label: 'routed to' },
    { source: 'NIR-2026-00012', target: 'CELL-RB', label: 'routed to' },
    { source: 'NIR-2026-00001', target: 'INST-001', label: 'against' },
    { source: 'NIR-2026-00008', target: 'INST-001', label: 'against' },
    { source: 'NIR-2026-00001', target: 'CELL-PGRC', label: 'routed to' },
    { source: 'NIR-2026-00008', target: 'CELL-RB', label: 'routed to' },
  ],
};

// ── Demo Audit Events ──
export const demoAuditEvents: AuditEvent[] = [
  { id: 'AUD-001', timestamp: '2026-10-10T09:01:00Z', actor: 'system', actor_role: 'ADMIN', action: 'ESCALATION', target_type: 'complaint', target_id: 'NIR-2026-00002', detail: 'SLA breach: auto-escalated to Bureau Head', ip_address: '10.0.0.1' },
  { id: 'AUD-002', timestamp: '2026-10-09T14:32:00Z', actor: 'analyst_ravi', actor_role: 'ANALYST', action: 'STATUS_CHANGE', target_type: 'complaint', target_id: 'NIR-2026-00010', detail: 'Status changed to AWAITING_REPLY. Institution notified.', ip_address: '10.0.0.15' },
  { id: 'AUD-003', timestamp: '2026-10-08T08:05:00Z', actor: 'analyst_meera', actor_role: 'ANALYST', action: 'CASE_ASSIGNED', target_type: 'complaint', target_id: 'NIR-2026-00011', detail: 'Case assigned to Analyst Meera J.', ip_address: '10.0.0.22' },
  { id: 'AUD-004', timestamp: '2026-10-07T10:18:00Z', actor: 'system', actor_role: 'ADMIN', action: 'TRIAGE', target_type: 'complaint', target_id: 'NIR-2026-00009', detail: 'Auto-triage: LOW confidence (58%). Flagged for human review.', ip_address: '10.0.0.1' },
  { id: 'AUD-005', timestamp: '2026-10-06T10:02:00Z', actor: 'system', actor_role: 'ADMIN', action: 'ROUTING', target_type: 'complaint', target_id: 'NIR-2026-00003', detail: 'Routed to SCHOLARSHIP cell. Confidence: 87%.', ip_address: '10.0.0.1' },
  { id: 'AUD-006', timestamp: '2026-10-05T14:22:00Z', actor: 'analyst_priya', actor_role: 'ANALYST', action: 'CASE_ASSIGNED', target_type: 'complaint', target_id: 'NIR-2026-00001', detail: 'Case assigned to Analyst Priya S.', ip_address: '10.0.0.18' },
  { id: 'AUD-007', timestamp: '2026-10-05T16:05:00Z', actor: 'analyst_ravi', actor_role: 'ANALYST', action: 'DUPLICATE_FLAG', target_type: 'complaint', target_id: 'NIR-2026-00004', detail: 'Flagged as potential duplicate of NIR-2026-00012. Requires human approval to merge.', ip_address: '10.0.0.15' },
  { id: 'AUD-008', timestamp: '2026-09-20T15:02:00Z', actor: 'analyst_priya', actor_role: 'ANALYST', action: 'RESOLUTION', target_type: 'complaint', target_id: 'NIR-2026-00006', detail: 'Case resolved. Certificate release confirmed by institution.', ip_address: '10.0.0.18' },
  { id: 'AUD-009', timestamp: '2026-10-09T09:30:00Z', actor: 'system', actor_role: 'ADMIN', action: 'TRIAGE', target_type: 'complaint', target_id: 'NIR-2026-00008', detail: 'Auto-triage: Infrastructure category, LOW urgency, RB cell.', ip_address: '10.0.0.1' },
  { id: 'AUD-010', timestamp: '2026-10-04T11:17:00Z', actor: 'analyst_meera', actor_role: 'ANALYST', action: 'IDENTITY_REVEAL_REQUEST', target_type: 'complaint', target_id: 'NIR-2026-00005', detail: 'Identity reveal requested for ICC case investigation. Requires dual approval.', ip_address: '10.0.0.22' },
];

// ── Demo Institution Replies ──
export const demoReplies: InstitutionReply[] = [
  { id: 'REPLY-001', complaint_id: 'NIR-2026-00001', institution_id: 'INST-001', submitted_by: 'Registrar, Vidya Bharati Engineering College', submitted_at: '2026-10-07T11:00:00Z', content: 'The fee refund is being processed. Due to the large volume of cancellations this semester, we are experiencing delays. We expect to complete all refunds by November 15, 2026.', attachments: ['refund_schedule.pdf'], status: 'PENDING_REVIEW' },
  { id: 'REPLY-002', complaint_id: 'NIR-2026-00010', institution_id: 'INST-008', submitted_by: 'Admin Officer, Deccan College', submitted_at: '2026-10-09T14:30:00Z', content: 'The student\'s disability certificate was from a private hospital. As per AICTE Saksham scheme guidelines, we require a certificate from a government hospital or a certified board. We have communicated this to the student.', attachments: [], status: 'PENDING_REVIEW' },
];

// ── Demo Dashboard Metrics ──
export const demoDashboardMetrics: DashboardMetrics = {
  total_complaints: 1247,
  pending_triage: 38,
  sla_breaches: 7,
  resolved_30d: 312,
  avg_resolution_days: 4.2,
  complaints_by_cell: { PGRC: 420, ANTI_RAGGING: 310, RB: 245, ICC: 158, SCHOLARSHIP: 114 },
  complaints_by_status: { SUBMITTED: 38, TRIAGED: 45, ROUTED: 67, UNDER_REVIEW: 145, AWAITING_REPLY: 28, RESOLVED: 312, ESCALATED: 12, CLOSED: 600 },
  complaints_by_urgency: { CRITICAL: 18, HIGH: 67, MEDIUM: 145, LOW: 82 },
  monthly_trend: [
    { month: 'May', received: 185, resolved: 160 },
    { month: 'Jun', received: 210, resolved: 190 },
    { month: 'Jul', received: 195, resolved: 180 },
    { month: 'Aug', received: 240, resolved: 210 },
    { month: 'Sep', received: 220, resolved: 200 },
    { month: 'Oct', received: 197, resolved: 185 },
  ],
  state_distribution: {
    'Maharashtra': 186, 'Karnataka': 142, 'Tamil Nadu': 128, 'Uttar Pradesh': 165,
    'Rajasthan': 89, 'Delhi': 76, 'Punjab': 54, 'Telangana': 68, 'Gujarat': 72,
    'Kerala': 45, 'West Bengal': 58, 'Madhya Pradesh': 62, 'Bihar': 38, 'Haryana': 34,
  },
  sla_performance: [
    { cell: 'PGRC', within_sla: 92, breached: 8 },
    { cell: 'Anti-Ragging', within_sla: 85, breached: 15 },
    { cell: 'RB', within_sla: 88, breached: 12 },
    { cell: 'ICC', within_sla: 90, breached: 10 },
    { cell: 'Scholarship', within_sla: 95, breached: 5 },
  ],
};

// ── Create Demo Complaint ──
let nextId = 13;
export function createDemoComplaint(payload: ComplaintSubmission): Complaint {
  const id = `NIR-2026-${String(nextId++).padStart(5, '0')}`;
  const now = new Date().toISOString();
  const sla = new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString();
  const complaint: Complaint = {
    id, title: payload.title, description: payload.description,
    category: payload.category, urgency: 'MEDIUM', status: 'SUBMITTED',
    language: payload.language, cell: '', state: payload.state,
    institution_id: '', institution_name: payload.institution_name,
    complainant_encrypted: '[ENCRYPTED]', submitted_at: now, updated_at: now,
    sla_deadline: sla, routing_confidence: 0, needs_human_review: true,
    assigned_to: null, is_duplicate_flagged: false, duplicate_of: null,
    evidence_count: 0,
    timeline: [{ id: `${id}-t1`, timestamp: now, action: 'Complaint Submitted', actor: 'Online Portal', detail: 'Complaint received via web form', type: 'submission' }],
  };
  demoComplaints.unshift(complaint);
  return complaint;
}

// ── Demo Accounts Info ──
export const demoAccounts = [
  { username: 'admin', password: 'admin', role: 'ADMIN', cell: '', description: 'System Administrator — full access' },
  { username: 'bureau_head', password: 'bureau123', role: 'BUREAU_HEAD', cell: 'RB', description: 'Bureau Head — escalation approval' },
  { username: 'analyst', password: 'analyst123', role: 'ANALYST', cell: 'PGRC', description: 'Complaint Analyst — case management' },
  { username: 'nodal', password: 'nodal123', role: 'NODAL_OFFICER', cell: '', description: 'Institution Nodal Officer — replies' },
  { username: 'auditor', password: 'auditor123', role: 'AUDITOR', cell: '', description: 'Auditor — read-only audit access' },
];
