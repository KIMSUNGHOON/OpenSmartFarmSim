import {createRoot} from 'react-dom/client';
import {createApi} from '../src/api';
import SelectedCropReplay from '../src/SelectedCropReplay';
import '@fontsource-variable/noto-sans-kr';
import '../src/App.css';

const target=document.getElementById('root');if(!target)throw Error('isolated test root unavailable');
const root=createRoot(target);let token:string|null=null,api:ReturnType<typeof createApi>|null=null;
window.__showSelectedCrop=(next,selection)=>{
  if(next!==token){token=next;api=next===null?null:createApi(next);}
  root.render(<SelectedCropReplay api={api} selection={selection}/>);
};
