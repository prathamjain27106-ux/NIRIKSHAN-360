# 📡 NIRIKSHAN 360

**Integrated Command-Centre Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells**  
SIH 2026 · Problem Statement SIH26264 · Smart Automation

> ⚠️ This is an advanced evaluation prototype using certified synthetic demo datasets. All processing telemetry is self-contained and explicitly labeled as simulated data for evaluation safety.

## 📽️ Live Demonstration & Video Walkthrough

The complete operational flow of NIRIKSHAN 360 is recorded and available here:

- **YouTube Live Demo Link:** [youtube.demo-video](https://youtu.be/GnumtX3Im10)
- **Video Scope:** Covers multi-channel ingest mockups, Explainable Multilingual Triage Engine, relational Norm-Check disclosures, active SLA countdown trackers, and interactive Neo4j Case Graph fallbacks.

## Overview

NIRIKSHAN 360 is a proactive, data-driven command-centre dashboard built for Team LOOPS (Logic Over Other People's Syntax). It unifies fragmented regulatory workflows, compliance mapping, and network intelligence into a tightly audited system across all target AICTE operational divisions:

| Cell | Core Regulatory Focus | Target Bureau Operations |
|---|---|---|
| RB | Regulation Bureau | Systemic infrastructure deficits, statutory validation compliance |
| PGRC | Public Grievance Redressal Cell | Capitation fee overcharges, structural refund delays, certificate withholding |
| Anti-Ragging | Supreme Court Compliance | Instantaneous disciplinary dispatch tracking and cell escalations |
| ICC | Internal Complaints Committee | POSH Act enforcement frameworks with deep identity protection overrides |
| Scholarship | Financial Aid Audits | Processing bottlenecks across Pragati, Saksham, and PSK welfare initiatives |

## 🔥 Core Features (Fully Implemented)

- ⚖️ **Explainable Multilingual Triage Engine:** A native rule-assisted processing engine combining English, Hindi, and phonetically blended Hinglish token extractions with explicit algorithmic reasoning.
- 🏛️ **Norm-Check Verification Engine:** Automated cross-referencing against relational statutory disclosure records, throwing absolute SUPPORTED, CONTRADICTED, or INSUFFICIENT_EVIDENCE states with immutable source citations.
- 🔗 **Dual-Engine Case Graph Visualization:** High-fidelity relationship graph rendering using Neo4j AuraDB with an automated relational fallback to PostgreSQL database maps during network connection losses.
- ⏱️ **Dynamic SLA Automation & Process Signals:** Real-time lifecycle countdown tickers coupled with background escalation handlers that flag organizational process log backlogs automatically.
- 📡 **Proportional Compliance Radar:** Size-normalized data views calculating unverified complaint density frequencies relative to total institutional approved intake bounds.
- 💓 **Systemic Pulse Diagnostic Engine:** Structural telemetry logging that mathematically differentiates localized institutional behavior from internal processing delays.
- 🛡️ **Non-Destructive Duplicate Detection:** Token-similarity matching within a strict 30-day window that isolates fraudulent target spams while requiring manual supervisor approval before linking.
- 🔒 **Auditable Override Tracking Logs:** Server-enforced, identity-mapped trail arrays recording every triage modification with a mandatory text block detailing operational justification.

## Technology Stack

| Layer | Component Infrastructure | Specifications |
|---|---|---|
| Frontend | React 18, Vite 8, Tailwind CSS, Recharts Architecture | Clean, component-isolated responsive metrics panel layouts featuring graceful zero-data empty states. |
| Backend | Python 3.11+, Django 4.2+, Django REST Framework | Multi-app modular backend separating auth tokens, processing queues, database logs, and dashboard metrics. |
| Database | Serverless Neon PostgreSQL (Production Cluster Mapping) | Native relational fallback engines tracking structured master records, disclosures, and relational nodes. |
| Graph Platform | Neo4j AuraDB Cluster Environment | External relational graph driver index mapping complaint references via isolated token relationships. |
| NLP Pipeline | Native Regular Expressions + Token Scanners | Specialized string query match arrays scanning linguistic patterns across multi-dialect inputs. |
| CORS Guard | django-cors-headers Cross-Port Middleware Protection | Secure port bridging linking dev clients (port 5173) safely with system API servers (port 8000). |

## Local Setup & Initialization

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git Installed

### 1. Repository Checkout & Local Token Configuration

```bash
git clone <repo-url>
cd NIRIKSHAN-360
cp .env.example .env
