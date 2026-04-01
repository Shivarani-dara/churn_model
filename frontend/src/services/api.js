import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export const predictChurn = async (formData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/predict`, formData);
    return response.data;
  } catch (error) {
    console.error("API error:", error);
    throw error;
  }
};