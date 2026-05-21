import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import Root from './main.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
