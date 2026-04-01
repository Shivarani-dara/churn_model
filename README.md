
# 🚀 ChurnGuard AI

### Intelligent Customer Churn Prediction & Retention System

---

## 📌 Overview

**ChurnGuard AI** is a full-stack AI application that predicts customer churn, explains the reasons behind it, and provides intelligent retention strategies.

This system combines:

* Machine Learning for prediction
* Explainable AI (SHAP) for insights
* NLP for text-based input
* RAG-based chatbot for retention guidance
* React dashboard for visualization

👉 The goal is to help businesses **predict, understand, and prevent customer churn proactively**.

---

## 🎯 Features

### 🔹 1. Churn Prediction

* Predicts churn probability using trained ML model
* Outputs:

  * Probability score
  * Prediction (Churn / No Churn)
  * Risk level (Low / Medium / High)

---

### 🔹 2. Explainable AI (SHAP)

* Displays top features influencing churn
* Helps answer:

  * *Why is this customer at risk?*

---

### 🔹 3. Natural Language Input (NLP)

* Accepts plain English input like:

  > “Customer has 2 years tenure, pays $80 monthly…”

* Uses LLM to:

  * Extract features
  * Convert to structured data
  * Run prediction

---

### 🔹 4. Retention Recommendation System

* Provides feature-based retention suggestions:

  * Discounts
  * Contract upgrades
  * Service improvements

---

### 🔹 5. AI Chatbot (RAG-based)

* Interactive chatbot UI
* Takes:

  * Model output
  * User queries
* Generates:

  * Personalized retention strategies

---

### 🔹 6. Batch Prediction (CSV Upload)

* Upload CSV file with multiple customers
* Returns:

  * Predictions for each row
  * Risk levels
* Useful for business-scale analysis

---

### 🔹 7. Interactive Dashboard

* Built using React
* Features:

  * Graph visualization
  * Prediction cards
  * History tracking
  * Chatbot interface

---

## 🏗️ System Architecture

```
User Input (Form / Text / CSV)
        ↓
React Frontend
        ↓
FastAPI Backend
        ↓
Feature Extraction (LLM)
        ↓
ML Model Prediction
        ↓
SHAP Explanation
        ↓
RAG Chatbot (Retention Strategy)
        ↓
Response to UI
```

---

## 🗂️ Project Structure

```
project/
│
├── backend/
│   ├── app.py
│   ├── rag_helper.py
│   ├── model/
│   │   ├── churn_model.pkl
│   │   ├── feature_names.pkl
│   │   └── explain.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Form.js
│   │   │   ├── Graph.js
│   │   │   ├── ResultCard.js
│   │   │   ├── TextPredict.js
│   │   │   ├── BatchUpload.js
│   │   │   ├── BatchResult.js
│   │   │   └── RetentionChat.js
│   │   ├── hooks/
│   │   │   ├── useChurnPrediction.js
│   │   │   └── useBatchPrediction.js
│   │   ├── services/
│   │   │   └── api.js
│   │   └── App.js
│
├── requirements.txt
├── .gitignore
├── README.md
```

---

## 🛠️ Tech Stack

### 🔹 Backend

* FastAPI
* Scikit-learn
* SHAP
* Pandas, NumPy
* Groq API (LLM)
* Sentence Transformers (RAG)

### 🔹 Frontend

* React.js
* Tailwind CSS
* Chart libraries

---

## 🚀 How to Run the Project

### 🔹 Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

API runs at:

```
http://127.0.0.1:8000
```

---

### 🔹 Frontend

```bash
cd frontend
npm install
npm start
```

Frontend runs at:

```
http://localhost:3000
```

---

## 🔐 Environment Variables

Set your API key:

```bash
export GROQ_API_KEY=your_api_key_here
```

---

## 📊 Sample API Request

```bash
curl -X POST http://127.0.0.1:8000/predict \
-H "Content-Type: application/json" \
-d '{"tenure": 12, "monthlyCharges": 50}'
```

---

## 📈 Sample Output

```json
{
  "churn_probability": 0.35,
  "prediction": "No Churn",
  "risk_level": "Low",
  "reasons": [...],
  "retention_recommendations": {...}
}
```

---

## 💡 Key Highlights

* Combines ML + NLP + RAG in one system
* Provides explainable predictions
* Includes chatbot for business decisions
* Supports both individual and bulk predictions
* Designed as a real-world business solution

---

## 👩‍💻 Team

* D. Shivarani
* Team Members

Department: Computer Science Engineering

---

## 📄 License

This project is developed for academic purposes.

---

## 🎯 Conclusion

ChurnGuard AI is not just a prediction system —
it is a **decision-support system** that helps businesses:

✔ Predict churn
✔ Understand causes
✔ Take proactive actions

---

⭐ *If you found this project useful, consider giving it a star!*




