import React, { useState } from "react";
import axios from "axios";

function TextPredict({ setResult, onPrediction }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post("http://127.0.0.1:8000/predict_text", { text });
      setResult(res.data);
      // Save to history if callback is provided
      if (onPrediction) onPrediction(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Error processing text");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-8 bg-[#0d0d14] rounded-2xl border border-[#1e1e2e] p-6">
      <h3 className="text-white font-semibold mb-2">Describe a customer in plain English</h3>
      <p className="text-gray-400 text-sm mb-3">
        Try: “A customer with 2 years tenure, paying $80 monthly, no online security, month-to-month contract”
      </p>
      <textarea
        rows={3}
        className="w-full bg-[#111118] border border-[#2a3a3e] rounded-lg p-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#7c5cfc]"
        placeholder="Describe the customer..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="mt-3 bg-[#7c5cfc] text-white px-5 py-2 rounded-lg hover:opacity-90 transition disabled:opacity-50"
      >
        {loading ? "Analyzing..." : "Predict from Text"}
      </button>
      {error && <div className="text-red-400 text-sm mt-3">{error}</div>}
    </div>
  );
}

export default TextPredict;