import { createRoot } from 'react-dom/client';
import TomatoAppearanceScene from './TomatoAppearanceScene';
import '@fontsource-variable/noto-sans-kr';
import './TomatoAppearance.css';
import './TomatoAppearancePage.css';

const root=document.getElementById('root');
if(!root)throw Error('Appearance viewer root unavailable');
createRoot(root).render(<TomatoAppearanceScene/>);
