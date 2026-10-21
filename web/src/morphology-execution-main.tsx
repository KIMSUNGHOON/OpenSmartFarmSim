import { createRoot } from 'react-dom/client';
import MorphologyExecutionPage from './MorphologyExecutionPage';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');if(!root)throw Error('Morphology execution root unavailable');
createRoot(root).render(<MorphologyExecutionPage/>);
