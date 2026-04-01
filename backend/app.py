from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import joblib
import pandas as pd
import shap
import os
import json
import re
from pathlib import Path
from groq import Groq
from typing import List, Optional
from dotenv import load_dotenv

from model.explain import get_reasons
from model.llm_explainer import generate_explanation
from rag_helper import retrieve_relevant_knowledge

# ─────────────────────────────────────────────
# Load .env safely
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ENV_PATHS = [
    BASE_DIR / ".env",           # backend/.env
    BASE_DIR.parent / ".env",    # project/.env
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


def build_default_input() -> dict:
    return {col: medians.get(col, 0) for col in feature_names}


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
    allow_credentials=False,  # safer with wildcard origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Input schemas
# ─────────────────────────────────────────────
class CustomerData(BaseModel):
    tenure: float
    monthlyCharges: float


class TextInput(BaseModel):
    text: str


class CustomerBatchData(BaseModel):
    data: List[CustomerData]


class ChatRequest(BaseModel):
    user_message: str
    prediction_data: dict

# ─────────────────────────────────────────────
# Helper: extract features using Groq
# ─────────────────────────────────────────────
def extract_features_with_groq(text: str) -> dict:
    if not groq_client:
        print("Groq client not available. Returning empty features.")
        return {}

    prompt = f"""
You are a data extraction assistant. Extract customer churn features from the text below and output only a JSON object with the exact keys:
gender, SeniorCitizen, Partner, Dependents, tenure, PhoneService, MultipleLines, InternetService,
OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies,
Contract, PaperlessBilling, PaymentMethod, MonthlyCharges, TotalCharges, Segment.

Mappings:
- gender: 0=Female, 1=Male
- SeniorCitizen: 0=No, 1=Yes
- Partner: 0=No, 1=Yes
- Dependents: 0=No, 1=Yes
- PhoneService: 0=No, 1=Yes
- MultipleLines: 0=No, 1=Yes, 2=No phone service
- InternetService: 0=No, 1=DSL, 2=Fiber optic
- OnlineSecurity: 0=No, 1=Yes, 2=No internet service
- OnlineBackup: 0=No, 1=Yes, 2=No internet service
- DeviceProtection: 0=No, 1=Yes, 2=No internet service
- TechSupport: 0=No, 1=Yes, 2=No internet service
- StreamingTV: 0=No, 1=Yes, 2=No internet service
- StreamingMovies: 0=No, 1=Yes, 2=No internet service
- Contract: 0=Month-to-month, 1=One year, 2=Two year
- PaperlessBilling: 0=No, 1=Yes
- PaymentMethod: 0=Electronic check, 1=Mailed check, 2=Bank transfer (automatic), 3=Credit card (automatic)
- Segment: integer (0 if not specified)
- MonthlyCharges, TotalCharges: float
- tenure: integer (months)

If a feature is not mentioned, set its value to null.

Text: {text}
JSON:
"""
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL_NAME,
            temperature=0,
            max_tokens=500,
        )
        raw = chat_completion.choices[0].message.content or ""
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in Groq response")
        return json.loads(json_match.group())
    except Exception as e:
        print(f"Groq extraction error: {e}")
        return {}

# ─────────────────────────────────────────────
# Helper: retention recommendations
# ─────────────────────────────────────────────
def generate_retention_recommendations(input_df, reasons):
    retention_recommendations = {}

    for r in reasons:
        feature = r["feature"]
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
        else:
            retention_recommendations[feature] = {
                "retention_action": "Analyze this feature and take retention measures"
            }

    return retention_recommendations

# ─────────────────────────────────────────────
# Helper: initial RAG retention response
# ─────────────────────────────────────────────
def generate_rag_retention_response(
    churn_probability: float,
    risk_level: str,
    reasons: list,
    extracted_features: Optional[dict] = None
):
    if not groq_client:
        return "AI retention assistant is unavailable because GROQ_API_KEY is not set or invalid."

    top_features = ", ".join([r["feature"] for r in reasons[:3]]) if reasons else "unknown"

    query = f"""
Customer churn probability: {churn_probability}
Risk level: {risk_level}
Top churn factors: {top_features}
Customer features: {extracted_features if extracted_features else {}}
Suggest retention strategies.
"""

    try:
        retrieved_chunks = retrieve_relevant_knowledge(query, top_k=3)
        context = "\n".join(retrieved_chunks) if retrieved_chunks else "No retrieved knowledge available."
    except Exception as e:
        print("RAG retrieval error:", e)
        context = "No retrieved knowledge available."

    prompt = f"""
You are a customer retention assistant.

Use this retrieved knowledge:
{context}

Customer summary:
- Churn probability: {churn_probability}
- Risk level: {risk_level}
- Top churn factors: {top_features}
- Customer features: {extracted_features if extracted_features else {}}

Respond in a chatbot-friendly style with:
1. A short summary
2. Top 3 retention steps
3. Why these steps fit this customer

Keep the answer practical, clear, and business-friendly.
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
        return "Unable to generate AI retention guidance right now."

# ─────────────────────────────────────────────
# Helper: follow-up chatbot response
# ─────────────────────────────────────────────
def generate_followup_chat_response(user_message: str, prediction_data: dict):
    if not groq_client:
        return "AI retention assistant is unavailable because GROQ_API_KEY is not set or invalid."

    churn_probability = prediction_data.get("churn_probability", "unknown")
    risk_level = prediction_data.get("risk_level", "unknown")
    reasons = prediction_data.get("reasons", [])
    extracted_features = prediction_data.get("extracted_features", {})

    top_features = ", ".join([r["feature"] for r in reasons[:3]]) if reasons else "unknown"

    query = f"""
Customer churn probability: {churn_probability}
Risk level: {risk_level}
Top churn factors: {top_features}
Customer features: {extracted_features}
User question: {user_message}
Suggest retention strategies and answer the user's question.
"""

    try:
        retrieved_chunks = retrieve_relevant_knowledge(query, top_k=3)
        context = "\n".join(retrieved_chunks) if retrieved_chunks else "No retrieved knowledge available."
    except Exception as e:
        print("Follow-up retrieval error:", e)
        context = "No retrieved knowledge available."

    prompt = f"""
You are an AI retention assistant for a churn prediction dashboard.

Use this retrieved knowledge:
{context}

Prediction context:
- Churn probability: {churn_probability}
- Risk level: {risk_level}
- Top churn factors: {top_features}
- Customer features: {extracted_features}

User question:
{user_message}

Answer the user's question clearly and practically.
If relevant:
1. Suggest retention actions
2. Explain why they fit this customer
3. Keep it concise and business-friendly
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
        print("Follow-up chatbot error:", e)
        return "Unable to generate a follow-up response right now."

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


@app.post("/predict")
def predict_churn(data: CustomerData):
    try:
        input_dict = build_default_input()
        input_dict["tenure"] = float(data.tenure)
        input_dict["MonthlyCharges"] = float(data.monthlyCharges)

        input_df = pd.DataFrame([input_dict])[feature_names]

        prob = float(model.predict_proba(input_df)[0][1])
        prediction = "Churn" if prob >= 0.5 else "No Churn"
        risk_level = "High" if prob > 0.7 else "Medium" if prob > 0.4 else "Low"

        reasons = get_reasons(input_df, explainer)
        explanation = generate_explanation(reasons)
        retention_recommendations = generate_retention_recommendations(input_df, reasons)
        chatbot_retention_response = generate_rag_retention_response(
            churn_probability=round(prob, 4),
            risk_level=risk_level,
            reasons=reasons,
            extracted_features=input_dict,
        )

        return {
            "churn_probability": round(prob, 4),
            "prediction": prediction,
            "risk_level": risk_level,
            "reasons": reasons,
            "explanation": explanation,
            "retention_recommendations": retention_recommendations,
            "chatbot_retention_response": chatbot_retention_response,
            "extracted_features": input_dict,
        }

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}


@app.post("/predict_text")
def predict_from_text(input_data: TextInput):
    try:
        extracted = extract_features_with_groq(input_data.text)

        input_dict = {}
        for col in feature_names:
            val = extracted.get(col)
            if val is None:
                val = medians.get(col, 0)
            input_dict[col] = val

        input_df = pd.DataFrame([input_dict])[feature_names]

        prob = float(model.predict_proba(input_df)[0][1])
        prediction = "Churn" if prob >= 0.5 else "No Churn"
        risk_level = "High" if prob > 0.7 else "Medium" if prob > 0.4 else "Low"

        reasons = get_reasons(input_df, explainer)
        explanation = generate_explanation(reasons)
        retention_recommendations = generate_retention_recommendations(input_df, reasons)
        chatbot_retention_response = generate_rag_retention_response(
            churn_probability=round(prob, 4),
            risk_level=risk_level,
            reasons=reasons,
            extracted_features=extracted,
        )

        return {
            "churn_probability": round(prob, 4),
            "prediction": prediction,
            "risk_level": risk_level,
            "reasons": reasons,
            "explanation": explanation,
            "extracted_features": extracted,
            "retention_recommendations": retention_recommendations,
            "chatbot_retention_response": chatbot_retention_response,
        }

    except Exception as e:
        print("Text prediction error:", e)
        return {"error": str(e)}


@app.post("/predict/batch")
def predict_batch(batch_data: CustomerBatchData):
    results = []

    try:
        for customer in batch_data.data:
            input_dict = build_default_input()
            input_dict["tenure"] = float(customer.tenure)
            input_dict["MonthlyCharges"] = float(customer.monthlyCharges)

            input_df = pd.DataFrame([input_dict])[feature_names]

            prob = float(model.predict_proba(input_df)[0][1])
            prediction = "Churn" if prob >= 0.5 else "No Churn"
            risk_level = "High" if prob > 0.7 else "Medium" if prob > 0.4 else "Low"

            reasons = get_reasons(input_df, explainer)
            explanation = generate_explanation(reasons)
            retention_recommendations = generate_retention_recommendations(input_df, reasons)
            chatbot_retention_response = generate_rag_retention_response(
                churn_probability=round(prob, 4),
                risk_level=risk_level,
                reasons=reasons,
                extracted_features=input_dict,
            )

            results.append({
                "tenure": customer.tenure,
                "MonthlyCharges": customer.monthlyCharges,
                "churn_probability": round(prob, 4),
                "prediction": prediction,
                "risk_level": risk_level,
                "reasons": reasons,
                "explanation": explanation,
                "retention_recommendations": retention_recommendations,
                "chatbot_retention_response": chatbot_retention_response,
            })

        return {"results": results}

    except Exception as e:
        print("Batch prediction error:", e)
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