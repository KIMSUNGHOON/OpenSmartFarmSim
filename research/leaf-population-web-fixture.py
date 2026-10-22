"""Compile original exported declaration metadata without evaluating crop models."""
from hashlib import sha256
import json
from pathlib import Path
import sys


def fixture(directory):
    raw=(directory/'index.json').read_bytes();index=json.loads(raw)
    root=(directory/'root.json').read_bytes();assert sha256(root).hexdigest()==index['artifact_sha256']
    declarations={}
    for descriptor in index['frames']:
        raw_frame=(directory/descriptor['path']).read_bytes();assert sha256(raw_frame).hexdigest()==descriptor['sha256']
        for leaf in json.loads(raw_frame)['leaves']:
            declaration={key:leaf[key] for key in ['leaf_id','attachment_internode_id','curve_sha256','emerged_elapsed_seconds_exact']}
            if leaf['leaf_id'] in declarations:assert declarations[leaf['leaf_id']]==declaration
            else:declarations[leaf['leaf_id']]=declaration
    return {'artifact_sha256':index['artifact_sha256'],'index_sha256':sha256(raw).hexdigest(),'frames':len(index['frames']),
            'declared_leaves':list(declarations.values())}


if __name__=='__main__':
    print('export const LEAF_POPULATION_FIXTURE='+json.dumps(fixture(Path(sys.argv[1])),sort_keys=True,separators=(',',':'))+' as const;')
