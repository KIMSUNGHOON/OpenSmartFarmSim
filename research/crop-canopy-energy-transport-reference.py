"""Independent Decimal80 capacity-inventory oracle; no app imports."""
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_SHA256 = 'd606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca'
D = Decimal
MASS = 'mg_CH2O/m2_floor'
TRANSPORT_UNITS = {'leaf_carbohydrate': MASS, 'leaf_allocation': MASS+'/s',
    'leaf_maintenance': MASS+'/s', 'leaf_removal': MASS+'/s',
    'leaf_heat_capacity': 'J/m2_leaf/K', 'canopy_temperature': 'degC',
    'incoming_capacity_temperature': 'degC', 'reference_temperature': 'degC'}
EVENT_UNITS = {'leaf_carbohydrate': MASS, 'leaf_removed': MASS,
    'leaf_heat_capacity': 'J/m2_leaf/K', 'canopy_sensible_energy': 'J/m2_floor',
    'reference_temperature': 'degC'}


def block(name, values, units):
    return {'input_id': 'synthetic-capacity-'+name, 'origin': 'synthetic',
        'values': {k: {'value': float(v), 'unit': units[k]} for k, v in values.items()}}


def transport(v, sla):
    leaf, cap = v['leaf_carbohydrate'], v['leaf_heat_capacity']
    tc, tin, ref = (v[k] for k in ('canopy_temperature','incoming_capacity_temperature','reference_temperature'))
    lai = sla*leaf
    capacity = cap*lai
    g, dm, dr = (cap*sla*v[k] for k in ('leaf_allocation','leaf_maintenance','leaf_removal'))
    net = g-dm-dr
    qin, qm, qr = g*(tin-ref), dm*(tc-ref), dr*(tc-ref)
    material = qin-qm-qr
    # Derive temperature from the open energy inventory, independently of the reduced formula.
    temperature_rate = (material-(tc-ref)*net)/capacity
    return dict(zip(('leaf_area_index','canopy_capacity','canopy_sensible_energy','leaf_net_rate',
        'capacity_allocation','capacity_maintenance','capacity_removal','capacity_net',
        'energy_incoming','energy_maintenance_outgoing','energy_removal_outgoing','energy_net',
        'material_temperature_rate','storage_rate_from_chain_rule'),
        (lai,capacity,capacity*(tc-ref),v['leaf_allocation']-v['leaf_maintenance']-v['leaf_removal'],
         g,dm,dr,net,qin,qm,qr,material,temperature_rate,capacity*temperature_rate+(tc-ref)*net)))


def removal(v, sla):
    leaf, removed, cap, energy, ref = (v[k] for k in EVENT_UNITS)
    lai = sla*leaf
    before = cap*lai
    temperature = ref+energy/before
    after_leaf = leaf-removed
    after_lai = sla*after_leaf
    after = cap*after_lai
    # Outflow from the removed capacity and its temperature; avoid app U*capacity-ratio path.
    outgoing = cap*sla*removed*(temperature-ref)
    after_energy = energy-outgoing
    return {'before_leaf_carbohydrate':leaf,'before_leaf_area_index':lai,
        'before_canopy_capacity':before,'before_canopy_sensible_energy':energy,
        'before_canopy_temperature':temperature,'after_leaf_carbohydrate':after_leaf,
        'after_leaf_area_index':after_lai,'after_canopy_capacity':after,
        'after_canopy_sensible_energy':after_energy,'after_canopy_temperature':ref+after_energy/after,
        'outgoing_sensible_energy':outgoing}


def references():
    raw = (ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()
    assert sha256(raw).hexdigest() == PROFILE_SHA256
    sla = D(str(json.loads(raw)['parameters']['sla']['value']))
    flow_cases, event_cases = [], []
    with localcontext() as context:
        context.prec = 80
        programs = [('no-flow','0','0','0','22','0'),
            ('same-temperature-entry','2','0','0','22','0'),
            ('cold-entry','2','.5','.25','14','0'),
            ('warm-entry','2','.5','.25','30','0'),
            ('maintenance-only','0','2','0','22','0'),
            ('continuous-removal-only','0','0','2','22','0'),
            ('net-zero-cold-entry','2','1','1','14','0'),
            ('cold-entry-reference20','2','.5','.25','14','20'),
            ('cold-entry-reference30','2','.5','.25','14','30'),
            ('cold-entry-reference-minus10','2','.5','.25','14','-10')]
        for name, allocation, maintenance, removed, incoming, reference in programs:
            v = dict(zip(TRANSPORT_UNITS,map(D,('75000',allocation,maintenance,removed,'1200','22',incoming,reference))))
            flow_cases.append({'case_id':name,'forcing':block(name,v,TRANSPORT_UNITS),
                'expected_decimal':{k:str(x) for k,x in transport(v,sla).items()}})
        for name, removed, reference in [('partial-reference0','15000','0'),
                ('partial-reference20','15000','20'),('partial-reference30','15000','30'),
                ('zero-removal','0','0'),('zero-energy-partial','15000','22')]:
            ref = D(reference)
            v = dict(zip(EVENT_UNITS,(D('75000'),D(removed),D('1200'),D('1200')*sla*D('75000')*(D('22')-ref),ref)))
            event_cases.append({'case_id':name,'event':block(name,v,EVENT_UNITS),
                'expected_decimal':{k:str(x) for k,x in removal(v,sla).items()}})
    return {'version':'crop-canopy-energy-transport-reference-cases-v1',
        'scope':'synthetic_software_reference_only','profile_sha256':PROFILE_SHA256,
        'oracle':'independent_Decimal80_open_capacity_inventory_no_app_import',
        'input_basis':'self-authored represented leaf-capacity cases, not cultivar measurements; capLeaf1200 is explicit synthetic input and not farm adoption; carbon is not leaf-water mass; metabolic heat excluded',
        'transport_cases':flow_cases,'event_cases':event_cases}


if __name__ == '__main__':
    print(json.dumps(references(),sort_keys=True,indent=2))
