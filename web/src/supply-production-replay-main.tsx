import {createRoot} from 'react-dom/client';
import SupplyProductionReplayPage from './SupplyProductionReplayPage';
import '@fontsource-variable/noto-sans-kr';
const root=document.getElementById('root');if(!root)throw Error('Supply replay root unavailable');
createRoot(root).render(<SupplyProductionReplayPage/>);
