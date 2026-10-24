"""Independent Decimal optical oracle, using the retained source parameter file."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT/'fixtures/crop-growth-reference-parameters-v1.json'
PROFILE_SHA256 = 'd606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca'


def independent_optics(inputs, parameters):
    def dec(value): return Decimal.from_float(float(value))
    with localcontext() as ctx:
        ctx.prec = 110
        p = {key: dec(row['value']) for key,row in parameters.items()}
        v = {key: dec(row['value']) for key,row in inputs['values'].items()}
        L, T, par = v['leaf_area_index'], v['canopy_temperature'], v['par_above_canopy']
        if par == 0:
            return {'photosynthesis': '0', 'compensation_point_ppm': None, 'electron_transport': '0'}
        if L == 0:
            if T != p['compensation_pivot_c']: return None
            return {'photosynthesis': '0', 'compensation_point_ppm': str(p['cGamma']*T), 'electron_transport': '0'}
        gamma = p['cGamma']*(p['compensation_pivot_c']+(T-p['compensation_pivot_c'])/L)
        ci = p['etaCo2AirStom']*v['co2']
        if gamma < 0 or gamma > ci: return None
        absorbed = par*(1-p['rhoCanPar'])*((1-(-p['k1Par']*L).exp())+
            p['rhoFlrPar']*(-p['k1Par']*L).exp()*(1-(-p['k2Par']*L).exp()))
        K = T+p['kelvin_offset']; gas = p['gas_constant_scale']*p['R']; ref = p['t25k']
        maximum = L*p['j25LeafMax']*(p['eJ']*(K-ref)/(gas*K*ref)).exp()*(1+((p['S']*ref-p['H'])/(gas*ref)).exp())/(1+((p['S']*K-p['H'])/(gas*K)).exp())
        light = p['alpha']*absorbed
        electron = (maximum+light-((maximum+light)**2-4*p['theta']*maximum*light).sqrt())/(2*p['theta'])
        gross = electron*(ci-gamma)/(p['electron_per_fixed_co2']*(ci+p['compensation_denominator_factor']*gamma))
        photorespiration = gross*gamma/ci
        inhibition = 1/(1+(p['buffer_full_slope']*(v['buffer']-p['cBufMax'])).exp())
        carbon = p['mCh2o']*inhibition*(gross-photorespiration)
        return {'photosynthesis': str(carbon), 'compensation_point_ppm': str(gamma), 'electron_transport': str(electron)}


def generate():
    raw = PROFILE.read_bytes(); assert sha256(raw).hexdigest() == PROFILE_SHA256
    parameters = json.loads(raw)['parameters']
    bases = json.loads((ROOT/'fixtures/crop-growth-reference-cases-v1.json').read_bytes())['cases']
    cases = []
    for base in bases:
        for lai in (0, 0.001, 0.1, 0.3, 1, 3):
            for buffer in (0, base['state']['values']['buffer']['value']):
                for par in (0, max(200, base['forcing']['values']['par_above_canopy']['value'])):
                    values = {**deepcopy(base['forcing']['values']), 'buffer': {'value': buffer, 'unit': 'mg_CH2O/m2_floor'},
                              'leaf_area_index': {'value': lai, 'unit': 'm2_leaf/m2_floor'}}
                    values['par_above_canopy']['value'] = par
                    inputs = {'input_id': 'explicit-optical-reference-' + str(len(cases)), 'origin': 'synthetic', 'values': values}
                    expected = independent_optics(inputs, parameters)
                    cases.append({'case_id': inputs['input_id'], 'source_software_case': base['case_id'], 'inputs': inputs,
                                  'expected_decimal': expected, 'status': 'supported' if expected is not None else 'COMPENSATION_POINT_HOLD'})
    assert len(cases) == 96 and not any(name == 'app' or name.startswith('app.') for name in sys.modules)
    return {'schema_version': 'explicit-lai-photosynthesis-software-reference-v1', 'origin': 'own_synthetic_software_fixture',
            'G0_G4': 'not_assessed', 'independent_precision': 110, 'profile_sha256': PROFILE_SHA256,
            'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(), 'cases': cases}


if __name__ == '__main__':
    output = Path(sys.argv[1]); data = generate(); output.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    print(json.dumps({'cases': len(data['cases']), 'supported': sum(c['status']=='supported' for c in data['cases']),
                      'sha256': sha256(output.read_bytes()).hexdigest(), 'app_imports': 0}))
