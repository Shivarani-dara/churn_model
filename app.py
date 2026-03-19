# api.py

from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd

# Load saved model and features
model = joblib.load('churn_model.pkl')
feature_names = joblib.load('feature_names.pkl')

app = FastAPI(title="Customer Churn Prediction API")

class CustomerData(BaseModel):
    gender: int
    SeniorCitizen: int
    Partner: int
    Dependents: int
    tenure: int
    PhoneService: int
    MultipleLines: int
    InternetService: int
    OnlineSecurity: int
    OnlineBackup: int
    DeviceProtection: int
    TechSupport: int
    StreamingTV: int
    StreamingMovies: int
    Contract: int
    PaperlessBilling: int
    PaymentMethod: int
    MonthlyCharges: float
    TotalCharges: float
    Segment: int

@app.get("/")
def root():
    return {"message": "Churn Prediction API is running"}

@app.post("/predict")
def predict_churn(data: CustomerData):
    input_df = pd.DataFrame([data.dict()])

    # Align with training features
    for col in feature_names:
        if col not in input_df.columns:
            input_df[col] = 0
    input_df = input_df[feature_names]

    prob = model.predict_proba(input_df)[0][1]
    prediction = "Churn" if prob >= 0.5 else "No Churn"

    return {
        "churn_probability": round(float(prob), 4),
        "prediction": prediction
    }