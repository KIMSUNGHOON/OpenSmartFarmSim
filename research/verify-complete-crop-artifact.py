#!/usr/bin/env python3
"""Verify one trusted complete research artifact in a cold, read-only process.

The caller supplies the trusted root and original packet. This checks software
preservation; it grants no farm authority or agricultural claim gate.
"""
import argparse
from hashlib import sha256
import importlib.abc
import json
import os
from pathlib import Path
import socket
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--root',required=True)
    parser.add_argument('--expected-packet',type=Path,required=True)
    args=parser.parse_args()
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
    import psycopg
    calls={key:0 for key in ('growth_import','DB','CLI','network','write_open')}
    allowed={'crop_complete_artifact_reader','crop_leaf_funded_birth_artifact_reader',
        'crop_leaf_carbon_stock_artifact_reader','crop_rational_morphology_artifact_reader',
        'crop_morphology_artifact_reader','crop_morphology_artifact_io'}

    class NoGrowth(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname.startswith('app.crop_')and fullname.removeprefix('app.')not in allowed:
                calls['growth_import']+=1
                raise AssertionError('reader imported growth: '+fullname)

    def forbidden(kind):
        def fail(*a,**k):
            calls[kind]+=1
            raise AssertionError(kind+' forbidden in reader')
        return fail

    def audit(event,values):
        if event=='open':
            flags=values[2]or 0
            if isinstance(flags,int)and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
                calls['write_open']+=1
                raise AssertionError('write open forbidden in reader')

    sys.meta_path.insert(0,NoGrowth())
    psycopg.connect=forbidden('DB')
    subprocess.Popen=forbidden('CLI')
    socket.socket=forbidden('network')
    sys.addaudithook(audit)
    from app import crop_complete_artifact_reader as reader
    from app.content_access import ContentAccess
    access=ContentAccess(os.getuid(),os.getegid())
    with args.expected_packet.open('rb')as stream:expected=stream.read(reader.MAX+1)
    assert len(expected)<=reader.MAX,'expected packet exceeds cap'
    manifest=reader.read_complete_crop_manifest(args.directory,access,args.root)
    packet=reader.read_complete_crop_packet(args.directory,access,args.root)
    assert reader._canonical(packet)==expected,'stored packet differs from supplied original bytes'
    frames=packet['frames'];dense=next(i for i,f in enumerate(frames)if f['evidence']['checkpoint']is None)
    selected=(0,dense,dense+1,len(frames)-1)
    for index in selected:
        value=reader.read_complete_crop_frame(args.directory,access,args.root,index=index)
        assert value['frame']==frames[index]
        state=value['snapshot']['state'];n=len(value['leaves'])
        for j,leaf in enumerate(value['leaves']):
            assert [leaf[k]['value']for k in ('thermal_age','area','carbohydrate')]==[state[107+j],state[107+n+j],state[107+2*n+j]]
    loaded=[name for name in sys.modules if name.startswith('app.crop_')]
    assert all(name.removeprefix('app.')in allowed for name in loaded)and not any(calls.values())
    print(json.dumps({'root_sha256':args.root,'frames':len(frames),'packet_sha256':sha256(expected).hexdigest(),
        'source_checkpoints':sum(f['evidence']['kind']=='original_funded_checkpoint'for f in frames),
        'dense_candidates':sum(f['evidence']['checkpoint']is None for f in frames),
        'leaf_state_values':3*sum(len(f['leaves'])for f in frames),'selected_decoded_frames':len(selected),
        'code_pins':len(manifest['code_sha256']),'calls':calls,'loaded_crop_modules':loaded,
        'G0_G4':'not_assessed','R2':'not_approved'},sort_keys=True))


if __name__=='__main__':main()
