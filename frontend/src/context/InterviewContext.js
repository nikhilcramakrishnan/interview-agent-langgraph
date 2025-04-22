import React, { createContext, useContext, useState, useEffect } from 'react';
import { data } from 'react-router-dom';

export const InterviewContext = createContext();

export const InterviewProvider = ({ children }) => {
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('sessionId') || null);
  const [interviewData, setInterviewData] = useState(() => {
    const saved = localStorage.getItem('interviewData');
    return saved ? JSON.parse(saved) : null;
  });

  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('sessionId', sessionId);
    }
  }, [sessionId]);


const updateInterviewData = (data) =>{
  setInterviewData(data)
}
  const clearSession = () => {
    setSessionId(null);
    setInterviewData(null);
    localStorage.removeItem('sessionId');
    localStorage.removeItem('interviewData');
  };

  return (
    <InterviewContext.Provider
      value={{
        sessionId,
        setSessionId,
        interviewData,
        setInterviewData,
        clearSession,
        updateInterviewData
      }}
    >
      {children}
    </InterviewContext.Provider>
  );
};

// ✅ Add this hook:
export const useInterview = () => {
  const context = useContext(InterviewContext);
  if (!context) {
    throw new Error("useInterview must be used within an InterviewProvider");
  }
  return context;
};
