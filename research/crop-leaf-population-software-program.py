"""Canonical owned probe declaration, with a required actual declaration timestamp."""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def program(declared_at):
    original=json.loads((ROOT/'fixtures/crop-leaf-area-software-program-v1.json').read_bytes())
    final=json.loads((ROOT/'web/public/morphology-rational-replay/frame-11.json').read_bytes())
    prototype=original['initialization']['leaves'][0]['initialization'];events=[]
    for i,node in enumerate(final['internodes'][3:]):
        events.append({'leaf_id':'explicit-followup-leaf-'+str(i),'attachment_internode_id':node['internode_id'],
            'emerged_elapsed_seconds_exact':deepcopy(node['emerged_elapsed_seconds_exact']),
            **{k:deepcopy(prototype[k]) for k in ['curve','normalization','initial_area']},
            'base_temperature':deepcopy(prototype['clock_state']['base_temperature'])})
    return {'schema_version':'leaf-population-software-program-v1','origin':'synthetic','program_id':'owned-explicit-leaf-population-probe',
        'rights':{**original['rights'],'declaration_id':'owned-leaf-population-probe-20261022','revision':'r1','declared_at_utc':declared_at},
        'stem':original['stem'],'initialization':{'input_id':'owned-explicit-population','initial_inventory':original['initialization']},
        'births':events,'display_policy':{**original['display_policy'],'leaf_count':'declared_initial_and_births_only'}}


if __name__=='__main__':
    sys.stdout.write(json.dumps(program(sys.argv[1]),sort_keys=True,separators=(',',':'),allow_nan=False))
