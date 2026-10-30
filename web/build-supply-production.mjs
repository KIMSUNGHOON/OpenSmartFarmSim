import {build} from 'vite';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {dirname,join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const root=dirname(fileURLToPath(import.meta.url)),repo=dirname(root);
const out=resolve(process.argv[2]??join(root,'dist-supply-production'));
if(process.argv.length>3||fs.existsSync(out))throw Error('Choose a new output directory; existing builds are retained.');
const inventory=JSON.parse(fs.readFileSync(join(repo,'research/fixtures/supply-morphology-public-20261030.json'),'utf8'));
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const originals=Object.entries(inventory.files).map(([name,pin])=>{
 if(name.includes('/')||name.includes('\\')||name==='.'||name==='..')throw Error('Invalid public fixture name.');
 const raw=fs.readFileSync(join(repo,inventory.directory,name));
 if(raw.length!==pin.bytes||hash(raw)!==pin.sha256)throw Error('Original public fixture changed.');return [name,raw];
});
if(originals.length!==101)throw Error('Unexpected fixture inventory.');
await build({root,configFile:join(root,'vite.supply-production.config.ts'),build:{outDir:out,emptyOutDir:false}});
const destination=join(out,'supply-morphology-replay/own-public-v1');fs.mkdirSync(destination,{recursive:true});
for(const [name,raw]of originals)fs.writeFileSync(join(destination,name),raw,{flag:'wx'});
fs.mkdirSync(join(out,'licenses'),{recursive:true});
for(const name of ['three-MIT.txt','noto-sans-kr-OFL.txt'])fs.copyFileSync(join(root,'public/licenses',name),join(out,'licenses',name),fs.constants.COPYFILE_EXCL);
fs.copyFileSync(join(root,'public/crop-appearance-icon.svg'),join(out,'crop-appearance-icon.svg'),fs.constants.COPYFILE_EXCL);
const files={};function walk(dir){for(const name of fs.readdirSync(dir)){const path=join(dir,name);if(fs.statSync(path).isDirectory())walk(path);else{const raw=fs.readFileSync(path);files[path.slice(out.length+1)]={bytes:raw.length,sha256:hash(raw)};}}}walk(out);
fs.writeFileSync(join(out,'build-manifest.json'),JSON.stringify({schema_version:'supply-replay-build-v1',scope:'own_synthetic_research_only',original_public_files:101,files},null,2),{flag:'wx'});
console.log(JSON.stringify({built_files:Object.keys(files).length+1,original_public_files:101}));
