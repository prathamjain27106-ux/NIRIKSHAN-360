"""Idempotent end-to-end demo sandbox seed command."""

import csv
import io
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from complaints.duplicates import find_possible_duplicates
from complaints.models import Complaint
from complaints.serializers import ComplaintCreateSerializer
from institutions.models import Institution
from institutions.norm_check import execute_norm_check


class Command(BaseCommand):
    help = "Create synthetic users, disclosure-backed institutions, and multilingual demo complaints."

    @transaction.atomic
    def handle(self, *args, **options):
        users = self._users()
        institutions = self._institutions(users["review_supervisor"])
        complaints = self._complaints(institutions)
        duplicate_count = sum(len(find_possible_duplicates(c)) for c in complaints)
        for institution in institutions:
            execute_norm_check(institution, users["review_supervisor"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo sandbox ready: {len(users)} users, {len(institutions)} institutions, "
                f"{len(complaints)} complaints, {duplicate_count} duplicate warnings."
            )
        )
        self.stdout.write(self.style.WARNING("DEMO DATA ACTIVE: all records are synthetic."))

    def _users(self):
        accounts = (
            ("intake_agent", os.getenv("DEMO_INTAKE_PASSWORD", "NirikshanDemo!2026"), User.Role.ANALYST),
            ("review_supervisor", os.getenv("DEMO_SUPERVISOR_PASSWORD", "NirikshanReview!2026"), User.Role.BUREAU_HEAD),
        )
        result = {}
        for username, password, role in accounts:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"role": role, "email": f"{username}@nirikshan.demo"},
            )
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
            result[username] = user
        return result

    def _institutions(self, supervisor):
        records = (
            ("Vidya Bharati Engineering College", "AICTE-MH-2019-001", "Maharashtra", "Pune", "ENGINEERING", 2800),
            ("Saraswati Institute of Technology", "AICTE-KA-2020-045", "Karnataka", "Bengaluru", "ENGINEERING", 3500),
        )
        institutions = []
        for name, aicte_id, state, city, institution_type, capacity in records:
            institution, _ = Institution.objects.get_or_create(
                aicte_id=aicte_id,
                defaults={
                    "name": name,
                    "state": state,
                    "city": city,
                    "institution_type": institution_type,
                    "student_count": capacity,
                },
            )
            institutions.append(institution)
        return institutions

    def _complaints(self, institutions):
        payload = """title,description,category,institution_name,institution_id,state,language,complainant_name
Fee refund pending,मेरी फीस वापसी लंबित है,FEE_REFUND,Vidya Bharati Engineering College,{mh},Maharashtra,hi,Demo Student
Fee refund pending,मेरी फीस वापसी अभी तक लंबित है,FEE_REFUND,Vidya Bharati Engineering College,{mh},Maharashtra,hinglish,Demo Student 2
Hostel safety concern,Hostel safety incident needs review,RAGGING,Saraswati Institute of Technology,{ka},Karnataka,en,Demo Student 3
""".format(mh=institutions[0].pk, ka=institutions[1].pk)
        complaints = []
        for row in csv.DictReader(io.StringIO(payload)):
            if Complaint.objects.filter(
                title=row["title"],
                institution_id=row["institution_id"],
                source_channel="CSV_IMPORT",
            ).exists():
                continue
            serializer = ComplaintCreateSerializer(
                data={
                    **row,
                    "source_channel": "CSV_IMPORT",
                    "institution_id": row["institution_id"],
                    "is_anonymous": True,
                }
            )
            serializer.is_valid(raise_exception=True)
            complaint = serializer.save()
            complaints.append(complaint)
        return complaints
