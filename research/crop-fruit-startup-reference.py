"""Independent startup policy algebra; no product imports or cultivar outputs."""
import argparse
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'explicit-entry-empty-sink-deferral-research-v1'


def references():
    profile_path = ROOT / 'fixtures/crop-fruit-cohort-reference-parameters-v1.json'
    profile = json.loads(profile_path.read_bytes())
    p = {key: Decimal(str(value.get('source_value', value['value'])))
         for key, value in profile['parameters'].items()}
    cases, alternatives = [], []
    data = (
        ('established', '10', '2', '1', {1:'7', 2:'2', 50:'3'}, None),
        ('balanced-first-entry', '6', '2', '3', {}, None),
        ('empty-tail-first-entry', '10', '2', '1', {1:'7'}, None),
        ('all-empty-first-entry', '10', '2', '1', {}, None),
        ('all-empty-no-entry', '10', '0', '0', {}, None),
        ('all-empty-zero', '0', '0', '0', {}, None),
        ('zero-entry-positive-tail', '10', '0', '0', {2:'2', 50:'3'}, None),
        ('small-empty-tail', '1e-20', '2e-21', '1', {}, None),
        ('large-empty-tail', '1e20', '2e19', '1', {}, None),
        ('entry-over-budget', '1', '2', '1', {2:'5'}, 'ENTRY_BUDGET_HOLD'),
        ('missing-W1', '10', '2', None, {}, 'INPUT_HOLD'),
        ('zero-W1-with-entry', '10', '2', '0', {}, 'ENTRY_STATE_HOLD'),
        ('missing-S', '10', None, '1', {}, 'INPUT_HOLD'),
        ('negative-S', '10', '-1', '1', {}, 'INPUT_HOLD'),
    )
    with localcontext() as context:
        context.prec = 70
        cg = p['fruit_growth_respiration']
        for name, f, s, w1, weights, hold in data:
            case = {'case_id':'synthetic-' + name, 'origin':'synthetic',
                    'requested_F':f, 'S':s, 'W1':w1,
                    'weights':[weights.get(j, '0') for j in range(1, 51)],
                    'expected_hold':hold}
            if hold is None:
                F, S, W1 = map(Decimal, (f, s, w1))
                A1 = S * W1
                tail = [Decimal(weights.get(j, '0')) for j in range(2, 51)]
                D2 = sum(tail)
                effective = F if D2 > 0 else A1
                deferred = F - effective
                allocated = [A1] + [(F-A1)*w/D2 if D2 > 0 else Decimal(0) for w in tail]
                retained = deferred * (1+cg)
                growth = effective * cg
                baseline_buffer = -F * (1+cg)
                residual = baseline_buffer + retained + sum(allocated) + growth
                assert sum(allocated) == effective and effective + deferred == F
                assert residual == 0 and sum([S] + [Decimal(0)]*49) == S
                case.update(effective_F=str(effective), deferred_F=str(deferred),
                    buffer_derivative_adjustment=str(retained), realized_growth_respiration=str(growth),
                    allocation=list(map(str, allocated)),
                    number_inflow=[str(S)] + ['0']*49,
                    whole_plant_carbon_residual=str(residual),
                    restore_structural_only_with_realized_respiration_residual=str(-cg*deferred),
                    unchanged_growth_respiration_extra_charge=str(cg*deferred),
                    legacy_allocation_hold='EMPTY_FRUIT_SINK_HOLD' if deferred > 0 else None)
            cases.append(case)
        for temperature in ('17', '20', '23'):
            rdev = p['cDev1'] + p['cDev2'] * Decimal(temperature)
            fgp = 1/(rdev*p['seconds_per_day'])
            peak = p['Gompertz_M_intercept'] + p['Gompertz_M_slope']*fgp
            b = 1/(p['Gompertz_B_intercept'] + p['Gompertz_B_M_slope']*peak)
            def mass(age):
                return p['GMax'] * (-(-b*(age-peak)).exp()).exp()
            zero, edge, midpoint = Decimal(0), fgp/p['nDev'], fgp/(2*p['nDev'])
            gr_mid = mass(midpoint)*b*(-b*(midpoint-peak)).exp()
            choices = (mass(edge)-mass(zero), mass(midpoint)-mass(zero), mass(edge))
            assert 0 < choices[1] < choices[0] < choices[2]
            alternatives.append({'reference_temperature_degC':temperature,
                'scope':'unadopted mathematical alternatives, not cultivar entry masses',
                'FGP_day':str(fgp), 'first_box_edge_day':str(edge),
                'integral_0_to_edge_mg_CH2O_per_fruit':str(choices[0]),
                'integral_0_to_midpoint_mg_CH2O_per_fruit':str(choices[1]),
                'absolute_mass_at_edge_mg_CH2O_per_fruit':str(choices[2]),
                'implementation_elapsed_100day_accumulation_mg_CH2O_per_fruit':str(gr_mid*100),
                'GR_over_GMax_per_s':str(gr_mid/p['GMax']/p['seconds_per_day']),
                'Gompertz_relative_rate_at_midpoint_per_s':str(gr_mid/mass(midpoint)/p['seconds_per_day'])})
        onset = {'scope':'synthetic original piecewise pre-onset counterexample',
            'initial_N1':'1', 'initial_C1':'5', 'dt_s':'1', 'transport_k_per_s':'0.1',
            'number_gate':'0', 'N2_after':'0', 'C2_after':'0.5',
            'conclusion':'positive carbon with zero number; do not reuse post-onset invariant or silently gate carbon'}
        assert Decimal(onset['C2_after']) == Decimal(onset['initial_C1'])*Decimal(onset['transport_k_per_s'])*Decimal(onset['dt_s'])
    return {'evidence_version':'crop-fruit-startup-policy-reference-v1',
        'policy_id':POLICY, 'scope':'independent synthetic research algebra, no product implementation acceptance',
        'method':'70-digit Decimal; explicit inputs; no product imports; no new agricultural coefficients',
        'pins':{str(path.relative_to(ROOT)):sha256(path.read_bytes()).hexdigest() for path in (
            Path(__file__), profile_path, ROOT/'contracts/crop-fruit-startup-policy-v1.md',
            ROOT/'research/crop-fruit-startup-source-register.json')},
        'cases':cases, 'accepted_algebra_cases':sum(c['expected_hold'] is None for c in cases),
        'hold_cases':sum(c['expected_hold'] is not None for c in cases),
        'W1_RGR_unadopted_alternatives':alternatives, 'pre_onset_counterexample':onset,
        'additional_policy_holds':['pre_onset_requires_separate_transport_policy',
            'missing_nonfinite_negative_RGR', 'carbon_positive_number_zero',
            'automatic_fruit_set_entry_mass_and_actual_phenology_unadopted'],
        'gates_opened':[], 'actual_crop_runs':0, 'independent_domestic_datasets':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
        default=ROOT/'research/artifacts/crop-fruit-startup-policy-reference-20261005.json')
    args = parser.parse_args()
    protected = (Path(__file__).resolve(), (ROOT/'contracts/crop-fruit-startup-policy-v1.md').resolve(),
        (ROOT/'research/crop-fruit-startup-source-register.json').resolve(),
        (ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').resolve())
    if args.output.is_symlink() or args.output.resolve() in protected:
        raise ValueError('reference_output_would_replace_input')
    document = references()
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'algebra_cases':document['accepted_algebra_cases'],
        'holds':document['hold_cases'], 'W1_RGR_alternatives':3, 'product_imports':False}))


if __name__ == '__main__':
    main()
