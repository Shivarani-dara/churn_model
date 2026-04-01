import React from "react";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

function Graph({ reasons = [], retentionRecommendations = {} }) {
  if (!reasons.length) {
    return (
      <div className="bg-[#1a1a26] rounded-xl p-4 text-center text-gray-500 text-sm">
        No feature impact data available.
      </div>
    );
  }

  const labels = reasons.map((r) => r.feature);
  const impacts = reasons.map((r) => parseFloat((r.impact * 100).toFixed(2)));

  const data = {
    labels,
    datasets: [
      {
        label: "Impact on Churn (%)",
        data: impacts,
        backgroundColor: impacts.map((v) => (v > 0 ? "rgba(255,99,132,0.7)" : "rgba(75,192,192,0.7)")),
        borderRadius: 5,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      tooltip: {
        callbacks: {
          label: function (context) {
            const feature = context.label;
            const impact = context.raw;
            const retention = retentionRecommendations?.[feature]?.retention_action || "No suggestion";
            return [`Impact: ${impact}%`, `Retention: ${retention}`];
          },
        },
      },
      legend: { display: false },
    },
    scales: {
      y: { beginAtZero: true, title: { display: true, text: "Impact on churn (%)" } },
      x: { title: { display: true, text: "Features" } },
    },
  };

  return (
    <div className="bg-[#1a1a26] rounded-xl p-4 mb-6">
      <Bar data={data} options={options} />
    </div>
  );
}

export default Graph;