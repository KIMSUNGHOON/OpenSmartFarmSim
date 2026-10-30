import {createRoot} from 'react-dom/client';
import SupplyMorphologyReplayPage from './SupplyMorphologyReplayPage';
import '@fontsource-variable/noto-sans-kr';
const root=document.getElementById('root');if(!root)throw Error('Supply replay root unavailable');
createRoot(root).render(<SupplyMorphologyReplayPage/>);
