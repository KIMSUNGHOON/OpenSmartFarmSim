import {createRoot} from 'react-dom/client';
import LeafAppearanceExecutionPage from './LeafAppearanceExecutionPage';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');if(!root)throw Error('Leaf execution root unavailable');
createRoot(root).render(<LeafAppearanceExecutionPage/>);
