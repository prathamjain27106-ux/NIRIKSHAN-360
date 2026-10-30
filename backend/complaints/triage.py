"""
NIRIKSHAN 360 — Explainable Multilingual Triage Engine
======================================================
Robust multilingual classification for English, Hindi, and Hinglish.
Uses spaCy where available alongside deterministic rule logic and keyword concordance.
Always returns:
  - category
  - priority (urgency)
  - destination cell
  - confidence score (0-100)
  - structured, human-readable reasons
  - triage_method: "rule-based/assisted triage" (unless real ML model active)
  - needs_human_review: True when confidence < threshold
"""

import re
from typing import Dict, Any, List, Optional
from django.conf import settings

# Attempt to load spaCy gracefully
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = spacy.blank("en")
except Exception:
    nlp = None

try:
    from django.conf import settings
    DEFAULT_CONFIDENCE_THRESHOLD = getattr(settings, "TRIAGE_CONFIDENCE_THRESHOLD", 75) if settings.configured else 75
except Exception:
    DEFAULT_CONFIDENCE_THRESHOLD = 75

# Patterns for each category across English, Hindi (Devanagari), and Hinglish (Latin)
CATEGORY_RULES = {
    "RAGGING": {
        "cell": "ANTI_RAGGING",
        "urgency": "CRITICAL",
        "english": [
            r"\bragging\b", r"\bragged\b", r"\bbullied\b", r"\bhazing\b",
            r"\bforced to (?:strip|dance|do push-?ups|drink|smoke|kneel)\b",
            r"\bhostel (?:violence|torture|abuse)\b",
            r"\bsenior (?:torture|harassment|abuse|bullying)\b",
            r"\bphysical abuse by seniors?\b",
            r"\banti-?ragging\b",
        ],
        "hindi": [
            r"रैगिंग", r"हॉस्टल में प्रताड़ना", r"सीनियर्स द्वारा प्रताड़ित",
            r"कनिष्ठ छात्रों को परेशान", r"रैगिंग की शिकायत", r"मारपीट.*हॉस्टल",
            r"हॉस्टल में मारपीट", r"प्रताड़ित करना"
        ],
        "hinglish": [
            r"ragging kar rahe", r"ragging kiya", r"seniors? torture", r"freshers? ko harass",
            r"push-?ups? karwa(?:ye|ya)", r"kapde utarwa(?:ye|ya)", r"hostel me bully",
            r"seniors? dhamki", r"seniors? pareshaan kar rahe", r"seniors? pareshan kar",
            r"seniors? ne peeta", r"hostel me ragging"
        ],
    },
    "SEXUAL_HARASSMENT": {
        "cell": "ICC",
        "urgency": "CRITICAL",
        "english": [
            r"\bsexual harassment\b", r"\bposh act\b", r"\binappropriate touch(?:ing)?\b",
            r"\bmolestation\b", r"\bmolested\b", r"\bsexual abuse\b",
            r"\bforced.*advances\b", r"\bobscene messages?\b",
            r"\bdemanding sexual favours?\b", r"\bharassment of female\b",
            r"\binappropriate behaviour with (?:girls?|women|female)\b",
        ],
        "hindi": [
            r"यौन उत्पीड़न", r"छेड़छाड़", r"अश्लील संदेश", r"गलत हरकत",
            r"महिला सुरक्षा", r"यौन शोषण", r"अश्लील व्यवहार", r"लड़कियों से छेड़खानी"
        ],
        "hinglish": [
            r"chedchaad", r"galat harkat", r"ashleel messages?", r"touch kiya",
            r"female students? ko harass", r"sexual harassment", r"molest kiya",
            r"inappropriate touch", r"prof ne galat", r"badtameezi.*ladkiyon",
        ],
    },
    "FEE_REFUND": {
        "cell": "PGRC",
        "urgency": "HIGH",
        "english": [
            r"\bfee refund\b", r"\brefund.*(?:admission|cancellation|fees?)\b",
            r"\bfees? not returned\b", r"\bdelayed refund\b", r"\bcaution deposit\b",
            r"\bcapitation fee\b", r"\breturn.*(?:my|the)? ?fees?\b",
            r"\btuition fee refund\b", r"\bcancelled admission.*refund\b",
        ],
        "hindi": [
            r"फीस वापसी", r"फीस वापस", r"शुल्क वापसी", r"प्रवेश रद्द.*शुल्क",
            r"धरोहर राशि", r"पैसे वापस नहीं", r"शुल्क नहीं लौटाया"
        ],
        "hinglish": [
            r"fees? refund nahi", r"paise wapas nahi", r"cancellation.*refund",
            r"fee return nahi", r"fees? atka rakh(?:a|i)", r"refund nahi kiya",
            r"admission cancel.*fees?", r"paisa refund karo", r"fees? lautayi nahi"
        ],
    },
    "CERTIFICATE_WITHHOLDING": {
        "cell": "PGRC",
        "urgency": "MEDIUM",
        "english": [
            r"\bcertificate withheld\b", r"\bwithholding.*(?:certificate|degree|marksheet)\b",
            r"\bdegree withholding\b", r"\boriginal marksheets?\b",
            r"\btc not issued\b", r"\bmigration certificate\b",
            r"\bwithholding original\b", r"\brefuses to (?:give|issue|release) (?:degree|marksheet|certificate)\b",
        ],
        "hindi": [
            r"प्रमाण पत्र रोक", r"अंकपत्र नहीं दे रहे", r"मूल दस्तावेज रोक",
            r"डिग्री रोकी", r"टीसी नहीं दी", r"सर्टिफिकेट नहीं दे रहे", r"दस्तावेज वापस"
        ],
        "hinglish": [
            r"marksheet roki", r"degree nahi de rahe", r"documents? wapas nahi",
            r"certificate atka rakh(?:a|i)", r"tc nahi de rahe",
            r"original certificate nahi", r"marksheet nahi mil rahi"
        ],
    },
    "SCHOLARSHIP_ISSUE": {
        "cell": "SCHOLARSHIP",
        "urgency": "MEDIUM",
        "english": [
            r"\bscholarship\b", r"\bpragati scheme\b", r"\bsaksham scheme\b",
            r"\baicte-?psk\b", r"\bfellowship not credited\b", r"\bstipend delayed\b",
            r"\bscholarship portal\b", r"\bdisbursement of scholarship\b",
        ],
        "hindi": [
            r"छात्रवृत्ति", r"प्रगति योजना", r"सक्षम छात्रवृत्ति",
            r"वजीफा नहीं मिला", r"फेलोशिप", r"छात्रवृत्ति राशि", r"छात्रवृत्ति क्रेडिट"
        ],
        "hinglish": [
            r"scholarship nahi aayi", r"pragati scholarship", r"saksham amount",
            r"stipend atka", r"scholarship credit nahi", r"fellowship nahi mili",
            r"scholarship ka paisa", r"portal pe scholarship pending"
        ],
    },
    "APPROVAL_VIOLATION": {
        "cell": "RB",
        "urgency": "HIGH",
        "english": [
            r"\bunapproved courses?\b", r"\bapproval violation\b",
            r"\bwithout aicte approval\b", r"\bfake affiliation\b",
            r"\binvalid degree\b", r"\bunapproved intake\b",
            r"\brunning without approval\b", r"\bunauthorized branch\b",
        ],
        "hindi": [
            r"बिना मान्यता के", r"अनाधिकृत पाठ्यक्रम", r"एआईसीटीई मान्यता उल्लंघन",
            r"फर्जी मान्यता", r"मान्यता रद्द", r"अमान्य डिग्री"
        ],
        "hinglish": [
            r"bina aicte approval", r"unapproved course", r"fake recognition",
            r"approval nahi hai", r"course ki aicte approval nahi", r"fake affiliation"
        ],
    },
    "FACULTY_ISSUE": {
        "cell": "RB",
        "urgency": "MEDIUM",
        "english": [
            r"\bfaculty shortage\b", r"\bunqualified teachers?\b",
            r"\bghost faculty\b", r"\bteachers? absent\b",
            r"\bno professors?\b", r"\bfaculty to student ratio\b",
            r"\bshortage of teachers?\b", r"\bteachers? don't teach\b",
        ],
        "hindi": [
            r"शिक्षकों की कमी", r"संकाय की कमी", r"अपात्र शिक्षक",
            r"प्रोफेसर नहीं हैं", r"अध्यापकों की अनुपस्थिति"
        ],
        "hinglish": [
            r"teachers? nahi hai", r"faculty shortage", r"professors? nahi padhate",
            r"faculty ki kami", r"professors? absent", r"teachers? ki kami"
        ],
    },
    "INFRASTRUCTURE": {
        "cell": "RB",
        "urgency": "LOW",
        "english": [
            r"\b(?:insufficient|broken|damaged|no) lab equipment\b",
            r"\bno library\b", r"\bbroken computers?\b",
            r"\bno drinking water\b", r"\bbuilding unsafe\b",
            r"\binfrastructure (?:poor|inadequate|lacking)\b",
            r"\blaboratory equipment\b", r"\bunusable labs?\b",
        ],
        "hindi": [
            r"पुस्तकालय नहीं है", r"प्रयोगशाला उपकरण", r"भवन असुरक्षित",
            r"आधारभूत संरचना", r"कंप्यूटर लैब खराब", r"पीने का पानी नहीं"
        ],
        "hinglish": [
            r"library nahi hai", r"labs? me computers? nahi", r"laboratory me samaan nahi",
            r"infrastructure bekar", r"lab equipment nahi", r"lab band padi hai"
        ],
    },
    "ADMISSION_IRREGULARITY": {
        "cell": "RB",
        "urgency": "HIGH",
        "english": [
            r"\badmission irregularity\b", r"\bcapitation fee\b",
            r"\bdonation for seat\b", r"\bmanagement quota irregularity\b",
            r"\badmission without entrance\b", r"\bseat selling\b",
            r"\billegal admission\b",
        ],
        "hindi": [
            r"प्रवेश में धांधली", r"अवैध दाखिला", r"डोनेशन लेकर सीट",
            r"प्रवेश घोटाला", r"बिना परीक्षा दाखिला"
        ],
        "hinglish": [
            r"bina entrance ke seat", r"donation le rahe", r"admission ghotala",
            r"management quota me extra", r"seat bech rahe"
        ],
    },
}


def detect_language(text: str) -> str:
    """Detect whether input text is English, Hindi (Devanagari), or Hinglish."""
    # Count Devanagari characters
    devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
    if devanagari_chars > 5:
        return "hi"
    
    # Common Hinglish stopwords / markers
    hinglish_markers = [
        r"\bnahi\b", r"\bhai\b", r"\bhain\b", r"\bkarte\b", r"\bkarta\b",
        r"\bpaise\b", r"\bhua\b", r"\bhue\b", r"\bcollege ne\b", r"\bbol\b",
        r"\brahe\b", r"\bkuch\b", r"\bko\b", r"\bka\b", r"\bki\b", r"\bke\b",
        r"\bme\b", r"\bse\b", r"\bpar\b", r"\bmera\b", r"\bmeri\b", r"\bmere\b",
        r"\bunhe\b", r"\bphir\b", r"\bbhi\b", r"\baaya\b", r"\baayi\b"
    ]
    hinglish_matches = sum(1 for p in hinglish_markers if re.search(p, text, re.IGNORECASE))
    if hinglish_matches >= 2:
        return "hinglish"
    
    return "en"


def classify_complaint(
    title: str,
    description: str,
    language: Optional[str] = None,
    threshold: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Perform explainable multilingual triage on complaint text.
    Returns:
      category, priority (urgency), destination_cell, confidence_score,
      reasons, triage_method, needs_human_review, confidence_threshold.
    """
    confidence_threshold = threshold if threshold is not None else DEFAULT_CONFIDENCE_THRESHOLD
    combined_text = f"{title}\n{description}".strip()
    
    detected_lang = language or detect_language(combined_text)
    
    # Optional spaCy text processing
    spacy_entities = []
    if nlp is not None:
        try:
            doc = nlp(title[:500])
            spacy_entities = [ent.text for ent in doc.ents]
        except Exception:
            pass
    
    best_category = "OTHER"
    best_score = 0
    matched_reasons = []
    matched_cell = "PGRC"
    matched_urgency = "MEDIUM"
    
    # Evaluate rule matches across each category
    category_scores = {}
    
    for cat_name, rules in CATEGORY_RULES.items():
        score = 0
        cat_reasons = []
        
        # Test English rules
        for pat in rules["english"]:
            title_match = re.search(pat, title, re.IGNORECASE)
            desc_match = re.search(pat, description, re.IGNORECASE)
            if title_match and desc_match:
                score += 55
                cat_reasons.append(f"Title and description match English pattern '{title_match.group(0)}'")
            elif title_match:
                score += 45
                cat_reasons.append(f"Title matches English pattern '{title_match.group(0)}'")
            elif desc_match:
                score += 35
                cat_reasons.append(f"Description matches English pattern '{desc_match.group(0)}'")
        
        # Test Hindi rules (Devanagari)
        for pat in rules["hindi"]:
            m_title = re.search(pat, title)
            m_desc = re.search(pat, description)
            if m_title and m_desc:
                score += 65
                cat_reasons.append(f"Title and description match Hindi pattern '{m_title.group(0)}'")
            elif m_title:
                score += 55
                cat_reasons.append(f"Title matches Hindi pattern '{m_title.group(0)}'")
            elif m_desc:
                score += 45
                cat_reasons.append(f"Description matches Hindi pattern '{m_desc.group(0)}'")
                
        # Test Hinglish rules
        for pat in rules["hinglish"]:
            m_title = re.search(pat, title, re.IGNORECASE)
            m_desc = re.search(pat, description, re.IGNORECASE)
            if m_title and m_desc:
                score += 60
                cat_reasons.append(f"Title and description match Hinglish expression '{m_title.group(0)}'")
            elif m_title:
                score += 50
                cat_reasons.append(f"Title matches Hinglish expression '{m_title.group(0)}'")
            elif m_desc:
                score += 40
                cat_reasons.append(f"Description matches Hinglish expression '{m_desc.group(0)}'")
        
        if score > 0:
            category_scores[cat_name] = (score, rules["cell"], rules["urgency"], cat_reasons)
    
    if category_scores:
        # Pick category with highest score
        sorted_cats = sorted(category_scores.items(), key=lambda item: item[1][0], reverse=True)
        top_cat, (raw_score, cell, urgency, reasons) = sorted_cats[0]
        
        best_category = top_cat
        matched_cell = cell
        matched_urgency = urgency
        
        # Normalize confidence to 0-100 scale
        if raw_score >= 80:
            confidence = min(98, 88 + (raw_score - 80) // 10)
        elif raw_score >= 45:
            confidence = min(87, 75 + (raw_score - 45) // 5)
        else:
            confidence = max(40, 50 + raw_score // 2)
            
        matched_reasons = reasons[:3]
        matched_reasons.append(f"Classified into {best_category} with {confidence}% rule concordance.")
        matched_reasons.append(f"Assigned destination cell {matched_cell} and priority {matched_urgency}.")
    else:
        # Ambiguous, low-confidence or generic grievance
        best_category = "OTHER"
        matched_cell = "PGRC"
        matched_urgency = "MEDIUM"
        confidence = 35
        matched_reasons = [
            "Text lacked strong category-specific keywords or regulatory violation markers.",
            "Confidence score is below the threshold; flagged for mandatory human review.",
            "Assigned fallback destination PGRC cell under general grievance category."
        ]
    
    needs_review = confidence < confidence_threshold
    
    if needs_review and "Flagged for mandatory human review" not in " ".join(matched_reasons):
        matched_reasons.append(
            f"Confidence score ({confidence}%) is below the configured threshold ({confidence_threshold}%). "
            "Case flagged for officer review."
        )

    return {
        "category": best_category,
        "priority": matched_urgency,
        "destination_cell": matched_cell,
        "confidence_score": confidence,
        "reasons": matched_reasons,
        "triage_method": "rule-based/assisted triage",
        "needs_human_review": needs_review,
        "confidence_threshold": confidence_threshold,
        "language_detected": detected_lang,
    }
