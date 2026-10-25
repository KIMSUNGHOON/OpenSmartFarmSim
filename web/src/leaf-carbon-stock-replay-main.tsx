import {createRoot} from 'react-dom/client';
import LeafCarbonStockReplayPage from './LeafCarbonStockReplayPage';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');if(!root)throw Error('Leaf carbon stock replay root unavailable');
createRoot(root).render(<LeafCarbonStockReplayPage/>);
