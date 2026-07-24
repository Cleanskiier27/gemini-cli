import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

const rootElement = document.getElementById('app');

if (!rootElement) {
  throw new Error('App root element not found');
}

createRoot(rootElement).render(
  React.createElement(React.StrictMode, null,
    React.createElement(App, null)
  )
);
