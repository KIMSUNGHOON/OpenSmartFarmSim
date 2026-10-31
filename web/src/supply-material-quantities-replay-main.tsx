import {createRoot} from 'react-dom/client';
import SupplyMaterialQuantitiesPage from './SupplyMaterialQuantitiesPage';
import '@fontsource-variable/noto-sans-kr';
const root=document.getElementById('root');if(!root)throw Error('Supply replay root unavailable');
createRoot(root).render(<SupplyMaterialQuantitiesPage/>);
