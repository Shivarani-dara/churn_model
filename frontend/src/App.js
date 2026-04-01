import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import Form from './components/Form';
import ResultCard from './components/ResultCard';
import TextPredict from './components/TextPredict';
import BulkUpload from './components/BulkUpload';
import Footer from './components/Footer';

function App() {
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const saved = localStorage.getItem('churnHistory');
    if (saved) setHistory(JSON.parse(saved));
  }, []);

  const addToHistory = (predictionData) => {
    const newEntry = {
      ...predictionData,
      timestamp: new Date().toLocaleString(),
    };
    const newHistory = [newEntry, ...history].slice(0, 5);
    setHistory(newHistory);
    localStorage.setItem('churnHistory', JSON.stringify(newHistory));
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <Header />
      <Hero />

      <main className="max-w-6xl mx-auto px-4 py-12 space-y-16">
        <section id="predict" className="space-y-8">
          <div className="grid lg:grid-cols-2 gap-10 items-stretch">
            <Form setResult={setResult} onPrediction={addToHistory} />

            <div>
              {result ? (
                <ResultCard data={result} />
              ) : (
                <div className="bg-[#0d0d14] rounded-2xl border border-[#1e1e2e] p-8 h-full flex items-center justify-center text-gray-500">
                  <p>Your prediction will appear here</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-[#0d0d14] border border-[#1e1e2e] rounded-2xl p-6">
            <TextPredict setResult={setResult} onPrediction={addToHistory} />
          </div>

          <div className="bg-[#0d0d14] border border-[#1e1e2e] rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">
              Bulk Customer Analysis
            </h2>
            <BulkUpload />
          </div>
        </section>

        {history.length > 0 && (
          <section id="history">
            <h2 className="font-syne text-2xl font-bold text-white mb-6">
              Recent Predictions
            </h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {history.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-[#0d0d14] border border-[#1e1e2e] rounded-xl p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`font-semibold ${
                        item.prediction === 'Churn'
                          ? 'text-red-400'
                          : 'text-green-400'
                      }`}
                    >
                      {item.prediction === 'Churn' ? '⚠️ Churn' : '✅ Loyal'}
                    </span>
                    <span className="text-xs text-gray-500">{item.timestamp}</span>
                  </div>
                  <p className="text-sm text-gray-400">
                    Prob: {(item.churn_probability * 100).toFixed(1)}%
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section
          id="about"
          className="bg-[#0d0d14] rounded-2xl border border-[#1e1e2e] p-8"
        >
          <h2 className="font-syne text-2xl font-bold text-white mb-4">
            About ChurnGuard AI
          </h2>
          <p className="text-gray-400 leading-relaxed">
            ChurnGuard AI uses machine learning to predict customer churn based
            on tenure, monthly charges, natural language descriptions, and bulk
            customer uploads. Our model provides explainable insights to help
            businesses take proactive measures to retain customers.
          </p>
        </section>
      </main>

      <Footer />
    </div>
  );
}

export default App;