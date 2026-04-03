import React, { useState } from "react";
import BulkCharts from "./BulkCharts";

function BulkUpload() {
  const [file, setFile] = useState(null);
  const [bulkResult, setBulkResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    setBulkResult(null);
    setError("");
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a CSV file.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    setBulkResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://127.0.0.1:8000/predict/upload-csv", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      console.log("Bulk API response:", data);

      if (!response.ok || data.error) {
        throw new Error(data.error || "CSV prediction failed.");
      }

      setBulkResult(data);
      setMessage("Bulk analysis completed successfully.");
    } catch (err) {
      setError(err.message || "Something went wrong while uploading CSV.");
    } finally {
      setLoading(false);
    }
  };

  const handleSendSingleEmail = async (customer) => {
    try {
      const response = await fetch("http://127.0.0.1:8000/send-offer-email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          customer_id: customer.customer_id,
          email: customer.email,
          email_message: customer.email_message,
        }),
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        throw new Error(data.error || "Failed to send email");
      }

      alert(`Email sent to ${customer.email}`);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSendHighRiskEmails = async () => {
    try {
      setEmailLoading(true);
      setError("");
      setMessage("");

      const response = await fetch(
        "http://127.0.0.1:8000/send-high-risk-emails?limit=10",
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok || data.error) {
        throw new Error(data.error || "Failed to send high-risk emails");
      }

      setMessage(`Bulk email process complete. Sent: ${data.sent_count}`);
    } catch (err) {
      setError(err.message || "Failed to send emails.");
    } finally {
      setEmailLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-4 md:items-center">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-300
                     file:mr-4 file:py-2 file:px-4
                     file:rounded-lg file:border-0
                     file:text-sm file:font-semibold
                     file:bg-blue-600 file:text-white
                     hover:file:bg-blue-700"
        />

        <button
          onClick={handleUpload}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg bg-green-600 hover:bg-green-700 text-white font-medium disabled:opacity-50"
        >
          {loading ? "Uploading..." : "Upload & Analyze"}
        </button>

        <button
          onClick={handleSendHighRiskEmails}
          disabled={emailLoading}
          className="px-5 py-2.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-medium disabled:opacity-50"
        >
          {emailLoading ? "Sending..." : "Send Emails to Top High-Risk"}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 p-4 rounded-xl">
          {error}
        </div>
      )}

      {message && (
        <div className="bg-green-500/10 border border-green-500/30 text-green-300 p-4 rounded-xl">
          {message}
        </div>
      )}

      {bulkResult && (
        <div className="space-y-6">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[#11111a] border border-[#1e1e2e] rounded-xl p-4">
              <p className="text-sm text-gray-400">Total Customers</p>
              <p className="text-2xl font-bold text-white">
                {bulkResult.total_customers}
              </p>
            </div>

            <div className="bg-[#11111a] border border-[#1e1e2e] rounded-xl p-4">
              <p className="text-sm text-gray-400">High Risk</p>
              <p className="text-2xl font-bold text-red-400">
                {bulkResult.high_risk_count}
              </p>
            </div>

            <div className="bg-[#11111a] border border-[#1e1e2e] rounded-xl p-4">
              <p className="text-sm text-gray-400">Medium Risk</p>
              <p className="text-2xl font-bold text-yellow-400">
                {bulkResult.medium_risk_count}
              </p>
            </div>

            <div className="bg-[#11111a] border border-[#1e1e2e] rounded-xl p-4">
              <p className="text-sm text-gray-400">Low Risk</p>
              <p className="text-2xl font-bold text-green-400">
                {bulkResult.low_risk_count}
              </p>
            </div>
          </div>

          <BulkCharts chartData={bulkResult.chart_data} />

          <div className="bg-[#11111a] border border-[#1e1e2e] rounded-2xl p-5 overflow-x-auto">
            <h3 className="text-lg font-semibold text-white mb-4">
              Bulk Prediction Results
            </h3>

            <table className="w-full text-sm text-left text-gray-300">
              <thead className="text-xs uppercase bg-[#181824] text-gray-400">
                <tr>
                  <th className="px-4 py-3">Customer</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Prediction</th>
                  <th className="px-4 py-3">Risk</th>
                  <th className="px-4 py-3">Probability</th>
                  <th className="px-4 py-3">Top Reason</th>
                  <th className="px-4 py-3">Suggested Offer</th>
                  <th className="px-4 py-3">Action</th>
                </tr>
              </thead>

              <tbody>
                {bulkResult.results?.map((item, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-[#232334] hover:bg-[#151520]"
                  >
                    <td className="px-4 py-3">
                      {item.customer_id || `Customer ${idx + 1}`}
                    </td>
                    <td className="px-4 py-3">{item.email || "N/A"}</td>
                    <td
                      className={`px-4 py-3 font-semibold ${
                        item.prediction === "Churn"
                          ? "text-red-400"
                          : "text-green-400"
                      }`}
                    >
                      {item.prediction}
                    </td>
                    <td className="px-4 py-3">{item.risk_level}</td>
                    <td className="px-4 py-3">
                      {(Number(item.churn_probability || 0) * 100).toFixed(2)}%
                    </td>
                    <td className="px-4 py-3">{item.top_reason_1 || "N/A"}</td>
                    <td className="px-4 py-3 text-cyan-300">
                      {item.suggested_offer || "—"}
                    </td>
                    <td className="px-4 py-3">
                      {item.risk_level === "High" &&
                      item.email &&
                      item.email_message ? (
                        <button
                          onClick={() => handleSendSingleEmail(item)}
                          className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          Send Email
                        </button>
                      ) : (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default BulkUpload;