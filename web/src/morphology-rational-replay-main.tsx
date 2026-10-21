import { createRoot } from 'react-dom/client';
import MorphologyReplayPage from './MorphologyReplayPage';
import { RATIONAL_MORPHOLOGY_SOURCE } from './morphologyReplay';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');if(!root)throw Error('Rational morphology replay root unavailable');
createRoot(root).render(<MorphologyReplayPage source={RATIONAL_MORPHOLOGY_SOURCE}/>);
