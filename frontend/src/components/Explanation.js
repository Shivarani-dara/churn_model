import React from "react";

function Explanation({ text }) {
  if (!text) return null;
  return (
    <div className="bg-[#12121a] p-4 rounded-lg text-gray-400 text-sm">
      {text}
    </div>
  );
}

export default Explanation;