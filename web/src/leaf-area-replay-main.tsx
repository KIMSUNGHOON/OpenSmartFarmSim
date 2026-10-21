import { createRoot } from 'react-dom/client';
import LeafAreaReplayPage from './LeafAreaReplayPage';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');if(!root)throw Error('Leaf area replay root unavailable');
createRoot(root).render(<LeafAreaReplayPage/>);
