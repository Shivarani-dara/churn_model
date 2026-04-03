import React, { useState } from "react";
import axios from "axios";

function Form({ setResult, onPrediction }) {
  const [formData, setFormData] = useState({
    tenure: "",
    monthlyCharges: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const tenure = Number(formData.tenure);
    const monthlyCharges = Number(formData.monthlyCharges);

    if (Number.isNaN(tenure) || tenure <= 0) {
      setError("Tenure must be a positive number.");
      return;
    }

    if (Number.isNaN(monthlyCharges) || monthlyCharges <= 0) {
      setError("Monthly charges must be a positive number.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const payload = {
        tenure,
        monthlyCharges,
      };

      const res = await axios.post("http://127.0.0.1:8000/predict", payload);

      console.log("Single prediction response:", res.data);

      if (res.data?.error) {
        throw new Error(res.data.error);
      }

      setResult(res.data);

      if (onPrediction) {
        onPrediction(res.data);
      }
    } catch (err) {
      setError(
        err?.response?.data?.error ||
          err?.message ||
          "Backend error. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#0d0d14] rounded-2xl border border-[#1e1e2e] overflow-hidden h-full">
      <div className="p-8">
        <div className="text-xs tracking-wider text-[#7c5cfc] mb-2">
          CUSTOMER INTELLIGENCE
        </div>

        <h2 className="font-syne text-3xl font-bold text-white mb-2">
          Predict Churn
          <br />
          Before It Happens
        </h2>

        <p className="text-sm text-gray-500 mb-6">
          Enter customer data to get an AI-powered churn risk score with
          explainable factors.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">
              Tenure (months)
            </label>
            <input
              type="number"
              name="tenure"
              value={formData.tenure}
              onChange={handleChange}
              placeholder="e.g., 12"
              min="1"
              step="1"
              className="w-full bg-[#111118] border border-[#2a2a3e] rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#7c5cfc]"
            />
          </div>

          <div className="mb-6">
            <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">
              Monthly Charges ($)
            </label>
            <input
              type="number"
              name="monthlyCharges"
              value={formData.monthlyCharges}
              onChange={handleChange}
              placeholder="e.g., 59.99"
              min="0.01"
              step="0.01"
              className="w-full bg-[#111118] border border-[#2a2a3e] rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#7c5cfc]"
            />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-[#7c5cfc] to-[#5b3dd6] text-white font-semibold py-3 rounded-lg hover:opacity-90 transition disabled:opacity-50"
          >
            {loading ? "Analysing..." : "Run Analysis →"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Form;