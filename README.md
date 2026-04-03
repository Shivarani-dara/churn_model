# 🚀 ChurnGuard AI

### An Intelligent Customer Churn Prediction & Retention Decision System

---

## 📌 1. Introduction

Customer churn is one of the biggest challenges faced by businesses today. Losing customers directly impacts revenue, growth, and brand reputation.

Traditional systems only **identify churn after it happens**, but modern businesses require:

* Early prediction
* Understanding of causes
* Actionable retention strategies

👉 **ChurnGuard AI** is designed to solve this problem by combining **Machine Learning, Explainable AI, Natural Language Processing, and Retrieval-Augmented Generation (RAG)** into a single intelligent system.

---

## 🎯 2. Objective

The main objective of this project is to:

* Predict whether a customer is likely to churn
* Explain the reasons behind the prediction
* Provide actionable retention strategies
* Allow flexible input (form, text, batch data)
* Assist decision-making through an AI chatbot

---

## ⚙️ 3. System Overview

ChurnGuard AI is a **full-stack AI system** consisting of:

### 🔹 Frontend (User Interface)

* Built using React.js
* Allows user interaction via:

  * Form input
  * Natural language input
  * CSV file upload
  * Chatbot interaction

### 🔹 Backend (API + Intelligence Layer)

* Built using FastAPI
* Handles:

  * Data processing
  * Model inference
  * Feature extraction (NLP)
  * Explainability (SHAP)
  * RAG-based chatbot

---

## 🧠 4. Core Technologies Used

### 🔹 Machine Learning

* Model trained using customer dataset
* Predicts churn probability

### 🔹 SHAP (Explainable AI)

* Identifies **which features influenced prediction**
* Helps answer:

  > “Why is this customer likely to churn?”

---

### 🔹 Natural Language Processing (NLP)

* Converts user text into structured features
* Example:

  ```
  Input:
  "Customer has 2 years tenure, pays $80 monthly"

  Output:
  tenure = 24
  MonthlyCharges = 80
  ```

---

### 🔹 RAG (Retrieval-Augmented Generation)

* Combines:

  * Model output
  * Domain knowledge
* Generates:

  * Personalized retention strategies

---

### 🔹 Full Stack Integration

* React → API → ML → AI → Response

---

## 🔄 5. System Workflow

```id="flow123"
User Input (Form / Text / CSV)
        ↓
Frontend (React UI)
        ↓
FastAPI Backend
        ↓
[If text] → Feature Extraction (LLM)
        ↓
Structured Input Data
        ↓
ML Model Prediction
        ↓
SHAP Explanation
        ↓
Retention Logic + RAG Chatbot
        ↓
Final Response (UI)
```

---

## 🧩 6. Functional Modules

### 🔹 6.1 Prediction Module

* Accepts:

  * tenure
  * monthly charges
* Outputs:

  * churn probability
  * prediction label
  * risk level

---

### 🔹 6.2 Explainability Module

* Uses SHAP values
* Displays:

  * Top influencing features
  * Positive/negative impact

---

### 🔹 6.3 NLP Module

* Uses LLM (Groq API)
* Extracts:

  * Numerical and categorical features
* Handles missing values using medians

---

### 🔹 6.4 Retention Recommendation Module

Two approaches:

#### Rule-based:

* Contract → suggest long-term plan
* No security → suggest upgrade
* High charges → suggest discounts

#### AI-based:

* Uses RAG chatbot
* Generates:

  * Context-aware retention strategies

---

### 🔹 6.5 Chatbot Module 🤖

* Interactive UI component

* Accepts user queries like:

  > “How to retain this customer?”

* Uses:

  * Model prediction
  * SHAP insights

* Returns:

  * Step-by-step retention plan

---

### 🔹 6.6 Batch Prediction Module

* Upload CSV file

* Columns:

  * tenure
  * monthlyCharges

* Outputs:

  * Prediction per customer
  * Risk classification

---

## 🗂️ 7. Project Structure

```id="structure123"
project/
│
├── backend/
│   ├── app.py                 # Main API
│   ├── rag_helper.py          # RAG logic
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
│   │   ├── services/
│   │   └── App.js
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🛠️ 8. Tech Stack

| Layer          | Technology             |
| -------------- | ---------------------- |
| Frontend       | React.js, Tailwind CSS |
| Backend        | FastAPI                |
| ML             | Scikit-learn           |
| Explainability | SHAP                   |
| NLP            | Groq LLM               |
| RAG            | Sentence Transformers  |
| Data           | Pandas, NumPy          |

---

## 🚀 9. How to Run

### Backend

```bash id="run1"
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

---

### Frontend

```bash id="run2"
cd frontend
npm install
npm start
```

---

## 🔐 10. Environment Setup

```bash id="env1"
export GROQ_API_KEY=your_api_key_here
```

---

## 📊 11. Sample Input & Output

### Input:

```json id="sample1"
{
  "tenure": 12,
  "monthlyCharges": 50
}
```

### Output:

```json id="sample2"
{
  "churn_probability": 0.35,
  "prediction": "No Churn",
  "risk_level": "Low",
  "reasons": [...],
  "retention_recommendations": {...}
}
```

---

## 💡 12. Key Contributions

* Integration of ML + NLP + RAG in one system
* Explainable predictions using SHAP
* Real-time API with UI
* Chatbot-driven decision support
* Batch processing capability

---

## ⚠️ 13. Limitations

* Depends on dataset quality
* LLM responses may vary
* Requires API key for NLP features

---

## 🔮 14. Future Enhancements

* Deployment (cloud-based)
* Real-time monitoring dashboard
* CRM integration
* Deep learning models
* Multilingual chatbot

---

## 👩‍💻 15. Team

* D. Shivarani
* Team Members

Department: Computer Science Engineering

---

## 📄 16. Conclusion

ChurnGuard AI transforms traditional churn prediction into a **complete intelligent decision system**.

It not only predicts churn but also:

✔ Explains reasons
✔ Suggests actions
✔ Assists business decisions

---

⭐ *This project demonstrates real-world application of AI in business analytics.*




