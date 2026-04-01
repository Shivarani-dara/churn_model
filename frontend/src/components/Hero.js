import React from 'react';

const Hero = () => {
  return (
    <section className="relative bg-gradient-to-r from-[#0a0a0f] via-[#1a1a2e] to-[#0a0a0f] py-20 overflow-hidden">
      {/* Simple overlay pattern (optional) */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(124,92,252,0.1),transparent_50%)]" />
      </div>
      <div className="container mx-auto px-4 text-center relative z-10">
        <h1 className="font-syne text-5xl md:text-6xl font-extrabold bg-gradient-to-r from-[#c8b8ff] to-[#7c5cfc] bg-clip-text text-transparent mb-4">
          Predict Customer Churn with AI
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto">
          Reduce churn, increase retention. Get instant insights on why customers leave and take action.
        </p>
      </div>
    </section>
  );
};

export default Hero;