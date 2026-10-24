import {createRoot} from 'react-dom/client';
import MorphologyScene from '../src/MorphologyScene';
import {loadLeafLifecycleReplay} from '../src/leafLifecycleReplay';
import '../src/MorphologyReplayPage.css';

const root=document.getElementById('root');if(!root)throw Error('empty geometry test root unavailable');
const replay=await loadLeafLifecycleReplay('with-removal',new AbortController().signal),frame=replay.frames.at(-1)!;
createRoot(root).render(<main className="morphology-page"><MorphologyScene frame={frame.stem} maximum={frame.stem.tracked_axis_length.value}
 leafBinding={{artifact_sha256:frame.artifact_sha256,result_sha256:frame.result_sha256,at:frame.at,leaves:[]}}/></main>);
