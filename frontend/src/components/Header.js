import React from 'react';

const Header = () => {
  const scrollTo = (id) => {
    const element = document.getElementById(id);
    if (element) element.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <header className="sticky top-0 z-50 bg-[#0d0d14]/90 backdrop-blur-md border-b border-[#1e1e2e]">
      <div className="container mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#7c5cfc]" />
          <span className="font-syne font-extrabold text-xl text-[#c8b8ff]">ChurnGuard AI</span>
        </div>
        <nav className="flex gap-6">
          <button onClick={() => scrollTo('predict')} className="text-sm text-gray-400 hover:text-[#c8b8ff] transition uppercase tracking-wider">Predict</button>
          <button onClick={() => scrollTo('history')} className="text-sm text-gray-400 hover:text-[#c8b8ff] transition uppercase tracking-wider">History</button>
          <button onClick={() => scrollTo('about')} className="text-sm text-gray-400 hover:text-[#c8b8ff] transition uppercase tracking-wider">About</button>
        </nav>
      </div>
    </header>
  );
};

export default Header;