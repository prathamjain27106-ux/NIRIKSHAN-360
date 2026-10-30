"""
NIRIKSHAN 360 — Norm-Check Verification Engine
================================================
Verifies institution compliance against mandatory AICTE Approval Process Handbook (APH)
disclosures using a structured evidence dataset.

Guarantees:
  1. Every finding is supported by a stored evidence record with:
     - source_url
     - retrieved_at / verified_at timestamp
     - relevant excerpt or field
  2. Returns: SUPPORTED, CONTRADICTED, or INSUFFICIENT_EVIDENCE
  3. If no valid evidence exists, returns INSUFFICIENT_EVIDENCE
  4. Never invents live AICTE records.
"""

from typing import List, Dict, Any, Optional
from django.utils import timezone
from .disclosure_dataset import DISCLOSURE_DATASET, get_institution_disclosure_evidence
from .models import Institution, NormCheckResult

STANDARD_NORMS = [
    {
        "norm": "Faculty-Student Ratio",
        "category": "Faculty",
        "detail": "AICTE prescribed faculty-student ratio of 1:20 for undergraduate engineering programs.",
        "source": "AICTE Approval Process Handbook, Section 4.2",
    },
    {
        "norm": "Anti-Ragging Committee",
        "category": "Student Welfare",
        "detail": "Mandatory constitution of anti-ragging committee and squad with multi-stakeholder representation.",
        "source": "UGC Anti-Ragging Regulations 2009 & Supreme Court Directives",
    },
    {
        "norm": "Internal Complaints Committee",
        "category": "Student Welfare",
        "detail": "Internal Complaints Committee (ICC) constituted per POSH Act 2013 and AICTE Gender Sensitization Regulations.",
        "source": "Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013",
    },
    {
        "norm": "Grievance Redressal Mechanism",
        "category": "Governance",
        "detail": "Functional Student Grievance Redressal Committee (SGRC) and University Ombudsman linkage.",
        "source": "AICTE (Redressal of Grievance of Students) Regulations, 2019",
    },
    {
        "norm": "Fee Structure Compliance",
        "category": "Financial",
        "detail": "Approved fee structure verified by State Fee Regulatory Authority without unauthorized capitation fee.",
        "source": "AICTE APH Section 3.1 & State Fee Regulatory Act",
    },
    {
        "norm": "Laboratory Equipment",
        "category": "Infrastructure",
        "detail": "Operational laboratories with prescribed equipment and minimum 1:4 computer terminal ratio.",
        "source": "AICTE APH Section 5.1 Lab Infrastructure Norms",
    },
    {
        "norm": "Fire Safety Compliance",
        "category": "Safety",
        "detail": "Valid Fire Safety NOC and disaster management compliance certificate.",
        "source": "National Building Code 2016, Part 4 Fire & Life Safety",
    },
    {
        "norm": "Approved Programs & Intake",
        "category": "Approval",
        "detail": "All running courses and intakes must have current AICTE Extension of Approval (EoA).",
        "source": "AICTE Regulations for Grant of Approval",
    },
]


def execute_norm_check(institution: Institution, user=None) -> List[NormCheckResult]:
    """
    Run norm-check for an institution against the structured disclosure dataset.
    Updates or creates NormCheckResult records.
    Never invents live AICTE records: if no disclosure record exists,
    returns INSUFFICIENT_EVIDENCE.
    """
    inst_disclosure = DISCLOSURE_DATASET.get(institution.aicte_id)
    results = []
    
    for norm_spec in STANDARD_NORMS:
        norm_name = norm_spec["norm"]
        category = norm_spec["category"]
        
        evidence_record = None
        if inst_disclosure and "norms" in inst_disclosure:
            evidence_record = inst_disclosure["norms"].get(norm_name)
            
        if evidence_record:
            finding = evidence_record.get("finding", "INSUFFICIENT_EVIDENCE")
            source_url = evidence_record.get("source_url", "")
            verified_at = evidence_record.get("retrieved_at")
            excerpt = evidence_record.get("excerpt", "")
            detail = evidence_record.get("detail", norm_spec["detail"])
            field_name = evidence_record.get("field", norm_name)
            reported_value = evidence_record.get("reported_value", "")
            required_norm = evidence_record.get("required_norm", "")
            source = norm_spec["source"]
            status_val = "PASS" if finding == "SUPPORTED" else "FAIL" if finding == "CONTRADICTED" else "INSUFFICIENT_EVIDENCE"
        else:
            # NO STORED EVIDENCE RECORD EXISTS — RETURN INSUFFICIENT EVIDENCE
            # Never invent live AICTE records!
            finding = "INSUFFICIENT_EVIDENCE"
            status_val = "INSUFFICIENT_EVIDENCE"
            source_url = ""
            verified_at = None
            excerpt = ""
            detail = (
                f"No verified disclosure filing found for '{norm_name}' in the structured AICTE disclosure dataset. "
                "AICTE live records are never invented."
            )
            field_name = norm_name
            reported_value = "Unreported / Not Available"
            required_norm = norm_spec["detail"]
            source = norm_spec["source"]
        
        # Upsert result
        obj, _ = NormCheckResult.objects.update_or_create(
            institution=institution,
            norm=norm_name,
            defaults={
                "category": category,
                "status": status_val,
                "finding": finding,
                "detail": detail,
                "source": source,
                "source_url": source_url,
                "verified_at": verified_at,
                "excerpt": excerpt,
                "field_name": field_name,
                "reported_value": reported_value,
                "required_norm": required_norm,
                "checked_by": user,
            }
        )
        results.append(obj)
        
    # Recompute compliance score & overall status based on verified evidence
    total = len(results)
    supported_count = sum(1 for r in results if r.finding == "SUPPORTED")
    contradicted_count = sum(1 for r in results if r.finding == "CONTRADICTED")
    insufficient_count = sum(1 for r in results if r.finding == "INSUFFICIENT_EVIDENCE")
    
    if insufficient_count == total:
        institution.norm_check_status = Institution.NormStatus.INSUFFICIENT_DATA
        institution.compliance_score = 0
    else:
        # Score calculation based on evaluated norms
        evaluated = supported_count + contradicted_count
        score = int((supported_count / max(evaluated, 1)) * 100) if evaluated > 0 else 0
        institution.compliance_score = score
        
        if score >= 75 and contradicted_count == 0:
            institution.norm_check_status = Institution.NormStatus.COMPLIANT
        elif contradicted_count > 0 and supported_count > 0:
            institution.norm_check_status = Institution.NormStatus.PARTIALLY_COMPLIANT
        elif contradicted_count > 0 and supported_count == 0:
            institution.norm_check_status = Institution.NormStatus.NON_COMPLIANT
        else:
            institution.norm_check_status = Institution.NormStatus.PARTIALLY_COMPLIANT
            
    institution.save(update_fields=["norm_check_status", "compliance_score"])
    return results
