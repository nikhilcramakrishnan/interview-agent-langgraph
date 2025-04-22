// src/App.js
import React, { useContext } from 'react';
import { InterviewProvider, InterviewContext } from './context/InterviewContext';
import StartForm from './components/StartForm';
import Interview from './components/Interview';

function MainApp() {
  const { sessionId, interviewData } = useContext(InterviewContext);

  return sessionId && interviewData ? <Interview /> : <StartForm />;
}

function App() {
  return (
    <InterviewProvider>
      <MainApp />
    </InterviewProvider>
  );
}

export default App;
