import { createRoot } from 'react-dom/client';
import App from './App';
import '@fontsource-variable/noto-sans-kr';
import './App.css';

const root=document.getElementById('root');
if (!root) throw new Error('Application root unavailable');
createRoot(root).render(<App />);
