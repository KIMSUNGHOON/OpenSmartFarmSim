import { createRoot } from 'react-dom/client';
import MorphologyReplayPage from './MorphologyReplayPage';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');if(!root)throw Error('Morphology replay root unavailable');
createRoot(root).render(<MorphologyReplayPage/>);
