import json
from pathlib import Path
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_PATH = BASE_DIR / "rag_data" / "retention_knowledge.json"


def load_knowledge_base() -> List[Dict[str, Any]]:
    if not KNOWLEDGE_PATH.exists():
        print(f"Knowledge base file not found: {KNOWLEDGE_PATH}")
        return []

    try:
        with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                print(f"Loaded {len(data)} retention knowledge entries")
                return data
            print("Knowledge base format invalid: expected a list")
            return []
    except Exception as e:
        print(f"Failed to load knowledge base: {e}")
        return []


KNOWLEDGE_BASE = load_knowledge_base()


def derive_customer_tags(customer_features: Dict[str, Any], risk_level: str) -> List[str]:
    tags = []

    tenure = float(customer_features.get("tenure", 0) or 0)
    monthly = float(customer_features.get("MonthlyCharges", 0) or 0)
    total = float(customer_features.get("TotalCharges", 0) or 0)
    contract = int(customer_features.get("Contract", 0) or 0)
    online_security = int(customer_features.get("OnlineSecurity", 0) or 0)
    tech_support = int(customer_features.get("TechSupport", 0) or 0)
    paperless = int(customer_features.get("PaperlessBilling", 0) or 0)

    if tenure <= 12:
        tags.append("new_customer")

    if monthly >= 70:
        tags.append("price_sensitive")

    if contract == 0:
        tags.append("contract_risk")

    if online_security == 0:
        tags.append("low_service_adoption")

    if tech_support == 0:
        tags.append("support_gap")

    if total >= 2000:
        tags.append("high_value_customer")

    if paperless == 1:
        tags.append("digital_engagement")

    if risk_level.lower() == "high":
        tags.append("high_risk")

    if online_security == 0 or tech_support == 0:
        tags.append("cross_sell_candidate")

    return list(set(tags))


def normalize_reason_features(reasons: List[Dict[str, Any]]) -> List[str]:
    return [r.get("feature", "") for r in reasons if r.get("feature")]


def score_entry(
    entry: Dict[str, Any],
    risk_level: str,
    top_features: List[str],
    customer_features: Dict[str, Any],
    customer_tags: List[str]
) -> int:
    score = 0

    entry_driver = entry.get("driver", "")
    entry_risk_levels = [x.lower() for x in entry.get("risk_levels", [])]
    entry_tags = entry.get("customer_tags", [])
    condition = entry.get("condition", "")

    risk_level = risk_level.lower()

    if risk_level in entry_risk_levels:
        score += 15

    if entry_driver in top_features:
        score += 35

    shared_tags = set(entry_tags).intersection(set(customer_tags))
    score += len(shared_tags) * 12

    contract = int(customer_features.get("Contract", 0) or 0)
    monthly = float(customer_features.get("MonthlyCharges", 0) or 0)
    tenure = float(customer_features.get("tenure", 0) or 0)
    online_security = int(customer_features.get("OnlineSecurity", 0) or 0)
    tech_support = int(customer_features.get("TechSupport", 0) or 0)
    total = float(customer_features.get("TotalCharges", 0) or 0)
    paperless = int(customer_features.get("PaperlessBilling", 0) or 0)

    if entry_driver == "Contract" and condition == "month_to_month" and contract == 0:
        score += 25

    if entry_driver == "MonthlyCharges" and condition == "high" and monthly >= 70:
        score += 25

    if entry_driver == "OnlineSecurity" and condition == "not_enabled" and online_security == 0:
        score += 25

    if entry_driver == "TechSupport" and condition == "not_enabled" and tech_support == 0:
        score += 25

    if entry_driver == "tenure" and condition == "low" and tenure <= 12:
        score += 25

    if entry_driver == "TotalCharges" and condition == "high_value_customer" and total >= 2000:
        score += 20

    if entry_driver == "PaperlessBilling" and condition == "enabled_or_promotable":
        score += 8 if paperless == 1 else 5

    if entry_driver == "risk_level" and condition == "high" and risk_level == "high":
        score += 30

    score += int(entry.get("priority", 0))

    return score


def retrieve_relevant_knowledge(
    query: str = "",
    top_k: int = 3,
    risk_level: str = "low",
    reasons: List[Dict[str, Any]] = None,
    customer_features: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    if not KNOWLEDGE_BASE:
        return []

    reasons = reasons or []
    customer_features = customer_features or {}

    top_features = normalize_reason_features(reasons)
    customer_tags = derive_customer_tags(customer_features, risk_level)

    scored_entries = []
    for entry in KNOWLEDGE_BASE:
        score = score_entry(
            entry=entry,
            risk_level=risk_level,
            top_features=top_features,
            customer_features=customer_features,
            customer_tags=customer_tags
        )
        scored_entries.append((score, entry))

    scored_entries.sort(key=lambda x: x[0], reverse=True)

    selected = [entry for score, entry in scored_entries[:top_k] if score > 0]

    if not selected:
        return []

    return selected