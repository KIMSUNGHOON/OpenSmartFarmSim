"""Write explicit self-authored arithmetic/appearance inputs, not crop parameters."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path


def program(stem_input,stem_root,declared_at):
    p=json.loads(stem_input);t=p['initial_state']['timeline_state'];leaves=[]
    with localcontext() as c:
        c.prec=100
        for i,maximum in enumerate((.0015,.002,.0025)):
            m=Decimal.from_float(maximum);initial=m/(1+Decimal(2).exp())
            leaves.append({'attachment_internode_id':p['initial_state']['internodes'][i]['length_state']['clock_state']['internode_id'],
                'initialization':{'input_id':'synthetic-leaf-'+str(i),'clock_state':{'origin':'synthetic',
                    'age_basis':'since_leaf_emergence','temperature_basis':'indoor_air_piecewise_constant',
                    'leaf_id':'declared-leaf-'+str(i),'time_origin_utc':t['started_at'],
                    'emerged_elapsed_seconds_exact':{'numerator':'0','denominator':'1','unit':'s'},
                    'at_elapsed_seconds_exact':{'numerator':'0','denominator':'1','unit':'s'},
                    'base_temperature':{'value':5,'unit':'degC'},
                    'age_exact':{'numerator':'0','denominator':'1','unit':'degC_day'}},
                'curve':{'profile_id':'synthetic-leaf-curve-'+str(i),'origin':'synthetic','values':{
                    'maximum_area':{'value':maximum,'unit':'m2'},'steepness':{'value':.25,'unit':'1/degC_day'},
                    'inflection_age':{'value':8,'unit':'degC_day'}}},'normalization':'zero_lower_asymptote_sigmoid_v1',
                'initial_area':{'value':float(initial),'unit':'m2'}}})
    return {'schema_version':'leaf-software-program-v1','origin':'synthetic','program_id':'synthetic-declared-leaf-day-v1',
        'rights':{'access':True,'declaration_id':'self-authored-leaf-fixture','declared_at_utc':declared_at,
            'display':True,'ownership_asserted':True,'redistribute':True,'revision':'r1-public-12',
            'store':True,'transform':True,'use':True},
        'stem':{'artifact_sha256':stem_root,'program_sha256':sha256(stem_input).hexdigest()},
        'initialization':{'input_id':'synthetic-initial-leaf-inventory','time_origin_utc':t['started_at'],
            'at_elapsed_seconds_exact':{'numerator':'0','denominator':'1','unit':'s'},'leaves':leaves},
        'display_policy':{'version':'stored-leaf-m2-authored-blade-triangles-v1',
            'surface':'one_sided_authored_leaflet_triangles','petiole_rachis_area_excluded':True,
            'placement':'declared_attachment_upper_end_authored_angles_v1',
            'length_width_shape':'authored_uniform_scale_not_cultivar_prediction','leaf_count':'declared_initial_only'}}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stem-input',type=Path,required=True);p.add_argument('--stem-root',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--declared-at');args=p.parse_args()
    stamp=args.declared_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
    args.output.write_text(json.dumps(program(args.stem_input.read_bytes(),args.stem_root,stamp),sort_keys=True,separators=(',',':')))
