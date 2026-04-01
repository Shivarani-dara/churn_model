import React, { useState } from "react";
import Papa from "papaparse";
import axios from "axios";

function BulkUpload() {
  const [fileName, setFileName] = useState("");
  const [rows, setRows] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setError("");
    setResults([]);
    setRows([]);

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (parsed) => {
        const cleaned = parsed.data.map((row) => ({
          tenure: Number(row.tenure),
          monthlyCharges: Number(row.monthlyCharges),
        }));
        setRows(cleaned);
      },
      error: () => setError("Failed to parse CSV file."),
    });
  };

  const handleBatchPredict = async () => {
    if (!rows.length) {
      setError("Please upload a valid CSV file first.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await axios.post("http://127.0.0.1:8000/predict/batch", {
        data: rows,
      });

      setResults(response.data.results || []);
    } catch (err) {
      setError(err.response?.data?.error || "Batch prediction failed.");
    } finally {
      setLoading(false);
    }
  };

  const successCount = results.filter((r) => r.prediction !== "Churn").length;
  const churnCount = results.length - successCount;

  return (
    <div>
      <p className="text-gray-400 text-sm mb-4">
        Upload a CSV file with columns: <span className="text-white">tenure</span> and{" "}
        <span className="text-white">monthlyCharges</span>
      </p>

      <input
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-300 mb-4 cursor-pointer"
      />

      {fileName && (
        <p className="text-sm text-gray-400 mb-3">
          Uploaded: <span className="text-white">{fileName}</span>{" "}
          {rows.length > 0 && `(${rows.length} rows ready)`}
        </p>
      )}

      <button
        onClick={handleBatchPredict}
        disabled={loading || !rows.length}
        className="bg-[#7c5cfc] text-white px-5 py-2 rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Predicting..." : "Run Batch Prediction"}
      </button>

      {error && <p className="text-red-400 text-sm mt-4">{error}</p>}

      {results.length > 0 && (
        <>
          <div className="mt-4 flex gap-4 text-sm">
            <span className="text-green-400">✅ Loyal: {successCount}</span>
            <span className="text-red-400">⚠️ Churn: {churnCount}</span>
          </div>
          <div className="mt-6 overflow-x-auto rounded-xl border border-[#1e1e2e]">
            <table className="w-full text-sm text-left">
              <thead className="bg-[#111118] text-gray-400 uppercase text-xs">
                <tr>
                  <th className="px-4 py-3">Tenure</th>
                  <th className="px-4 py-3">Monthly</th>
                  <th className="px-4 py-3">Prediction</th>
                  <th className="px-4 py-3">Probability</th>
                  <th className="px-4 py-3">Risk</th>
                </tr>
              </thead>
              <tbody>
                {results.map((item, idx) => (
                  <tr key={idx} className="border-t border-[#1e1e2e] hover:bg-[#151522] transition">
                    <td className="px-4 py-3">{item.tenure}</td>
                    <td className="px-4 py-3">{item.MonthlyCharges}</td>
                    <td
                      className={`px-4 py-3 font-semibold ${
                        item.prediction === "Churn" ? "text-red-400" : "text-green-400"
                      }`}
                    >
                      {item.prediction}
                    </td>
                    <td className="px-4 py-3">{(item.churn_probability * 100).toFixed(1)}%</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded text-xs ${
                          item.risk_level === "High"
                            ? "bg-red-500/20 text-red-400"
                            : item.risk_level === "Medium"
                            ? "bg-yellow-500/20 text-yellow-400"
                            : "bg-green-500/20 text-green-400"
                        }`}
                      >
                        {item.risk_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

export default BulkUpload;