import React from "react";
import Graph from "./Graph";
import Explanation from "./Explanation";
import RetentionChat from "./RetentionChat";

function ResultCard({ data }) {
  if (!data) return null;

  const isChurn = data.prediction === "Churn";

  return (
    <div className="bg-[#0d0d14] rounded-2xl border border-[#1e1e2e] overflow-hidden h-full">
      <div className="p-8">
        <div className="text-xs tracking-wider text-gray-500 mb-2">
          RISK ASSESSMENT
        </div>

        <div className="flex items-center gap-3 mb-2 flex-wrap">
          <h2
            className={`font-syne text-4xl font-bold ${
              isChurn ? "text-red-400" : "text-green-400"
            }`}
          >
            {isChurn ? "HIGH RISK" : "LOYAL"}
          </h2>

          <span
            className={`px-3 py-1 rounded-full text-xs font-medium border ${
              isChurn
                ? "bg-red-500/20 text-red-400 border-red-500/30"
                : "bg-green-500/20 text-green-400 border-green-500/30"
            }`}
          >
            {data.prediction}
          </span>
        </div>

        <div className="text-sm text-gray-400 mb-2">
          Churn probability:{" "}
          <span className="text-white font-medium">
            {(Number(data.churn_probability || 0) * 100).toFixed(1)}%
          </span>
        </div>

        <div className="text-sm text-gray-400 mb-6">
          Risk level:{" "}
          <span className="text-white font-medium">
            {data.risk_level || "N/A"}
          </span>
        </div>

        <Graph
          reasons={data.reasons || []}
          retentionRecommendations={data.retention_recommendations || {}}
        />

        <Explanation text={data.explanation || "No explanation available."} />

        <RetentionChat
          response={data.chatbot_retention_response || ""}
          predictionData={data}
        />
      </div>
    </div>
  );
}

export default ResultCard;