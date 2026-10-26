import {createRoot} from 'react-dom/client';
import CompleteCropReplayPage from './CompleteCropReplayPage';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');if(!root)throw Error('Complete crop replay root unavailable');
createRoot(root).render(<CompleteCropReplayPage/>);
