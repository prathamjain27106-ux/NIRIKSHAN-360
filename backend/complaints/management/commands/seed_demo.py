"""
NIRIKSHAN 360 — Seed Demo Data
=================================
Creates synthetic data for prototype demonstration.
Run: python manage.py seed_demo

Demo accounts (development/demo mode ONLY):
  admin       / admin123     — System Administrator
  bureau_head / bureau123    — Bureau Head (PGRC)
  analyst     / analyst123   — Complaint Analyst (PGRC)
  analyst2    / analyst123   — Complaint Analyst (Anti-Ragging)
  nodal       / nodal123     — Institution Nodal Officer
  auditor     / auditor123   — Auditor

All data is synthetic and clearly labelled. Not connected to any AICTE production system.
"""

import random
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from accounts.crypto import encrypt_identity
from complaints.models import Complaint, CaseTimelineEvent, SLAPolicy
from institutions.models import Institution, NormCheckResult, InstitutionReply
from audit.models import AuditEvent


class Command(BaseCommand):
    help = "Seed the database with synthetic demo data for prototype demonstration."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete existing data before seeding")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stderr.write(self.style.ERROR(
                "Seed data can only be created in DEBUG mode. "
                "Set DJANGO_DEBUG=True or remove this check for demo deployments."
            ))
            return

        if options["flush"]:
            self.stdout.write("Flushing existing data...")
            InstitutionReply.objects.all().delete()
            CaseTimelineEvent.objects.all().delete()
            Complaint.objects.all().delete()
            NormCheckResult.objects.all().delete()
            Institution.objects.all().delete()
            AuditEvent.objects.all().delete()
            SLAPolicy.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write("Creating demo accounts...")
        users = self._create_users()
        self.stdout.write("Creating SLA policies...")
        self._create_sla_policies()
        self.stdout.write("Creating institutions...")
        institutions = self._create_institutions(users)
        self.stdout.write("Creating complaints...")
        complaints = self._create_complaints(institutions, users)
        self.stdout.write("Creating norm-check results...")
        self._create_norm_checks(institutions, users)
        self.stdout.write("Creating audit events...")
        self._create_audit_events(complaints, users)

        self.stdout.write(self.style.SUCCESS(
            f"\n[OK] Seed complete: {len(users)} users, {len(institutions)} institutions, "
            f"{len(complaints)} complaints, SLA policies, norm checks, audit events."
        ))
        self.stdout.write(self.style.WARNING(
            "\n[!] DEMO DATA -- All data is synthetic. Not connected to any AICTE production system."

        ))

    def _create_users(self):
        accounts = [
            ("admin", "admin123", User.Role.ADMIN, "", "System", "Admin"),
            ("bureau_head", "bureau123", User.Role.BUREAU_HEAD, "PGRC", "Rajesh", "Kumar"),
            ("analyst", "analyst123", User.Role.ANALYST, "PGRC", "Priya", "Sharma"),
            ("analyst2", "analyst123", User.Role.ANALYST, "ANTI_RAGGING", "Meera", "Joshi"),
            ("nodal", "nodal123", User.Role.NODAL_OFFICER, "", "Vikram", "Patel"),
            ("auditor", "auditor123", User.Role.AUDITOR, "", "Anita", "Desai"),
        ]
        users = {}
        for username, password, role, cell, first, last in accounts:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": role, "cell": cell,
                    "first_name": first, "last_name": last,
                    "email": f"{username}@nirikshan.demo",
                    "is_staff": role == User.Role.ADMIN,
                    "is_superuser": role == User.Role.ADMIN,
                },
            )
            if created:
                user.set_password(password)
                user.save()
            users[username] = user
        return users

    def _create_sla_policies(self):
        policies = [
            ("RB", "CRITICAL", 24), ("RB", "HIGH", 72), ("RB", "MEDIUM", 168), ("RB", "LOW", 336),
            ("PGRC", "CRITICAL", 24), ("PGRC", "HIGH", 48), ("PGRC", "MEDIUM", 120), ("PGRC", "LOW", 240),
            ("ANTI_RAGGING", "CRITICAL", 12), ("ANTI_RAGGING", "HIGH", 24), ("ANTI_RAGGING", "MEDIUM", 72), ("ANTI_RAGGING", "LOW", 168),
            ("ICC", "CRITICAL", 24), ("ICC", "HIGH", 48), ("ICC", "MEDIUM", 120), ("ICC", "LOW", 240),
            ("SCHOLARSHIP", "CRITICAL", 48), ("SCHOLARSHIP", "HIGH", 96), ("SCHOLARSHIP", "MEDIUM", 168), ("SCHOLARSHIP", "LOW", 336),
        ]
        for cell, urgency, hours in policies:
            SLAPolicy.objects.get_or_create(cell=cell, urgency=urgency, defaults={"deadline_hours": hours})

    def _create_institutions(self, users):
        inst_data = [
            ("Vidya Bharati Engineering College", "AICTE-MH-2019-001", "Maharashtra", "Pune", "ENGINEERING", 2800, 1985, 78, "PARTIALLY_COMPLIANT"),
            ("Saraswati Institute of Technology", "AICTE-KA-2020-045", "Karnataka", "Bangalore", "ENGINEERING", 3500, 1992, 85, "COMPLIANT"),
            ("Rajput College of Pharmacy", "AICTE-RJ-2018-012", "Rajasthan", "Jaipur", "PHARMACY", 1200, 2001, 52, "NON_COMPLIANT"),
            ("Lakshmi Devi School of Management", "AICTE-TN-2017-078", "Tamil Nadu", "Chennai", "MANAGEMENT", 800, 2005, 92, "COMPLIANT"),
            ("National Polytechnic Institute", "AICTE-UP-2016-034", "Uttar Pradesh", "Lucknow", "ENGINEERING", 4200, 1978, 61, "PARTIALLY_COMPLIANT"),
            ("Bharati Architecture Academy", "AICTE-DL-2021-009", "Delhi", "New Delhi", "ARCHITECTURE", 450, 2010, 88, "COMPLIANT"),
            ("Guru Nanak Engineering Works", "AICTE-PB-2015-056", "Punjab", "Amritsar", "ENGINEERING", 2100, 1995, 73, "PARTIALLY_COMPLIANT"),
            ("Deccan College of Applied Arts", "AICTE-TS-2019-023", "Telangana", "Hyderabad", "APPLIED_ARTS", 600, 2008, 90, "COMPLIANT"),
        ]
        institutions = []
        for name, aicte_id, state, city, itype, students, year, score, norm_status in inst_data:
            inst, _ = Institution.objects.get_or_create(
                aicte_id=aicte_id,
                defaults={
                    "name": name, "state": state, "city": city,
                    "institution_type": itype, "student_count": students,
                    "established_year": year, "compliance_score": score,
                    "norm_check_status": norm_status,
                    "last_inspection": timezone.now().date() - timedelta(days=random.randint(30, 365)),
                },
            )
            institutions.append(inst)

        # Assign nodal officer to first institution
        if "nodal" in users and institutions:
            institutions[0].nodal_officer = users["nodal"]
            institutions[0].save()

        return institutions

    def _create_complaints(self, institutions, users):
        now = timezone.now()
        complaint_data = [
            ("Fee refund not processed after cancellation", "I cancelled my admission in July 2026 but the college has not refunded ₹85,000 despite multiple requests. They keep saying it is under process.", "FEE_REFUND", "HIGH", "PGRC", "UNDER_REVIEW", 0, "en"),
            ("Ragging incident in hostel", "Senior students physically harassed freshers in Block C hostel on 15th September. Multiple witnesses present. Warden was informed but took no action.", "RAGGING", "CRITICAL", "ANTI_RAGGING", "ESCALATED", 1, "en"),
            ("Scholarship amount not credited", "AICTE scholarship for SC/ST students for session 2025-26 has not been credited despite college confirming disbursement to AICTE.", "SCHOLARSHIP_ISSUE", "MEDIUM", "SCHOLARSHIP", "ROUTED", 2, "en"),
            ("College running unapproved courses", "College is running B.Tech in AI/ML without AICTE approval. Students enrolled in 2025 batch are affected. Approval status shows pending on AICTE portal.", "APPROVAL_VIOLATION", "HIGH", "RB", "UNDER_REVIEW", 3, "en"),
            ("Sexual harassment by faculty member", "A faculty member has been making inappropriate comments and unwanted advances towards female students. Multiple complaints to HOD were ignored.", "SEXUAL_HARASSMENT", "CRITICAL", "ICC", "UNDER_REVIEW", 4, "en"),
            ("Certificate withheld after completion", "College is withholding my degree certificate and marksheets despite clearing all dues. They are demanding additional 'processing fee' of ₹15,000.", "CERTIFICATE_WITHHOLDING", "HIGH", "PGRC", "AWAITING_REPLY", 0, "en"),
            ("Insufficient lab equipment", "Computer lab has only 20 working systems for 120 students. Networking lab has no routers. Physics lab equipment is outdated and non-functional.", "INFRASTRUCTURE", "MEDIUM", "RB", "TRIAGED", 5, "en"),
            ("Faculty shortage in core departments", "Mechanical Engineering dept has 3 faculty for 240 students (ratio 1:80). Minimum AICTE norm is 1:20. Guest faculty teach all practical sessions.", "FACULTY_ISSUE", "HIGH", "RB", "ROUTED", 6, "en"),
            ("Admission irregularity — management quota", "College admitted 40 students beyond sanctioned intake through 'management quota' not approved by AICTE. Charging ₹5 lakh capitation fee.", "ADMISSION_IRREGULARITY", "HIGH", "RB", "SUBMITTED", 3, "en"),
            ("Fee refund delayed beyond 15 days", "मैंने 1 अगस्त को एडमिशन कैंसिल किया था लेकिन अभी तक फीस वापस नहीं मिली। कॉलेज बार-बार टाल रहा है।", "FEE_REFUND", "MEDIUM", "PGRC", "TRIAGED", 0, "hi"),
            ("Anti-ragging committee not constituted", "As per UGC regulations, college must have anti-ragging committee. No such committee exists. No helpline number displayed.", "RAGGING", "MEDIUM", "ANTI_RAGGING", "ROUTED", 1, "en"),
            ("Placement data misrepresented", "College website claims 95% placement but actual placement is below 30%. This misleading data was used for AICTE approval renewal.", "APPROVAL_VIOLATION", "MEDIUM", "RB", "SUBMITTED", 7, "en"),
        ]

        complaints = []
        analyst = users.get("analyst")
        analyst2 = users.get("analyst2")

        for i, (title, desc, cat, urgency, cell, stat, inst_idx, lang) in enumerate(complaint_data):
            inst = institutions[inst_idx] if inst_idx < len(institutions) else institutions[0]

            # Encrypt identity
            names = ["Rahul Verma", "Sneha Gupta", "Anonymous", "Amit Kumar", "Priya Singh",
                     "Ravi Sharma", "Neha Patel", "Suresh Yadav", "Kavita Jain", "Anonymous",
                     "Deepak Mehta", "Sonia Kapoor"]
            name = names[i] if i < len(names) else "Demo User"
            is_anon = name == "Anonymous"
            if is_anon:
                ct, nonce = b"", b""
            else:
                ct, nonce = encrypt_identity(f"name={name}|contact={name.lower().replace(' ', '.')}@demo.in")

            days_ago = random.randint(5, 60)
            created = now - timedelta(days=days_ago)

            # Calculate SLA
            try:
                sla = SLAPolicy.objects.get(cell=cell, urgency=urgency)
                sla_deadline = created + timedelta(hours=sla.deadline_hours)
            except SLAPolicy.DoesNotExist:
                sla_deadline = created + timedelta(days=7)

            c = Complaint(
                title=title, description=desc, category=cat, urgency=urgency,
                cell=cell, status=stat, institution=inst,
                institution_name_text=inst.name, state=inst.state,
                language=lang, source_channel="WEB_PORTAL",
                complainant_encrypted=ct, complainant_nonce=nonce,
                is_anonymous=is_anon,
                routing_confidence=random.randint(58, 98),
                needs_human_review=random.choice([True, False]),
                sla_deadline=sla_deadline,
            )
            c.save()

            # Assign some complaints
            if stat in ("UNDER_REVIEW", "AWAITING_REPLY", "ESCALATED", "RESOLVED"):
                assignee = analyst2 if cell == "ANTI_RAGGING" else analyst
                if assignee:
                    c.assigned_to = assignee
                    c.save()

            # Timeline events
            CaseTimelineEvent.objects.create(
                complaint=c, event_type="SUBMISSION", action="Complaint Submitted",
                detail=f"Complaint received via Web Portal",
                actor_label="Online Portal", created_at=created,
            )
            if stat != "SUBMITTED":
                CaseTimelineEvent.objects.create(
                    complaint=c, event_type="TRIAGE", action="Auto-Triage",
                    detail=f"Category and urgency assigned. Language: {lang}. Routed to {cell}.",
                    actor_label="System", created_at=created + timedelta(minutes=1),
                )
            if stat in ("ROUTED", "UNDER_REVIEW", "AWAITING_REPLY", "ESCALATED", "RESOLVED"):
                CaseTimelineEvent.objects.create(
                    complaint=c, event_type="ROUTING", action=f"Routed to {cell}",
                    detail=f"Assigned to {cell} cell for processing",
                    actor_label="System", created_at=created + timedelta(hours=1),
                )
            if stat in ("UNDER_REVIEW", "AWAITING_REPLY", "ESCALATED", "RESOLVED"):
                CaseTimelineEvent.objects.create(
                    complaint=c, event_type="STATUS_CHANGE", action="Under Review",
                    detail="Case picked up for investigation",
                    actor_label=analyst.username if analyst else "System",
                    actor=analyst, created_at=created + timedelta(days=1),
                )
            if stat == "ESCALATED":
                CaseTimelineEvent.objects.create(
                    complaint=c, event_type="ESCALATION", action="Escalated to Bureau Head",
                    detail="SLA breach: auto-escalated to Bureau Head",
                    actor_label="System", created_at=created + timedelta(days=3),
                )

            # Duplicate flag for complaint 4
            if i == 3 and len(complaints) >= 1:
                c.is_duplicate_flagged = True
                c.duplicate_family = complaints[0]
                c.save()

            complaints.append(c)

        return complaints

    def _create_norm_checks(self, institutions, users):
        norms = [
            ("Faculty-Student Ratio", "Faculty", "Faculty to student ratio meets AICTE minimum of 1:20", "APH 2024-25 Section 4.2"),
            ("Lab Infrastructure", "Infrastructure", "Required labs with minimum equipment as per curriculum", "APH 2024-25 Section 5.1"),
            ("Library Resources", "Infrastructure", "Library with minimum prescribed books and journals", "APH 2024-25 Section 5.3"),
            ("Grievance Redressal Cell", "Governance", "Functional grievance redressal committee with student representation", "UGC Regulations 2019"),
            ("Anti-Ragging Committee", "Student Welfare", "Constituted as per Supreme Court/UGC directives", "UGC Anti-Ragging Regulations"),
            ("ICC Constitution", "Student Welfare", "Internal Complaints Committee constituted under POSH Act", "POSH Act 2013"),
            ("Financial Transparency", "Financial", "Fee structure approved and published. No capitation fee.", "APH 2024-25 Section 3.1"),
            ("Placement Data Accuracy", "Governance", "Published placement data verifiable and accurate", "AICTE Notification 2023"),
        ]
        analyst = users.get("analyst")
        for inst in institutions:
            for norm_name, category, detail, source in norms:
                status_choice = random.choices(
                    ["PASS", "FAIL", "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE"],
                    weights=[50, 20, 20, 10],
                )[0]
                if inst.compliance_score >= 85:
                    status_choice = random.choices(["PASS", "INSUFFICIENT_EVIDENCE"], weights=[80, 20])[0]
                elif inst.compliance_score < 60:
                    status_choice = random.choices(["FAIL", "INSUFFICIENT_EVIDENCE", "PASS"], weights=[50, 30, 20])[0]

                NormCheckResult.objects.get_or_create(
                    institution=inst, norm=norm_name,
                    defaults={
                        "category": category, "status": status_choice,
                        "detail": f"{detail}. Status: {status_choice}.",
                        "source": source, "checked_by": analyst,
                    },
                )

    def _create_audit_events(self, complaints, users):
        now = timezone.now()
        events_data = [
            (10, "ESCALATION", "system", "Complaint", 1, "SLA breach: auto-escalated to Bureau Head"),
            (9, "STATUS_CHANGE", "analyst", "Complaint", 9, "Status changed to AWAITING_REPLY. Institution notified."),
            (8, "ASSIGNMENT", "analyst2", "Complaint", 10, "Case assigned to Analyst Meera J."),
            (7, "TRIAGE", "system", "Complaint", 8, "Auto-triage: LOW confidence (58%). Flagged for human review."),
            (6, "ROUTING", "system", "Complaint", 2, "Routed to SCHOLARSHIP cell. Confidence: 87%."),
            (5, "ASSIGNMENT", "analyst", "Complaint", 0, "Case assigned to Analyst Priya S."),
            (5, "DUPLICATE_FLAG", "analyst", "Complaint", 3, "Flagged as potential duplicate of NIR-2026-00012. Requires human approval to merge."),
            (20, "RESOLUTION", "analyst", "Complaint", 5, "Case resolved. Certificate release confirmed by institution."),
            (1, "TRIAGE", "system", "Complaint", 7, "Auto-triage: Infrastructure category, LOW urgency, RB cell."),
            (3, "IDENTITY_REVEAL_REQUEST", "bureau_head", "Complaint", 4, "Identity reveal requested for sexual harassment case investigation."),
        ]
        for days_ago, action, actor_key, target_type, comp_idx, detail in events_data:
            actor = users.get(actor_key) if actor_key != "system" else None
            target_id = complaints[comp_idx].tracking_id if comp_idx < len(complaints) else ""
            AuditEvent.objects.create(
                timestamp=now - timedelta(days=days_ago),
                actor=actor,
                actor_username=actor_key,
                actor_role=actor.role if actor else "",
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
            )
