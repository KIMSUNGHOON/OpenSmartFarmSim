"""New owned material-point results with independent Decimal/exact-ledger checks."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app import crop_funded_fractional_birth_point as model
from app.content_access import ContentAccess


def declared(context, declaration, web, count, temperature):
    captured = context.value
    events = []
    for i in range(count):
        leaf = deepcopy(captured['program']['leaves'][0])
        leaf.update(leaf_id=f'qa-fractional-leaf-{i}', thermal_age={'value': 0., 'unit': 'degC_day'},
                    initial_area=model.short.old.leaf_area._area_at(Fraction(0), leaf['curve']))
        leaf.update({k: deepcopy(web['new_leaf_values'][k]) for k in ('initial_carbon', 'sink_weight', 'carbon_removal')})
        events.append({'event_id': f'qa-fractional-event-{i}', 'attachment_internode_id': f'declared-only-node-{i}',
                       'incoming_temperature': {'value': temperature, 'unit': 'degC'}, 'leaf': leaf})
    return {'schema_version': 'funded-fractional-birth-point-input-v1', 'input_id': 'own-fractional-point-qa',
            'origin': 'synthetic', 'policy': model.point.POLICY, 'context_sha256': context.sha256,
            'candidate_sha256': model._digest(captured['candidate']),
            'at_elapsed_seconds_exact': captured['candidate']['at']['elapsed_seconds_exact'],
            'model_floor_area': captured['program']['model_floor_area'], 'events': events}


def independent(result, context):
    before = result['before_sample']; after = result['after_sample']; p = result['after_program']
    a, b = before['state'], after['state']; n = len(context.value['program']['leaves']); size = len(p['leaves'])
    assert result['source_candidate'] == context.value['candidate']
    assert before['at'] == after['at'] == context.value['candidate']['at'] and 'step_index' not in before
    assert b[1:104] == a[1:104] and b[105:107] == a[105:107]
    assert b[107:107+n] == a[107:107+n] and b[107+n:107+size] == [0.]*(size-n)
    assert b[107+size:107+size+n] == a[107+n:107+2*n]
    assert b[107+2*size:107+2*size+n] == a[107+2*n:]
    assert after['curve_invariant_changes'][:n] == before['curve_invariant_changes']
    d = Decimal.from_float
    flows = result['point_flows']
    with localcontext() as dc:
        dc.prec = 200
        masses = [d(row['initial_carbon']['value']) for row in p['leaves'][n:]]
        cost = d(context._profiles[0].values['cLeafG']); total = sum(masses, Decimal(0))
        assert flows['structural_carbon']['value'] == float(total)
        assert flows['growth_respiration']['value'] == float(cost*total)
        assert flows['buffer_debit']['value'] == float(total*(1+cost))
        assert b[0] == float(d(a[0])-d(flows['buffer_debit']['value']))
        k, floor, ref = [d(q['value']) for q in (p['scenario']['parameters']['leaf_heat_capacity'], p['model_floor_area'], p['scenario']['parameters']['reference_temperature'])]
        caps, energies = [], []
        for receipt, event in zip(result['birth_receipts'], result['inputs']['events'], strict=True):
            values = event['leaf']['curve']['values']
            maximum, steepness, midpoint = [d(float(values[key]['value'])) for key in ('maximum_area', 'steepness', 'inflection_age')]
            expected_area = maximum/(1+(steepness*midpoint).exp())
            area = receipt['initialization']['state']['area']['value']
            assert abs(d(area)-expected_area) <= Decimal('1e-12')*abs(expected_area)
            cap = float(k*d(area)/floor); energy = float(d(cap)*(d(event['incoming_temperature']['value'])-ref))
            assert receipt['capacity_in']['value'] == cap and receipt['sensible_in']['value'] == energy
            caps.append(d(cap)); energies.append(d(energy))
        assert flows['capacity_in']['value'] == float(sum(caps, Decimal(0)))
        assert flows['sensible_in']['value'] == float(sum(energies, Decimal(0)))
        assert b[104] == float(d(a[104])+d(flows['sensible_in']['value']))
    f = {k: Fraction.from_float(v['value']) for k, v in flows.items()}
    carbon = lambda y, count: fsum([y[0], y[1], *y[4:54], *y[107+2*count:]])
    terms = {'buffer': (b[0], -a[0], flows['buffer_debit']['value']),
             'new_stock': (*[row['initial_carbon']['value'] for row in p['leaves'][n:]], -flows['structural_carbon']['value']),
             'whole_carbon': (carbon(b, size), -carbon(a, n), flows['growth_respiration']['value']),
             'sensible': (b[104], -a[104], -flows['sensible_in']['value']),
             'capacity': (after['derived']['canopy_capacity']['value'], -before['derived']['canopy_capacity']['value'], -flows['capacity_in']['value'])}
    for name, row in terms.items():
        exact = sum(map(Fraction.from_float, row), Fraction(0)); balance = result['balances'][name]
        assert float(exact) == balance['residual']['value'] and abs(exact) <= Fraction.from_float(balance['budget']['value'])
    assert result['checkpoint'] is None and result['attachment_status'] == 'declared_not_bound_to_stem'
    return size-n


def verify(source, output):
    source, output = Path(source), Path(output)
    raw = (ROOT/'fixtures/crop-funded-fractional-birth-point-fixtures-v1.json').read_bytes(); declaration = json.loads(raw)
    for path, expected in declaration['sources'].items():
        assert sha256((ROOT/path).read_bytes()).hexdigest() == expected
    assert all(declaration['rights'][k] is True for k in ('use', 'display', 'redistribute'))
    register = json.loads((source/'register.json').read_bytes())
    assert register['declaration_sha256'] == declaration['sources']['fixtures/crop-funded-event-state-fixtures-v2.json']
    web = json.loads((ROOT/declaration['new_leaf_values_source']).read_bytes())
    output.mkdir(mode=0o750)
    access = ContentAccess(os.getuid(), os.getgid()); records = []; receipts = 0; contexts = []; holds = []
    for case in register['cases']:
        directory = source/'leaves'/str(case['case_index'])
        m = model.leaf.read_funded_leaf_manifest(directory, access, case['leaf_root_sha256'])
        assert m['source_rights']['redistribute'] is True
        context = model.prepare_fractional_birth_context(directory, source/'stem', access,
            leaf_root_sha256=case['leaf_root_sha256'], stem_root_sha256=register['stem_root_sha256'],
            stem_start_index=case['stem_start_index'], bracket_index=0,
            time_tolerance_seconds_exact={'numerator': '1', 'denominator': '1000000', 'unit': 's'})
        contexts.append({'case_index': case['case_index'], 'context_sha256': context.sha256,
                         'candidate_sha256': model._digest(context.value['candidate'])})
        plans = [(n, t) for n in declaration['batch_counts'] for t in declaration['incoming_temperatures_degC']]
        if case['case_index'] == declaration['maximum_case']:
            plans.append((declaration['maximum_result_leaves']-len(context.value['program']['leaves']), web['new_leaf_values']['incoming_temperature']['value']))
        for count, temperature in plans:
            value = declared(context, declaration, web, count, temperature)
            try:
                result = model.apply_fractional_births(context=context, inputs=value)
            except model.FractionalBirthHold as error:
                if count in declaration['batch_counts'] or not str(error).startswith('CAPACITY_HOLD:'):
                    raise
                frames = []; current = error; visited = set()
                while current is not None and id(current) not in visited:
                    visited.add(id(current)); trace = current.__traceback__
                    while trace is not None:
                        frame = trace.tb_frame
                        if frame.f_code.co_name == '_canonical' and isinstance(frame.f_locals.get('raw'), bytes):
                            frames.append({'module': frame.f_globals.get('__name__'),
                                'serialized_bytes': len(frame.f_locals['raw']), 'limit_bytes': frame.f_globals.get('MAX_BYTES')})
                        trace = trace.tb_next
                    current = current.__context__
                name = f"held-case-{case['case_index']}-count-{count}-inputs.json"
                data = model._canonical(value); (output/name).write_bytes(data)
                holds.append({'case_index': case['case_index'], 'count': count, 'temperature': temperature,
                    'reason': str(error), 'capacity_frames': frames, 'inputs_path': name,
                    'inputs_sha256': sha256(data).hexdigest(), 'requested_case_accepted': False})
                continue
            receipts += independent(result, context)
            name = f"case-{case['case_index']}-count-{count}-temperature-{temperature}.json"
            data = model._canonical(result); (output/name).write_bytes(data)
            records.append({'case_index': case['case_index'], 'count': count, 'temperature': temperature,
                            'result_leaves': len(result['after_program']['leaves']), 'path': name,
                            'sha256': sha256(data).hexdigest(), 'bytes': len(data)})
    summary = {'scope': 'software_research_only', 'G0_G4': 'not_assessed', 'declaration_sha256': sha256(raw).hexdigest(),
               'source_register_sha256': sha256((source/'register.json').read_bytes()).hexdigest(),
               'contexts': contexts, 'points': records, 'point_count': len(records), 'holds': holds,
               'verification_status': 'normal_points_verified_boundary_capacity_hold' if holds else 'all_requested_points_verified',
               'all_requested_points_accepted': not holds, 'independent_Decimal_precision': 200,
               'independent_leaf_receipts': receipts, 'independent_point_balances': 5*len(records),
               'checkpoint_adoptions': 0, 'actual_stem_attachment': 'not_bound'}
    (output/'index.json').write_bytes(model._canonical(summary))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('source', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.source, args.output), sort_keys=True))
