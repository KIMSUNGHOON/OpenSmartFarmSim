import {createRoot} from 'react-dom/client';
import LeafLifecycleReplayPage from './LeafLifecycleReplayPage';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');if(!root)throw Error('Leaf lifecycle replay root unavailable');
createRoot(root).render(<LeafLifecycleReplayPage/>);
