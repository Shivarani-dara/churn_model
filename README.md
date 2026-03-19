# 🧠 Customer Intelligence System
### Customer Segmentation & Churn Prediction

![Python](https://img.shields.io/badge/Python-3.10-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green) ![Scikit-learn](https://img.shields.io/badge/Scikit--learn-latest-orange) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Overview

The **Customer Intelligence System** is a Machine Learning project that helps businesses identify customers who are likely to **stop using their service (churn)**. It uses unsupervised learning to **segment customers into groups** and supervised learning to **predict churn probability** for each customer.

Originally built for a **Telecom company** dataset, this system is designed to work across any customer-facing industry — e-commerce, banking, ride-sharing, subscription services, and more.

---

## 🎯 Key Features

- **Customer Segmentation** using K-Means, Hierarchical, and DBSCAN clustering
- **Churn Prediction** using Logistic Regression, Random Forest, and Gradient Boosting
- **Model Explainability** using SHAP values — understand *why* a customer is predicted to churn
- **REST API** built with FastAPI for real-time predictions
- **Interactive API docs** via Swagger UI at `/docs`

---

## 🗂️ Project Structure

```
customer-intelligence/
│
├── Customer_Intelligence_System.ipynb   ← Full ML pipeline (training)
├── app.py                               ← FastAPI application
├── churn_model.pkl                      ← Trained model (generated after training)
├── feature_names.pkl                    ← Feature list (generated after training)
├── requirements.txt                     ← Python dependencies
├── Dockerfile                           ← Docker configuration
└── README.md                            ← You are here
```

---

## 📊 Dataset

**Telco Customer Churn** — IBM Sample Dataset

- **Source:** [Kaggle — Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
- **Size:** 7,043 customers × 21 features
- **Target:** `Churn` column (Yes/No → 1/0)

### Key Columns

| Column | Description |
|--------|-------------|
| `tenure` | Months the customer has been with the company |
| `MonthlyCharges` | Monthly bill amount |
| `TotalCharges` | Total amount paid |
| `Contract` | Contract type (Month-to-month / 1yr / 2yr) |
| `InternetService` | DSL / Fiber optic / None |
| `Churn` | **Target** — Did the customer leave? |

---

## ⚙️ How It Works

```
Raw Dataset
    ↓
Data Preprocessing (encoding, scaling, missing values)
    ↓
K-Means Clustering (segments customers into 3 groups)
    ↓
Add 'Segment' as a feature
    ↓
Train 3 Classification Models
    ↓
Compare & Select Best Model (Logistic Regression — ROC-AUC: 0.84)
    ↓
Deploy as FastAPI REST API
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip
- Git

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/yourusername/customer-intelligence.git
cd customer-intelligence
```

---

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

> If you're behind a proxy, set it first:
> ```bash
> pip install -r requirements.txt --proxy http://username:password@proxyip:port
> ```

---

### Step 3 — Download the Dataset

1. Go to [Kaggle — Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
2. Download `WA_Fn-UseC_-Telco-Customer-Churn.csv`
3. Place it in the **root of the project folder**

---

### Step 4 — Train the Model

Open `Customer_Intelligence_System.ipynb` in Jupyter Notebook and run all cells **top to bottom**.

```bash
jupyter notebook Customer_Intelligence_System.ipynb
```

This will:
- Preprocess the data
- Run 3 clustering algorithms and pick the best (K-Means)
- Train 3 classification models and compare them
- Save the best model as `churn_model.pkl`
- Save feature names as `feature_names.pkl`

---

### Step 5 — Start the API

```bash
uvicorn app:app --reload
```

The API will be running at: `http://127.0.0.1:8000`

---

### Step 6 — Test the API

Open your browser and go to:

```
http://127.0.0.1:8000/docs
```

This opens the **Swagger UI** where you can test predictions interactively.

#### Sample Request (POST `/predict`)

```json
{
  "gender": 1,
  "SeniorCitizen": 0,
  "Partner": 1,
  "Dependents": 0,
  "tenure": 5,
  "PhoneService": 1,
  "MultipleLines": 0,
  "InternetService": 1,
  "OnlineSecurity": 0,
  "OnlineBackup": 0,
  "DeviceProtection": 0,
  "TechSupport": 0,
  "StreamingTV": 0,
  "StreamingMovies": 0,
  "Contract": 0,
  "PaperlessBilling": 1,
  "PaymentMethod": 2,
  "MonthlyCharges": 85.0,
  "TotalCharges": 425.0,
  "Segment": 0
}
```

#### Sample Response

```json
{
  "churn_probability": 0.7294,
  "prediction": "Churn"
}
```

---

## 📈 Model Results

### Clustering Comparison

| Algorithm | Silhouette Score | Result |
|-----------|-----------------|--------|
| **K-Means** | **0.4514** | ✅ Best |
| Hierarchical | 0.3960 | OK |
| DBSCAN | N/A (1 cluster) | ❌ Failed |

### Classification Comparison

| Model | Accuracy | ROC-AUC |
|-------|----------|---------|
| **Logistic Regression** | **0.7991** | **0.8403** ✅ |
| Random Forest | 0.7921 | 0.8261 |
| Gradient Boosting | 0.7878 | 0.8257 |

> **ROC-AUC > 0.80 = Good model.** Logistic Regression was selected as the best model.

---

## 🔢 Feature Encoding Reference

When sending data to the API, use these encoded values:

| Feature | Values |
|---------|--------|
| `gender` | 0 = Female, 1 = Male |
| `SeniorCitizen` | 0 = No, 1 = Yes |
| `Partner` | 0 = No, 1 = Yes |
| `Dependents` | 0 = No, 1 = Yes |
| `PhoneService` | 0 = No, 1 = Yes |
| `MultipleLines` | 0 = No, 1 = Yes, 2 = No phone service |
| `InternetService` | 0 = DSL, 1 = Fiber optic, 2 = No |
| `Contract` | 0 = Month-to-month, 1 = One year, 2 = Two year |
| `PaymentMethod` | 0 = Bank transfer, 1 = Credit card, 2 = Electronic check, 3 = Mailed check |
| `Segment` | 0, 1, or 2 (from K-Means clustering) |

---

## 🐳 Docker (Optional)

```bash
# Build
docker build -t churn-api .

# Run
docker run -p 8000:8000 churn-api
```

Then open `http://127.0.0.1:8000/docs`

---

## 🌍 Adapting to Other Industries

This system works for **any industry** by swapping the dataset:

| Industry | Churn Definition |
|----------|-----------------|
| E-commerce | No purchase in 60 days |
| Ride-sharing | No ride in 30 days |
| Banking | Account closed / inactive |
| OTT/Streaming | Subscription cancelled |

Just replace the CSV dataset and redefine the `Churn` column accordingly.

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| Pandas, NumPy | Data processing |
| Scikit-learn | ML models & clustering |
| SHAP | Model explainability |
| FastAPI | REST API |
| Uvicorn | ASGI server |
| Joblib | Model serialization |
| Docker | Containerization |

---

## 👩‍💻 Team

| Name | Roll Number |
|------|------------|
| D. Shiva Rani | B211330 |
| S. Prathyusha | B211206 |
| Farzana | B211117 |

**Guide:** Mr. Sujoy Sarkar  
**Department:** Computer Science and Engineering

---

## 📄 License

This project is for academic purposes.
