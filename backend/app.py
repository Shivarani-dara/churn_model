from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import joblib
import pandas as pd
import shap
import os
import io
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from groq import Groq
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from collections import Counter
import json
from datetime import datetime

from model.explain import get_reasons
from model.llm_explainer import generate_explanation
from rag_helper import retrieve_relevant_knowledge

# ─────────────────────────────────────────────
# Load .env safely
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ENV_PATHS = [
    BASE_DIR / ".env",
    BASE_DIR.parent / ".env",
]

for env_path in ENV_PATHS:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"Loaded environment from: {env_path}")
        break
else:
    print("No .env file found in backend/ or project root.")

# ─────────────────────────────────────────────
# Global variables
# ─────────────────────────────────────────────
model = None
feature_names = None
explainer = None
medians = None
groq_client = None

GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
DB_PATH = BASE_DIR / "churn_results.db"

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def get_clean_env_value(key: str) -> Optional[str]:
    value = os.getenv(key)
    if value is None:
        return None
    value = value.strip().strip('"').strip("'")
    return value or None


def get_groq_client() -> Optional[Groq]:
    groq_api_key = get_clean_env_value("GROQ_API_KEY")

    if not groq_api_key:
        print("GROQ_API_KEY not set. Groq-powered features disabled.")
        return None

    if not groq_api_key.startswith("gsk_"):
        print("GROQ_API_KEY format looks invalid. Expected key to start with 'gsk_'.")
        return None

    try:
        client = Groq(api_key=groq_api_key)
        print("Groq client initialized")
        print("Groq key loaded:", groq_api_key[:8] + "...")
        return client
    except Exception as e:
        print("Failed to initialize Groq client:", e)
        return None


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS churn_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            email TEXT,
            churn_probability REAL,
            prediction TEXT,
            risk_level TEXT,
            top_reason_1 TEXT,
            top_reason_2 TEXT,
            top_reason_3 TEXT,
            reasons_summary TEXT,
            rag_summary TEXT,
            rag_steps_json TEXT,
            email_message TEXT,
            suggested_offer TEXT,
            email_status TEXT DEFAULT 'Pending',
            email_sent_at TEXT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("Database ready")


def save_prediction_to_db(result: Dict[str, Any], email: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO churn_results (
            customer_id, email, churn_probability, prediction, risk_level,
            top_reason_1, top_reason_2, top_reason_3, reasons_summary,
            rag_summary, rag_steps_json, email_message, suggested_offer, email_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result.get("customer_id"),
        email,
        result.get("churn_probability"),
        result.get("prediction"),
        result.get("risk_level"),
        result.get("top_reason_1"),
        result.get("top_reason_2"),
        result.get("top_reason_3"),
        result.get("reasons_summary"),
        result.get("rag_summary"),
        json.dumps(result.get("rag_steps", [])),
        result.get("email_message"),
        result.get("suggested_offer"),
        "Pending"
    ))

    conn.commit()
    conn.close()


def fetch_high_risk_customers(limit: int = 10):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM churn_results
        WHERE risk_level = 'High'
        ORDER BY churn_probability DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_email_status(record_id: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE churn_results
        SET email_status = ?, email_sent_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, record_id))

    conn.commit()
    conn.close()


def build_default_input() -> dict:
    return {col: medians.get(col, 0) for col in feature_names}


def normalize_input_keys(input_data: Dict[str, Any]) -> Dict[str, Any]:
    key_mapping = {
        "monthlyCharges": "MonthlyCharges",
        "totalCharges": "TotalCharges",
    }

    normalized = {}
    for key, value in input_data.items():
        mapped_key = key_mapping.get(key, key)
        normalized[mapped_key] = value

    return normalized


def build_customer_input(customer_data: Dict[str, Any]) -> dict:
    input_dict = build_default_input()
    normalized_data = normalize_input_keys(customer_data)

    for key, value in normalized_data.items():
        if key in input_dict and value is not None:
            try:
                input_dict[key] = float(value)
            except (ValueError, TypeError):
                pass

    return input_dict


def build_fallback_reasons(input_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    fallback = []

    tenure = float(input_dict.get("tenure", 0) or 0)
    monthly = float(input_dict.get("MonthlyCharges", 0) or 0)
    contract = float(input_dict.get("Contract", 0) or 0)
    online_security = float(input_dict.get("OnlineSecurity", 0) or 0)
    tech_support = float(input_dict.get("TechSupport", 0) or 0)
    total = float(input_dict.get("TotalCharges", 0) or 0)
    paperless = float(input_dict.get("PaperlessBilling", 0) or 0)

    if contract == 0:
        fallback.append({
            "feature": "Contract",
            "impact": 0.18,
            "reason": "Customer is on a month-to-month contract, which often increases churn risk."
        })

    if monthly >= 70:
        fallback.append({
            "feature": "MonthlyCharges",
            "impact": 0.16,
            "reason": "Monthly charges are relatively high."
        })

    if tenure <= 12:
        fallback.append({
            "feature": "tenure",
            "impact": 0.14,
            "reason": "Customer has low tenure and may still be in the early loyalty stage."
        })

    if online_security == 0:
        fallback.append({
            "feature": "OnlineSecurity",
            "impact": 0.13,
            "reason": "Online security is not enabled."
        })

    if tech_support == 0:
        fallback.append({
            "feature": "TechSupport",
            "impact": 0.12,
            "reason": "Tech support is not enabled."
        })

    if total >= 2000:
        fallback.append({
            "feature": "TotalCharges",
            "impact": 0.10,
            "reason": "Customer has high accumulated value and should be carefully retained."
        })

    if paperless == 0:
        fallback.append({
            "feature": "PaperlessBilling",
            "impact": 0.08,
            "reason": "Customer is not on paperless billing."
        })

    return fallback[:5]


def make_table_friendly_text(reasons, retention_recommendations, rag_text):
    reason_items = []

    for r in reasons[:3]:
        feature = r.get("feature", "")
        reason_text = r.get("reason")

        if not reason_text:
            impact_val = round(r.get("impact", 0), 4)
            reason_text = f"impact {impact_val}"

        reason_items.append(f"{feature}: {reason_text}")

    reasons_summary = "; ".join(reason_items) if reason_items else "No major reasons identified"

    retention_summary = "; ".join(
        [v.get("retention_action", "") for _, v in retention_recommendations.items()]
    ) if retention_recommendations else "No rule-based retention actions"

    rag_summary = rag_text.replace("\n", " | ") if rag_text else "No AI retention analysis"

    return reasons_summary, retention_summary, rag_summary


def generate_offer(risk_level: str, reasons: List[Dict[str, Any]]) -> Optional[str]:
    if risk_level != "High":
        return None

    top_features = [r.get("feature") for r in reasons]

    if "MonthlyCharges" in top_features:
        return "20% discount for next 3 months"

    if "Contract" in top_features:
        return "Upgrade to yearly plan with special savings"

    if "TechSupport" in top_features:
        return "Free premium tech support for 1 month"

    if "OnlineSecurity" in top_features:
        return "Free online security add-on for 2 months"

    if "tenure" in top_features:
        return "Welcome loyalty offer for new customers"

    return "Exclusive loyalty reward offer"


def generate_chart_data(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    prediction_counts = Counter([r.get("prediction", "Unknown") for r in results])
    risk_counts = Counter([r.get("risk_level", "Unknown") for r in results])

    top_reason_counts = Counter()
    retention_action_counts = Counter()

    churn_probabilities = []
    customer_probabilities = []

    for idx, r in enumerate(results, start=1):
        churn_prob = float(r.get("churn_probability", 0) or 0)
        churn_probabilities.append(churn_prob)

        customer_probabilities.append({
            "customer_id": r.get("customer_id") or f"Customer {idx}",
            "churn_probability": round(churn_prob * 100, 2)
        })

        for reason in r.get("reasons", []):
            feature = reason.get("feature")
            if feature:
                top_reason_counts[feature] += 1

        for _, value in r.get("retention_recommendations", {}).items():
            action = value.get("retention_action")
            if action:
                retention_action_counts[action] += 1

    avg_churn_probability = round(
        (sum(churn_probabilities) / len(churn_probabilities)) * 100, 2
    ) if churn_probabilities else 0

    customer_probabilities = sorted(
        customer_probabilities,
        key=lambda x: x["churn_probability"],
        reverse=True
    )[:10]

    return {
        "prediction_distribution": dict(prediction_counts),
        "risk_distribution": dict(risk_counts),
        "top_reasons": dict(top_reason_counts.most_common(10)),
        "retention_actions": dict(retention_action_counts.most_common(10)),
        "average_churn_probability": avg_churn_probability,
        "top_risky_customers": customer_probabilities,
    }


def predict_one_customer(customer_dict: Dict[str, Any]) -> Dict[str, Any]:
    input_dict = build_customer_input(customer_dict)
    input_df = pd.DataFrame([input_dict])[feature_names]

    prob = float(model.predict_proba(input_df)[0][1])
    prediction = "Churn" if prob >= 0.5 else "No Churn"
    risk_level = "High" if prob > 0.7 else "Medium" if prob > 0.4 else "Low"

    reasons = get_reasons(input_df, explainer)
    if not reasons:
        reasons = build_fallback_reasons(input_dict)

    explanation = generate_explanation(reasons)
    retention_recommendations = generate_retention_recommendations(input_df, reasons)

    structured_plan = generate_structured_rag_retention_plan(
        churn_probability=round(prob, 4),
        risk_level=risk_level,
        reasons=reasons,
        extracted_features=input_dict,
    )

    rag_summary = structured_plan.get("summary", "")
    rag_steps = structured_plan.get("steps", [])
    email_message = structured_plan.get("email_message", "")

    chatbot_retention_response = (
        f"Summary: {rag_summary}\n\n"
        f"Steps:\n" +
        "\n".join(
            [
                f"{idx+1}. {step.get('title', '')} - {step.get('description', '')} "
                f"(Priority: {step.get('priority', '')}, Channel: {step.get('channel', '')})"
                for idx, step in enumerate(rag_steps)
            ]
        )
        if rag_steps else rag_summary
    )

    reasons_summary, retention_summary, _ = make_table_friendly_text(
        reasons,
        retention_recommendations,
        rag_summary
    )

    suggested_offer = rag_steps[0]["title"] if rag_steps else generate_offer(risk_level, reasons)

    return {
        "customer_id": customer_dict.get("customer_id"),
        "email": customer_dict.get("email"),
        "churn_probability": round(prob, 4),
        "prediction": prediction,
        "risk_level": risk_level,
        "reasons": reasons,
        "explanation": explanation,
        "retention_recommendations": retention_recommendations,
        "chatbot_retention_response": chatbot_retention_response,
        "extracted_features": input_dict,
        "used_features": input_dict,
        "top_reason_1": reasons[0]["feature"] if len(reasons) > 0 else "",
        "top_reason_2": reasons[1]["feature"] if len(reasons) > 1 else "",
        "top_reason_3": reasons[2]["feature"] if len(reasons) > 2 else "",
        "reasons_summary": reasons_summary,
        "retention_summary": retention_summary,
        "rag_summary": rag_summary,
        "rag_steps": rag_steps,
        "email_message": email_message,
        "suggested_offer": suggested_offer,
    }


# ─────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, feature_names, explainer, medians, groq_client

    try:
        model = joblib.load(BASE_DIR / "model" / "churn_model.pkl")
        feature_names = joblib.load(BASE_DIR / "model" / "feature_names.pkl")
        background = joblib.load(BASE_DIR / "model" / "background.pkl")

        medians = background.median().to_dict()
        explainer = shap.KernelExplainer(model.predict_proba, background)

        groq_client = get_groq_client()
        init_db()

        print("Model loaded")
        print("Features:", feature_names)
        print("SHAP explainer ready")

    except Exception as e:
        print("Startup error:", e)
        raise

    yield


# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
app = FastAPI(title="Customer Churn Prediction API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Input schemas
# ─────────────────────────────────────────────
class CustomerData(BaseModel):
    customer_id: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[float] = None
    SeniorCitizen: Optional[float] = None
    Partner: Optional[float] = None
    Dependents: Optional[float] = None
    tenure: Optional[float] = None
    PhoneService: Optional[float] = None
    MultipleLines: Optional[float] = None
    InternetService: Optional[float] = None
    OnlineSecurity: Optional[float] = None
    OnlineBackup: Optional[float] = None
    DeviceProtection: Optional[float] = None
    TechSupport: Optional[float] = None
    StreamingTV: Optional[float] = None
    StreamingMovies: Optional[float] = None
    Contract: Optional[float] = None
    PaperlessBilling: Optional[float] = None
    PaymentMethod: Optional[float] = None
    MonthlyCharges: Optional[float] = None
    TotalCharges: Optional[float] = None
    Segment: Optional[float] = None

    monthlyCharges: Optional[float] = None
    totalCharges: Optional[float] = None


class CustomerBatchData(BaseModel):
    data: List[CustomerData]


class ChatRequest(BaseModel):
    user_message: str
    prediction_data: dict


class SendSingleEmailRequest(BaseModel):
    customer_id: Optional[str] = None
    email: str
    suggested_offer: str


# ─────────────────────────────────────────────
# Retention recommendation helper
# ─────────────────────────────────────────────
def generate_retention_recommendations(input_df, reasons):
    retention_recommendations = {}

    for r in reasons:
        feature = r["feature"]

        if feature not in input_df.columns:
            continue

        val = input_df.iloc[0][feature]

        if feature == "Contract":
            retention_recommendations[feature] = {
                "retention_action": "Offer longer contract (1-2 years)"
            }
        elif feature == "OnlineSecurity" and val == 0:
            retention_recommendations[feature] = {
                "retention_action": "Provide free online security upgrade"
            }
        elif feature == "TechSupport" and val == 0:
            retention_recommendations[feature] = {
                "retention_action": "Offer premium tech support plan"
            }
        elif feature == "PaperlessBilling" and val == 0:
            retention_recommendations[feature] = {
                "retention_action": "Encourage paperless billing for convenience"
            }
        elif feature == "MonthlyCharges":
            retention_recommendations[feature] = {
                "retention_action": "Offer discounts or bundle deals"
            }
        elif feature == "tenure":
            retention_recommendations[feature] = {
                "retention_action": "Improve onboarding and loyalty engagement"
            }
        elif feature == "TotalCharges":
            retention_recommendations[feature] = {
                "retention_action": "Prioritize this high-value customer with a personalized retention offer"
            }
        else:
            retention_recommendations[feature] = {
                "retention_action": "Analyze this feature and take retention measures"
            }

    return retention_recommendations
def generate_structured_rag_retention_plan(
    churn_probability: float,
    risk_level: str,
    reasons: list,
    extracted_features: Optional[dict] = None
):
    try:
        retrieved_chunks = retrieve_relevant_knowledge(
            query="retention strategy",
            top_k=3,
            risk_level=risk_level,
            reasons=reasons,
            customer_features=extracted_features if extracted_features else {}
        )
    except Exception as e:
        print("Structured RAG retrieval error:", e)
        retrieved_chunks = []

    if retrieved_chunks and isinstance(retrieved_chunks[0], dict):
        context = "\n".join([
            f"Title: {item.get('title', '')}\n"
            f"Driver: {item.get('driver', '')}\n"
            f"Action: {item.get('action', '')}\n"
            f"Why: {item.get('why', '')}\n"
            f"Priority: {item.get('priority', '')}\n"
            f"Cost: {item.get('cost', '')}\n"
            for item in retrieved_chunks
        ])
    else:
        context = "\n".join([str(item) for item in retrieved_chunks]) if retrieved_chunks else "No retrieved knowledge available."

    top_features = ", ".join([r["feature"] for r in reasons[:3]]) if reasons else "unknown"

    if not groq_client:
        fallback_steps = []
        for item in retrieved_chunks[:3]:
            if isinstance(item, dict):
                fallback_steps.append({
                    "title": item.get("title", "Retention Action"),
                    "description": item.get("action", "Take retention action"),
                    "priority": item.get("priority", "Medium"),
                    "channel": "Email"
                })

        email_message = (
            f"Dear Customer,\n\n"
            f"We value your relationship with us. Based on your current profile, "
            f"we would like to support you with personalized retention benefits.\n\n"
            f"Best regards,\nCustomer Support Team"
        )

        return {
            "summary": f"Customer is at {risk_level} churn risk with probability {churn_probability}.",
            "steps": fallback_steps,
            "email_message": email_message
        }

    prompt = f"""
You are a customer retention assistant.

Use only the retrieved knowledge and the given prediction context.

Return ONLY valid JSON in this exact format:
{{
  "summary": "short business summary",
  "steps": [
    {{
      "title": "step title",
      "description": "clear action description",
      "priority": "High/Medium/Low",
      "channel": "Email/SMS/Call/App"
    }}
  ],
  "email_message": "customer-friendly retention email body"
}}

Rules:
- Give exactly 3 steps
- Keep them practical and business-friendly
- Base them only on retrieved knowledge and actual churn reasons
- Do not include markdown
- Do not include extra text outside JSON

Retrieved knowledge:
{context}

Prediction context:
- Churn probability: {churn_probability}
- Risk level: {risk_level}
- Top churn factors: {top_features}
- Customer features: {extracted_features if extracted_features else {}}
"""

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL_NAME,
            temperature=0.2,
            max_tokens=700,
        )

        content = chat_completion.choices[0].message.content.strip()

        try:
            return json.loads(content)
        except Exception:
            print("Structured JSON parse failed. Raw content:", content)
            return {
                "summary": f"Customer is at {risk_level} churn risk with probability {churn_probability}.",
                "steps": [],
                "email_message": content
            }

    except Exception as e:
        print("Structured RAG generation error:", e)
        return {
            "summary": "Unable to generate structured retention plan right now.",
            "steps": [],
            "email_message": (
                "Dear Customer,\n\n"
                "We value your association with us and would like to support you "
                "with a personalized retention offer.\n\n"
                "Best regards,\nCustomer Support Team"
            )
        }

# ─────────────────────────────────────────────
# RAG response helper
# ─────────────────────────────────────────────
def generate_rag_retention_response(
    churn_probability: float,
    risk_level: str,
    reasons: list,
    extracted_features: Optional[dict] = None
):
    try:
        retrieved_chunks = retrieve_relevant_knowledge(
            query="retention strategy",
            top_k=3,
            risk_level=risk_level,
            reasons=reasons,
            customer_features=extracted_features if extracted_features else {}
        )
    except Exception as e:
        print("RAG retrieval error:", e)
        retrieved_chunks = []

    if not groq_client:
        if not retrieved_chunks:
            return "No retention strategies available."

        lines = []
        lines.append(f"Summary: Customer is at {risk_level} churn risk with probability {churn_probability}.")
        lines.append("Top retention steps:")
        for i, item in enumerate(retrieved_chunks[:3], start=1):
            if isinstance(item, dict):
                lines.append(f"{i}. {item.get('action', 'Take retention action')} ({item.get('title', 'Strategy')})")
            else:
                lines.append(f"{i}. {str(item)}")
        lines.append("Why these steps fit this customer:")
        for item in retrieved_chunks[:3]:
            if isinstance(item, dict):
                lines.append(f"- {item.get('why', '')}")
        return "\n".join(lines)

    top_features = ", ".join([r["feature"] for r in reasons[:3]]) if reasons else "fallback drivers"

    if retrieved_chunks and isinstance(retrieved_chunks[0], dict):
        context = "\n".join([
            f"Title: {item.get('title', '')}\n"
            f"Driver: {item.get('driver', '')}\n"
            f"Action: {item.get('action', '')}\n"
            f"Why: {item.get('why', '')}\n"
            f"Priority: {item.get('priority', '')}\n"
            f"Cost: {item.get('cost', '')}\n"
            for item in retrieved_chunks
        ])
    else:
        context = "\n".join([str(item) for item in retrieved_chunks]) if retrieved_chunks else "No retrieved knowledge available."

    prompt = f"""
You are a customer retention assistant.

Use only the retrieved strategies and the given prediction context.
Do not invent churn drivers that are not present in the prediction context.
Prioritize actions that best match the customer's risk level, top churn factors, and feature values.

Retrieved strategies:
{context}

Customer summary:
- Churn probability: {churn_probability}
- Risk level: {risk_level}
- Top churn factors: {top_features}
- Customer features: {extracted_features if extracted_features else {}}

Respond in this format:
1. Summary
2. Top 3 retention steps (ranked)
3. Why these steps fit this customer

Keep the answer practical, specific, and business-friendly.
"""

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL_NAME,
            temperature=0.3,
            max_tokens=400,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print("RAG chatbot error:", e)

        if not retrieved_chunks:
            return "Unable to generate AI retention guidance right now."

        lines = []
        lines.append(f"Summary: Customer is at {risk_level} churn risk with probability {churn_probability}.")
        lines.append("Top retention steps:")
        for i, item in enumerate(retrieved_chunks[:3], start=1):
            if isinstance(item, dict):
                lines.append(f"{i}. {item.get('action', 'Take retention action')} ({item.get('title', 'Strategy')})")
            else:
                lines.append(f"{i}. {str(item)}")
        lines.append("Why these steps fit this customer:")
        for item in retrieved_chunks[:3]:
            if isinstance(item, dict):
                lines.append(f"- {item.get('why', '')}")
        return "\n".join(lines)


# ─────────────────────────────────────────────
# Follow-up chatbot helper
# ─────────────────────────────────────────────
def generate_followup_chat_response(user_message: str, prediction_data: dict):
    if not groq_client:
        return "AI retention assistant is unavailable because GROQ_API_KEY is not set or invalid."

    churn_probability = prediction_data.get("churn_probability", "unknown")
    risk_level = prediction_data.get("risk_level", "unknown")
    reasons = prediction_data.get("reasons", [])
    extracted_features = prediction_data.get("extracted_features", {})
    existing_rag_steps = prediction_data.get("rag_steps", [])
    existing_rag_summary = prediction_data.get("rag_summary", "")

    if not existing_rag_steps:
        structured_plan = generate_structured_rag_retention_plan(
            churn_probability=churn_probability,
            risk_level=risk_level,
            reasons=reasons,
            extracted_features=extracted_features
        )
        existing_rag_summary = structured_plan.get("summary", "")
        existing_rag_steps = structured_plan.get("steps", [])

    rag_context = "\n".join([
        f"{idx+1}. {step.get('title', '')} - {step.get('description', '')} "
        f"(Priority: {step.get('priority', '')}, Channel: {step.get('channel', '')})"
        for idx, step in enumerate(existing_rag_steps)
    ]) if existing_rag_steps else "No structured steps available."

    top_features = ", ".join([r["feature"] for r in reasons[:3]]) if reasons else "unknown"

    prompt = f"""
You are an AI retention assistant for a churn prediction dashboard.

Use only the structured retention plan and prediction context below.
Answer the user's question in a conversational and practical way.

Structured retention summary:
{existing_rag_summary}

Structured retention steps:
{rag_context}

Prediction context:
- Churn probability: {churn_probability}
- Risk level: {risk_level}
- Top churn factors: {top_features}
- Customer features: {extracted_features}

User question:
{user_message}

Answer clearly and practically.
If relevant:
1. Mention the most suitable retention step first
2. Explain why it fits this customer
3. Suggest channel/timing if useful
4. Keep it concise and business-friendly
"""

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL_NAME,
            temperature=0.3,
            max_tokens=450,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print("Follow-up chatbot error:", e)
        return "Unable to generate a follow-up response right now."


# ─────────────────────────────────────────────
# Email helpers
# ─────────────────────────────────────────────
class SendSingleEmailRequest(BaseModel):
    customer_id: Optional[str] = None
    email: str
    email_message: str


# ─────────────────────────────────────────────
# Email helpers
# ─────────────────────────────────────────────
def send_offer_email(to_email: str, customer_id: str, email_message: str):
    sender_email = get_clean_env_value("SENDER_EMAIL")
    sender_password = get_clean_env_value("SENDER_APP_PASSWORD")

    if not sender_email or not sender_password:
        raise Exception("SENDER_EMAIL or SENDER_APP_PASSWORD is missing in .env")

    subject = "Personalized Retention Support for You"

    body = email_message or f"""
Dear {customer_id or 'Customer'},

We value your association with us and would like to support you with a personalized retention plan.

Best regards,
Customer Support Team
"""

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, to_email, msg.as_string())
    server.quit()


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Churn Prediction API is running"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "groq_enabled": groq_client is not None,
    }


@app.get("/high-risk-customers")
def get_high_risk_customers(limit: int = 10):
    try:
        data = fetch_high_risk_customers(limit)
        return {"count": len(data), "customers": data}
    except Exception as e:
        return {"error": str(e)}


@app.post("/predict")
def predict_churn(data: CustomerData):
    try:
        result = predict_one_customer(data.dict())
        if result.get("email"):
            save_prediction_to_db(result, result.get("email"))
        return result
    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}


@app.post("/predict/batch")
def predict_batch(batch_data: CustomerBatchData):
    try:
        results = []
        for customer in batch_data.data:
            result = predict_one_customer(customer.dict())
            save_prediction_to_db(result, result.get("email"))
            results.append(result)

        chart_data = generate_chart_data(results)

        return {
            "total_customers": len(results),
            "high_risk_count": sum(1 for r in results if r["risk_level"] == "High"),
            "medium_risk_count": sum(1 for r in results if r["risk_level"] == "Medium"),
            "low_risk_count": sum(1 for r in results if r["risk_level"] == "Low"),
            "results": results,
            "chart_data": chart_data,
        }

    except Exception as e:
        print("Batch prediction error:", e)
        return {"error": str(e)}


@app.post("/predict/upload-csv")
async def predict_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        results = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            result = predict_one_customer(row_dict)
            save_prediction_to_db(result, result.get("email"))
            results.append(result)

        chart_data = generate_chart_data(results)

        return {
            "total_customers": len(results),
            "high_risk_count": sum(1 for r in results if r["risk_level"] == "High"),
            "medium_risk_count": sum(1 for r in results if r["risk_level"] == "Medium"),
            "low_risk_count": sum(1 for r in results if r["risk_level"] == "Low"),
            "results": results,
            "chart_data": chart_data,
        }

    except Exception as e:
        print("CSV upload error:", e)
        return {"error": str(e)}


@app.post("/send-offer-email")
def send_single_offer_email(data: SendSingleEmailRequest):
    try:
        send_offer_email(
            to_email=data.email,
            customer_id=data.customer_id or "Customer",
            email_message=data.email_message
        )
        return {"message": f"Email sent successfully to {data.email}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/send-high-risk-emails")
def send_high_risk_emails(limit: int = 10):
    try:
        customers = fetch_high_risk_customers(limit)
        sent_count = 0
        failed = []

        for customer in customers:
            email = customer.get("email")
            email_message = customer.get("email_message")
            customer_id = customer.get("customer_id") or "Customer"

            if not email or not email_message:
                failed.append({
                    "customer_id": customer_id,
                    "reason": "Missing email or email message"
                })
                continue

            try:
                send_offer_email(
                    to_email=email,
                    customer_id=customer_id,
                    email_message=email_message
                )
                update_email_status(customer["id"], "Sent")
                sent_count += 1
            except Exception as e:
                failed.append({
                    "customer_id": customer_id,
                    "email": email,
                    "reason": str(e)
                })

        return {
            "message": "Bulk email process completed",
            "sent_count": sent_count,
            "failed": failed
        }

    except Exception as e:
        return {"error": str(e)}


@app.post("/chat_retention")
def chat_retention(chat_request: ChatRequest):
    try:
        reply = generate_followup_chat_response(
            user_message=chat_request.user_message,
            prediction_data=chat_request.prediction_data,
        )
        return {"reply": reply}
    except Exception as e:
        print("Chat retention error:", e)
        return {"error": str(e)}