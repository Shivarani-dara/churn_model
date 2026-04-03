import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

function RetentionChat({ response, predictionData = {} }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (response && response.trim()) {
      setMessages([{ text: response, sender: "ai" }]);
    } else {
      setMessages([]);
    }
    setInput("");
    setIsTyping(false);
  }, [response, predictionData]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const sendMessage = async (messageText = input) => {
    const trimmedMessage = messageText.trim();
    if (!trimmedMessage) return;

    const userMsg = { text: trimmedMessage, sender: "user" };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await axios.post("http://127.0.0.1:8000/chat_retention", {
        user_message: trimmedMessage,
        prediction_data: predictionData,
      });

      const aiReply =
        res?.data?.reply && String(res.data.reply).trim()
          ? res.data.reply
          : "No response generated.";

      setMessages((prev) => [...prev, { text: aiReply, sender: "ai" }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          text:
            err?.response?.data?.error ||
            "Failed to get chatbot response.",
          sender: "ai",
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickAction = (text) => {
    sendMessage(text);
  };

  if (!response && messages.length === 0) return null;

  return (
    <div className="mt-6 bg-[#111827] border border-[#1e1e2e] rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-4 border-b border-[#1e1e2e] bg-[#0f172a]">
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 flex items-center justify-center">
          <span className="text-white text-sm">🤖</span>
        </div>
        <div>
          <h3 className="font-semibold text-purple-400">
            AI Retention Assistant
          </h3>
          <p className="text-xs text-gray-500">Ask follow-up questions</p>
        </div>
      </div>

      <div className="p-4 max-h-80 overflow-y-auto space-y-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.sender === "ai" ? "justify-start" : "justify-end"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                msg.sender === "ai"
                  ? "bg-[#1e293b] text-gray-200 rounded-tl-none"
                  : "bg-purple-600 text-white rounded-tr-none"
              }`}
            >
              {String(msg.text)
                .split("\n")
                .map((line, i) => (
                  <p key={i} className="whitespace-pre-line">
                    {line}
                  </p>
                ))}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-[#1e293b] rounded-2xl rounded-tl-none px-4 py-2 text-sm text-gray-300">
              <span className="animate-pulse">✍️</span> Typing...
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <div className="px-4 pb-3 flex flex-wrap gap-2">
        <button
          onClick={() =>
            handleQuickAction("What are the top 3 retention steps for this customer?")
          }
          className="text-xs bg-[#2d3748] hover:bg-[#4a5568] text-gray-300 px-3 py-1 rounded-full transition"
        >
          Top retention steps
        </button>

        <button
          onClick={() =>
            handleQuickAction("What should we do first to reduce churn risk?")
          }
          className="text-xs bg-[#2d3748] hover:bg-[#4a5568] text-gray-300 px-3 py-1 rounded-full transition"
        >
          What to do first?
        </button>

        <button
          onClick={() =>
            handleQuickAction("How can pricing be improved for this customer?")
          }
          className="text-xs bg-[#2d3748] hover:bg-[#4a5568] text-gray-300 px-3 py-1 rounded-full transition"
        >
          Pricing advice
        </button>
      </div>

      <div className="p-4 border-t border-[#1e1e2e] flex gap-2 bg-[#0f172a]">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") sendMessage();
          }}
          placeholder="Ask about retention strategies..."
          className="flex-1 bg-[#111118] border border-[#2a2a3e] rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#7c5cfc]"
        />
        <button
          onClick={() => sendMessage()}
          className="bg-[#7c5cfc] text-white px-4 py-2 rounded-lg hover:opacity-90 transition"
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default RetentionChat;