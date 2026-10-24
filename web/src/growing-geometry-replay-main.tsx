import {createRoot} from 'react-dom/client';
import GrowingGeometryReplayPage from './GrowingGeometryReplayPage';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');if(!root)throw Error('Growing geometry replay root unavailable');
createRoot(root).render(<GrowingGeometryReplayPage/>);
