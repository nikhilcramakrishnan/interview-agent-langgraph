import React from 'react';
import ReactDOM from 'react-dom/client'; // For React 18+
import './index.css'; // 
import App from './App';

const container = document.getElementById('root'); //
const root = ReactDOM.createRoot(container); 

root.render( 
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

