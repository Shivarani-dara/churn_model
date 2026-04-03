import React from "react";
import { Bar, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Title,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Title
);

function BulkCharts({ chartData }) {
  if (!chartData) {
    return (
      <div className="bg-[#11111a] border border-[#1e1e2e] rounded-2xl p-5 text-gray-400">
        No bulk chart data available.
      </div>
    );
  }

  const predictionDistribution = chartData.prediction_distribution || {};
  const riskDistribution = chartData.risk_distribution || {};
  const topReasons = chartData.top_reasons || {};
  const topRiskyCustomers = chartData.top_risky_customers || [];
  const retentionActions = chartData.retention_actions || {};
  const avgChurnProbability = chartData.average_churn_probability || 0;

  const predictionLabels = Object.keys(predictionDistribution);
  const predictionValues = Object.values(predictionDistribution);

  const riskLabels = Object.keys(riskDistribution);
  const riskValues = Object.values(riskDistribution);

  const reasonLabels = Object.keys(topReasons);
  const reasonValues = Object.values(topReasons);

  const riskyCustomerLabels = topRiskyCustomers.map(
    (item) => item.customer_id || "Unknown"
  );
  const riskyCustomerValues = topRiskyCustomers.map(
    (item) => Number(item.churn_probability || 0)
  );

  const retentionLabels = Object.keys(retentionActions);
  const retentionValues = Object.values(retentionActions);

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: "#e5e7eb",
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            return `${context.label}: ${context.raw}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: "#cbd5e1" },
        grid: { color: "rgba(255,255,255,0.08)" },
      },
      y: {
        beginAtZero: true,
        ticks: { color: "#cbd5e1" },
        grid: { color: "rgba(255,255,255,0.08)" },
      },
    },
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: "#e5e7eb",
        },
      },
    },
  };

  const predictionPieData = {
    labels: predictionLabels,
    datasets: [
      {
        label: "Prediction Distribution",
        data: predictionValues,
        backgroundColor: [
          "rgba(255, 99, 132, 0.7)",
          "rgba(75, 192, 192, 0.7)",
          "rgba(255, 206, 86, 0.7)",
          "rgba(153, 102, 255, 0.7)",
        ],
        borderWidth: 1,
      },
    ],
  };

  const riskBarData = {
    labels: riskLabels,
    datasets: [
      {
        label: "Risk Distribution",
        data: riskValues,
        backgroundColor: [
          "rgba(255, 99, 132, 0.7)",
          "rgba(255, 206, 86, 0.7)",
          "rgba(75, 192, 192, 0.7)",
        ],
        borderRadius: 6,
      },
    ],
  };

  const reasonsBarData = {
    labels: reasonLabels,
    datasets: [
      {
        label: "Top Churn Drivers",
        data: reasonValues,
        backgroundColor: "rgba(54, 162, 235, 0.7)",
        borderRadius: 6,
      },
    ],
  };

  const riskyCustomersBarData = {
    labels: riskyCustomerLabels,
    datasets: [
      {
        label: "Top Risky Customers (%)",
        data: riskyCustomerValues,
        backgroundColor: "rgba(255, 99, 132, 0.7)",
        borderRadius: 6,
      },
    ],
  };

  const retentionBarData = {
    labels: retentionLabels,
    datasets: [
      {
        label: "Retention Actions",
        data: retentionValues,
        backgroundColor: "rgba(153, 102, 255, 0.7)",
        borderRadius: 6,
      },
    ],
  };

  return (
    <div className="space-y-6 mt-6">
      <div className="bg-[#11111a] border border-[#1e1e2e] rounded-2xl p-5">
        <h3 className="text-lg font-semibold text-white mb-2">
          Average Churn Probability
        </h3>
        <p className="text-3xl font-bold text-red-400">
          {Number(avgChurnProbability).toFixed(2)}%
        </p>
      </div>

      {predictionLabels.length > 0 && (
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="bg-[#11111a] border border-[#1e1e2e] rounded-2xl p-5">
            <h3 className="text-lg font-semibold text-white mb-4">
              Prediction Distribution
            </h3>
            <div className="h-[320px]">
              <Pie data={predictionPieData} options={pieOptions} />
            </div>
          </div>

          <div className="bg-[#11111a] border border-[#1e1e2e] rounded-2xl p-5">
            <h3 className="text-lg font-semibold text-white mb-4">
              Risk Distribution
            </h3>
            <div className="h-[320px]">
              <Bar data={riskBarData} options={commonOptions} />
            </div>
          </div>
        </div>
      )}

      {reasonLabels.length > 0 && (
        <div className="bg-[#11111a] border border-[#1e1e2e] rounded-2xl p-5">
          <h3 className="text-lg font-semibold text-white mb-4">
            Top Churn Drivers
          </h3>
          <div className="h-[360px]">
            <Bar data={reasonsBarData} options={commonOptions} />
          </div>
        </div>
      )}

      {retentionLabels.length > 0 && (
        <div className="bg-[#11111a] border border-[#1e1e2e] rounded-2xl p-5">
          <h3 className="text-lg font-semibold text-white mb-4">
            Suggested Retention Actions
          </h3>
          <div className="h-[360px]">
            <Bar data={retentionBarData} options={commonOptions} />
          </div>
        </div>
      )}

      {riskyCustomerLabels.length > 0 && (
        <div className="bg-[#11111a] border border-[#1e1e2e] rounded-2xl p-5">
          <h3 className="text-lg font-semibold text-white mb-4">
            Top Risky Customers
          </h3>
          <div className="h-[360px]">
            <Bar data={riskyCustomersBarData} options={commonOptions} />
          </div>
        </div>
      )}
    </div>
  );
}

export default BulkCharts;