"""
NIRIKSHAN 360 — Differentiation Layer Test Suite
==================================================
Comprehensive automated tests covering:
  1. Multilingual triage (English, Hindi, Hinglish)
  2. Low-confidence triage & human review flagging
  3. Norm-check with structured evidence & missing evidence handling
  4. False-positive duplicate candidate detection & dismissal
  5. Neo4j graph disconnection & PostgreSQL fallback
  6. SLA deadline calculation & auto-escalation
  7. Role-based permission enforcement (403 forbidden)
  8. Immutable audit entries & human override trails
"""

from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from complaints.models import Complaint, CaseTimelineEvent, SLAPolicy
from complaints.triage import classify_complaint
from complaints.duplicates import find_possible_duplicates
from complaints.graph import get_case_graph, Neo4jAdapter
from institutions.models import Institution, NormCheckResult
from institutions.norm_check import execute_norm_check
from audit.models import AuditEvent


class DifferentiationLayerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username="admin_user", password="password123", role="ADMIN")
        self.analyst = User.objects.create_user(username="analyst_user", password="password123", role="ANALYST", cell="PGRC")
        self.nodal = User.objects.create_user(username="nodal_user", password="password123", role="NODAL_OFFICER")
        self.auditor = User.objects.create_user(username="auditor_user", password="password123", role="AUDITOR")

        # Standard SLA policies
        SLAPolicy.objects.get_or_create(cell="ANTI_RAGGING", urgency="CRITICAL", defaults={"deadline_hours": 12})
        SLAPolicy.objects.get_or_create(cell="ICC", urgency="CRITICAL", defaults={"deadline_hours": 24})
        SLAPolicy.objects.get_or_create(cell="PGRC", urgency="HIGH", defaults={"deadline_hours": 48})
        SLAPolicy.objects.get_or_create(cell="PGRC", urgency="MEDIUM", defaults={"deadline_hours": 120})
        SLAPolicy.objects.get_or_create(cell="SCHOLARSHIP", urgency="MEDIUM", defaults={"deadline_hours": 168})
        SLAPolicy.objects.get_or_create(cell="RB", urgency="HIGH", defaults={"deadline_hours": 72})
        SLAPolicy.objects.get_or_create(cell="RB", urgency="MEDIUM", defaults={"deadline_hours": 168})

        self.inst_vbec = Institution.objects.create(
            name="Vidya Bharati Engineering College",
            aicte_id="AICTE-MH-2019-001",
            state="Maharashtra",
            city="Pune",
            compliance_score=75,
        )

    # ══════════════════════════════════════════════════════════
    # 1. Multilingual Triage (English, Hindi, Hinglish)
    # ══════════════════════════════════════════════════════════

    def test_multilingual_triage_english(self):
        """Verify English triage correctly classifies category, urgency, destination cell, and reasons."""
        res_ragging = classify_complaint(
            title="Senior violence in hostel",
            description="Seniors forced freshers to do push-ups and bullied them violently during hostel hazing.",
            language="en"
        )
        self.assertEqual(res_ragging["category"], "RAGGING")
        self.assertEqual(res_ragging["priority"], "CRITICAL")
        self.assertEqual(res_ragging["destination_cell"], "ANTI_RAGGING")
        self.assertGreaterEqual(res_ragging["confidence_score"], 75)
        self.assertFalse(res_ragging["needs_human_review"])
        self.assertEqual(res_ragging["triage_method"], "rule-based/assisted triage")
        self.assertTrue(any("Ragging" in r or "push-ups" in r or "RAGGING" in r for r in res_ragging["reasons"]))

        res_icc = classify_complaint(
            title="Inappropriate touch by professor",
            description="A professor has been sending obscene messages and demanding sexual favours from female students.",
            language="en"
        )
        self.assertEqual(res_icc["category"], "SEXUAL_HARASSMENT")
        self.assertEqual(res_icc["priority"], "CRITICAL")
        self.assertEqual(res_icc["destination_cell"], "ICC")

    def test_multilingual_triage_hindi(self):
        """Verify Hindi (Devanagari) triage logic."""
        res_fee = classify_complaint(
            title="प्रवेश रद्द करने पर फीस वापसी नहीं मिली",
            description="मैंने कॉलेज में प्रवेश रद्द कराया था परंतु दो महीने बीत जाने पर भी शुल्क वापसी नहीं की गई है।",
            language="hi"
        )
        self.assertEqual(res_fee["category"], "FEE_REFUND")
        self.assertEqual(res_fee["destination_cell"], "PGRC")
        self.assertGreaterEqual(res_fee["confidence_score"], 75)
        self.assertFalse(res_fee["needs_human_review"])
        self.assertEqual(res_fee["language_detected"], "hi")

        res_cert = classify_complaint(
            title="डिग्री और अंकपत्र रोक लिया है",
            description="कॉलेज मूल दस्तावेज रोक कर बैठा है और टीसी नहीं दे रहे हैं।",
            language="hi"
        )
        self.assertEqual(res_cert["category"], "CERTIFICATE_WITHHOLDING")
        self.assertEqual(res_cert["destination_cell"], "PGRC")

    def test_multilingual_triage_hinglish(self):
        """Verify Hinglish (Latin script) triage logic."""
        res_scholarship = classify_complaint(
            title="Pragati scholarship credit nahi hui",
            description="Mera pragati scholarship ka paisa account me credit nahi hua hai college bol raha hai AICTE se nahi aaya.",
            language="hinglish"
        )
        self.assertEqual(res_scholarship["category"], "SCHOLARSHIP_ISSUE")
        self.assertEqual(res_scholarship["destination_cell"], "SCHOLARSHIP")
        self.assertGreaterEqual(res_scholarship["confidence_score"], 75)
        self.assertFalse(res_scholarship["needs_human_review"])
        self.assertEqual(res_scholarship["language_detected"], "hinglish")

        res_approval = classify_complaint(
            title="Unapproved course chala rahe hai",
            description="College bina aicte approval ke artificial intelligence branch chala raha hai degree invalid ho jayegi.",
            language="hinglish"
        )
        self.assertEqual(res_approval["category"], "APPROVAL_VIOLATION")
        self.assertEqual(res_approval["destination_cell"], "RB")

    # ══════════════════════════════════════════════════════════
    # 2. Low-Confidence Review
    # ══════════════════════════════════════════════════════════

    def test_low_confidence_flagged_for_human_review(self):
        """Uncertain or vague grievances must be flagged for human review."""
        res = classify_complaint(
            title="General dissatisfaction",
            description="College experience has been very bad and unfair please look into this matter.",
            threshold=75
        )
        self.assertEqual(res["category"], "OTHER")
        self.assertLess(res["confidence_score"], 75)
        self.assertTrue(res["needs_human_review"])
        self.assertTrue(any("human review" in r.lower() for r in res["reasons"]))

        # Verify through API submission
        self.client.force_authenticate(user=self.admin)
        post_res = self.client.post("/api/complaints/create/", {
            "title": "General dissatisfaction",
            "description": "College experience has been very bad and unfair please look into this matter.",
            "institution_name": self.inst_vbec.name,
            "institution_id": str(self.inst_vbec.id),
        }, format="json")
        self.assertEqual(post_res.status_code, 201)
        data = post_res.json()
        self.assertTrue(data["needs_human_review"])
        self.assertEqual(data["category"], "OTHER")

    # ══════════════════════════════════════════════════════════
    # 3. Norm-Check: Structured Evidence & Missing Evidence
    # ══════════════════════════════════════════════════════════

    def test_norm_check_with_structured_evidence(self):
        """Norm-check results must be supported by stored evidence records with URL, timestamp, and excerpt."""
        results = execute_norm_check(self.inst_vbec, user=self.analyst)
        self.assertGreater(len(results), 0)

        # Check a supported norm
        anti_ragging = next(r for r in results if r.norm == "Anti-Ragging Committee")
        self.assertEqual(anti_ragging.finding, "SUPPORTED")
        self.assertEqual(anti_ragging.status, "PASS")
        self.assertTrue(anti_ragging.source_url.startswith("https://"))
        self.assertIsNotNone(anti_ragging.verified_at)
        self.assertIn("Office Order VBEC/ARC/2026-01", anti_ragging.excerpt)

        # Check a contradicted norm
        fsr = next(r for r in results if r.norm == "Faculty-Student Ratio")
        self.assertEqual(fsr.finding, "CONTRADICTED")
        self.assertEqual(fsr.status, "FAIL")
        self.assertTrue(fsr.source_url.startswith("https://"))
        self.assertIn("1:35", fsr.excerpt)

    def test_missing_evidence_returns_insufficient_evidence_never_invents(self):
        """If no valid disclosure evidence exists, return INSUFFICIENT_EVIDENCE and never invent live records."""
        unknown_inst = Institution.objects.create(
            name="Unregistered Private Institute",
            aicte_id="AICTE-UNKNOWN-9999",
            state="Goa",
            city="Panaji",
        )
        results = execute_norm_check(unknown_inst, user=self.analyst)
        for r in results:
            self.assertEqual(r.finding, "INSUFFICIENT_EVIDENCE")
            self.assertEqual(r.status, "INSUFFICIENT_EVIDENCE")
            self.assertEqual(r.source_url, "")
            self.assertIsNone(r.verified_at)
            self.assertIn("never invented", r.detail)

    # ══════════════════════════════════════════════════════════
    # 4. False-Positive Duplicate Candidates & Officer Confirmation
    # ══════════════════════════════════════════════════════════

    def test_false_positive_duplicate_candidates_and_officer_linking(self):
        """Present matches with explanation; require officer confirmation; never auto-merge."""
        self.client.force_authenticate(user=self.analyst)

        # Create two related fee complaints against same institution
        c1 = Complaint.objects.create(
            title="Refund of 85,000 pending after cancellation",
            description="Cancelled seat in July, no fee refund received yet.",
            category="FEE_REFUND",
            institution=self.inst_vbec,
            state="Maharashtra",
        )
        c2 = Complaint.objects.create(
            title="Fee refund after cancelling seat",
            description="Fee of 85,000 has not been returned after cancellation.",
            category="FEE_REFUND",
            institution=self.inst_vbec,
            state="Maharashtra",
        )

        # Create an unrelated complaint (false-positive candidate)
        c3 = Complaint.objects.create(
            title="Ragging in boys hostel",
            description="Senior students threatening freshers in hostel.",
            category="RAGGING",
            institution=self.inst_vbec,
            state="Maharashtra",
        )

        candidates = find_possible_duplicates(c1)
        self.assertTrue(any(item["candidate"].pk == c2.pk for item in candidates))
        match_c2 = next(item for item in candidates if item["candidate"].pk == c2.pk)
        self.assertGreaterEqual(match_c2["similarity_score"], 60)
        self.assertIn("Matching institution", match_c2["similarity_explanation"])
        self.assertIn("officer confirmation", match_c2["similarity_explanation"].lower())

        # Candidate c3 (Ragging) should have significantly lower similarity score than c2 (Fee Refund)
        match_c3 = next((item for item in candidates if item["candidate"].pk == c3.pk), None)
        if match_c3:
            self.assertLess(match_c3["similarity_score"], match_c2["similarity_score"])

        # Check duplicate retrieval API
        dup_res = self.client.get(f"/api/complaints/{c1.tracking_id}/duplicates/")
        self.assertEqual(dup_res.status_code, 200)
        self.assertIn("Never auto-merge", dup_res.json()["policy"])

        # Officer confirms and links c2 as duplicate of c1
        link_res = self.client.post(f"/api/complaints/{c2.tracking_id}/link-duplicate/", {
            "canonical_id": c1.tracking_id,
            "confirm": True,
            "reason": "Confirmed same student case filed twice by guardian and student.",
        }, format="json")
        self.assertEqual(link_res.status_code, 200)
        c2.refresh_from_db()
        self.assertEqual(c2.duplicate_family, c1)
        self.assertTrue(c2.is_duplicate_flagged)
        # c1 must NOT be deleted (never auto-merge / destroy cases)
        self.assertTrue(Complaint.objects.filter(pk=c1.pk).exists())

        # Officer dismisses false-positive candidate c3
        dismiss_res = self.client.post(f"/api/complaints/{c1.tracking_id}/dismiss-duplicate/", {
            "candidate_id": c3.tracking_id,
            "reason": "False positive: completely different issue (Ragging vs Fee Refund).",
        }, format="json")
        self.assertEqual(dismiss_res.status_code, 200)

    # ══════════════════════════════════════════════════════════
    # 5. Graph Disconnection & PostgreSQL Fallback
    # ══════════════════════════════════════════════════════════

    def test_graph_disconnection_falls_back_to_postgres(self):
        """When Neo4j is disconnected or credentials unconfigured, seamlessly return PostgreSQL graph."""
        c = Complaint.objects.create(
            title="Lab equipment missing",
            description="No computers in computer lab.",
            category="INFRASTRUCTURE",
            institution=self.inst_vbec,
            cell="RB",
        )

        # Force Neo4j connection failure via mock
        with patch.object(Neo4jAdapter, "check_connection", return_value=False):
            graph_data = get_case_graph(complaint_id=c.tracking_id)
            self.assertTrue(graph_data["fallback"])
            self.assertEqual(graph_data["engine"], "postgres")
            self.assertGreaterEqual(len(graph_data["nodes"]), 1)
            self.assertGreaterEqual(len(graph_data["edges"]), 1)

            # Assert labeled edges exist
            labels = [e["label"] for e in graph_data["edges"]]
            self.assertIn("against", labels)

            # PRIVACY CHECK: Nodes must NOT contain complainant identity or narrative
            for node in graph_data["nodes"]:
                self.assertNotIn("No computers in computer lab", node["label"])
                self.assertNotIn("complainant_name", node.get("metadata", {}))

    # ══════════════════════════════════════════════════════════
    # 6. SLA Escalation
    # ══════════════════════════════════════════════════════════

    def test_sla_escalation_detection_and_auto_escalation(self):
        """Verify SLA breach detection, countdown, overdue flag, and auto-escalation event."""
        past_time = timezone.now() - timedelta(hours=50)
        c = Complaint.objects.create(
            title="Overdue scholarship case",
            description="Stipend not credited for months.",
            category="SCHOLARSHIP_ISSUE",
            institution=self.inst_vbec,
            cell="SCHOLARSHIP",
            urgency="HIGH",
            status="UNDER_REVIEW",
            sla_deadline=past_time,
        )
        self.assertTrue(c.is_sla_breached)
        self.assertTrue(c.is_overdue)
        self.assertLess(c.sla_hours_remaining, 0)

        # Trigger auto-escalations check
        self.client.force_authenticate(user=self.analyst)
        res = self.client.post("/api/complaints/check-escalations/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(c.tracking_id, res.json()["escalated_cases"])

        c.refresh_from_db()
        self.assertEqual(c.status, Complaint.Status.ESCALATED)

        # Check timeline event
        timeline_events = CaseTimelineEvent.objects.filter(complaint=c, event_type="ESCALATION")
        self.assertTrue(timeline_events.exists())
        self.assertIn("SLA Breach", timeline_events.first().action)

    # ══════════════════════════════════════════════════════════
    # 7. Role-Based Permissions (403 Forbidden)
    # ══════════════════════════════════════════════════════════

    def test_permission_denied_requests(self):
        """Nodal officer or unauthorized users must be blocked (HTTP 403) from analyst operations."""
        c = Complaint.objects.create(
            title="Restricted operation complaint",
            description="Test complaint for RBAC verification.",
            category="FEE_REFUND",
            institution=self.inst_vbec,
        )

        # Nodal officer cannot assign
        self.client.force_authenticate(user=self.nodal)
        res_assign = self.client.post(f"/api/complaints/{c.tracking_id}/assign/", {
            "assigned_to": self.analyst.pk
        }, format="json")
        self.assertEqual(res_assign.status_code, 403)

        # Nodal officer cannot override triage
        res_override = self.client.post(f"/api/complaints/{c.tracking_id}/override/", {
            "field": "category",
            "value": "RAGGING",
            "reason": "Unauthorized attempt"
        }, format="json")
        self.assertEqual(res_override.status_code, 403)

        # Nodal officer cannot link duplicate
        res_link = self.client.post(f"/api/complaints/{c.tracking_id}/link-duplicate/", {
            "canonical_id": c.tracking_id,
            "confirm": True,
            "reason": "Unauthorized attempt"
        }, format="json")
        self.assertEqual(res_link.status_code, 403)

    # ══════════════════════════════════════════════════════════
    # 8. Auditable Human Overrides & Immutable Audit Entries
    # ══════════════════════════════════════════════════════════

    def test_auditable_human_overrides_and_audit_entries(self):
        """Auditable human overrides must record timeline events and immutable AuditEvent entries."""
        c = Complaint.objects.create(
            title="Fee dispute needing category change",
            description="Fee refund requested, but also involves admission irregularity.",
            category="FEE_REFUND",
            institution=self.inst_vbec,
            urgency="MEDIUM",
            cell="PGRC",
        )

        self.client.force_authenticate(user=self.analyst)

        # Analyst overrides urgency to CRITICAL with justification
        override_res = self.client.post(f"/api/complaints/{c.tracking_id}/override/", {
            "field": "urgency",
            "value": "CRITICAL",
            "reason": "Urgency upgraded because complainant faces imminent admission cancellation deadline.",
        }, format="json")
        self.assertEqual(override_res.status_code, 200)

        c.refresh_from_db()
        self.assertEqual(c.urgency, "CRITICAL")

        # Verify CaseTimelineEvent created
        event = CaseTimelineEvent.objects.filter(complaint=c, event_type="OVERRIDE").first()
        self.assertIsNotNone(event)
        self.assertIn("Human Override: urgency", event.action)
        self.assertIn("imminent admission cancellation deadline", event.detail)

        # Verify immutable AuditEvent created
        audit_entry = AuditEvent.objects.filter(target_id=c.tracking_id, action="OVERRIDE").first()
        self.assertIsNotNone(audit_entry)
        self.assertEqual(audit_entry.actor, self.analyst)
        self.assertIn("MEDIUM", audit_entry.detail)
        self.assertIn("CRITICAL", audit_entry.detail)
