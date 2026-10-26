"""Project a source-bound coupled shoot and bind its declared funded leaves."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import fsum, isclose, isfinite
from pathlib import Path

from . import crop_funded_fractional_continuation as crop
from . import crop_rational_internode_length as length
from .crop_morphology_artifact_io import MorphologyBlobStore, _need

VERSION = 'funded-fractional-source-shoot-leaf-binding-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
F = Fraction.from_float
epochs = crop.birth.candidate.event.epochs
stem = epochs.stem
point = epochs.point


class FractionalStemBindingHold(ValueError):
    pass


def _pins():
    return {**crop._pins(), 'backend/app/crop_funded_fractional_stem_binding.py': sha256(Path(__file__).read_bytes()).hexdigest()}


def _exact(value, unit): return crop.birth.candidate.event._rational(value, unit)
def _fraction(value): return stem._fraction(value)
def _digest(value): return crop._digest(value)


def _fence():
    _need(_pins()['backend/app/crop_funded_fractional_stem_binding.py'] == CODE_SHA256,
          'CODE_HOLD: original fractional shoot binding required')


def _stem_source(context, source):
    selection = source['candidate']['selection']; index = selection['stem_start_index']
    manifest = stem.read_rational_morphology_manifest(context._stem_directory, context._access, selection['stem_root_sha256'])
    _need(manifest['code_sha256'] == {name: _pins()[name] for name in stem.SOURCE_PATHS}, 'CODE_HOLD: original stored stem code required')
    _need(type(index) is int and -1 <= index < len(manifest['samples']), 'INDEX_HOLD: actual stored stem selection required')
    with MorphologyBlobStore(context._stem_directory, context._access) as store:
        raw = store.get(manifest['program_sha256'], maximum=stem.PROGRAM_MAX); program = stem._parse(raw, stem.PROGRAM_MAX)
        state, state_sha, result_sha, result_raw = epochs._selected(store, context._stem_directory, context._access,
            selection['stem_root_sha256'], manifest, program, index)
        stem._state(state); timeline = state['timeline_state']
        _need(timeline['at'] == source['candidate']['at']['time_origin_utc'], 'TIME_HOLD: actual selected stem must begin the crop epoch')
        delta = stem._utc(timeline['at'])-stem._utc(timeline['started_at']); offset = Fraction(delta.days*86400+delta.seconds)
        _need(all(manifest['program_rights'][k] is True for k in ('use','display')), 'RIGHTS_HOLD: original stem use/display required')
        _need(store.get(manifest['program_sha256'], maximum=stem.PROGRAM_MAX) == raw, 'SOURCE_HOLD: stem program changed')
        if result_sha is not None:
            _need(store.get(result_sha, maximum=stem.RESULT_MAX) == result_raw, 'SOURCE_HOLD: selected stem result changed')
    return {'manifest': manifest, 'state': state, 'state_sha256': state_sha, 'result_sha256': result_sha,
            'program_sha256': manifest['program_sha256'], 'offset': offset}


def _birth(source, book):
    candidate = source['candidate']; certificate = candidate['source_root_certificate']; bracket = certificate['source_bracket']
    timeline = book['state']['timeline_state']; interval = certificate['numerical_root_interval']
    _need(bracket['sequence'] == timeline['next_sequence'] and bracket['thermal_age_exact'] == timeline['next_threshold_exact'],
          'EVENT_HOLD: first original source threshold required')
    at = _fraction(candidate['at']['elapsed_seconds_exact'])
    _need(candidate['at']['elapsed_seconds_exact'] == interval['upper_elapsed_seconds_exact']
          and interval['time_origin_utc'] == timeline['at'] and _fraction(interval['lower_elapsed_seconds_exact']) < at,
          'TIME_HOLD: original crossed-side numerical birth required')
    identity = {key: timeline[key] for key in ('shoot_id','development_origin_id','schedule_id','started_at')}
    identity.update(sequence=bracket['sequence'], birth_age_exact=bracket['thermal_age_exact'])
    return {'internode_id': 'internode:'+_digest(identity), 'sequence': bracket['sequence'],
        'threshold_age_exact': deepcopy(bracket['thermal_age_exact']), 'at_elapsed_seconds_exact': _exact(at,'s'),
        'development_elapsed_seconds_exact': _exact(book['offset']+at,'s'),
        'numerical_root_interval': deepcopy(interval), 'candidate_sha256': _digest(candidate),
        'event_time_scope': 'certified_polynomial_crossed_side_upper_bound_not_physical_error'}


def describe_fractional_internode(point_context):
    try:
        _fence(); source, _ = crop.birth._context(point_context); crop.birth._sources(point_context, source)
        book = _stem_source(point_context, source); result = _birth(source, book)
        _need(_stem_source(point_context, source) == book, 'SOURCE_HOLD: selected stem changed before return')
        crop.birth._sources(point_context, source); _fence()
        return {**result, 'model_version': VERSION, 'stem_source_state_sha256': book['state_sha256'],
                'emergence_profile': deepcopy(book['state']['emergence_profile']), 'scope': 'software_research_only', 'G0_G4': 'not_assessed'}
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise FractionalStemBindingHold(str(error)) from None


def _declaration(value, context, data, manifest, root_program):
    raw = crop._canonical(value)
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: bounded initial-link declaration required')
    value = crop._parse(raw, MAX_BYTES)
    crop.birth.point._closed(value, {'schema_version','input_id','origin','context_sha256','leaf_root_sha256',
        'stem_root_sha256','root_initial_state_sha256','model_floor_area','initial_attachments','rights','reviewer'})
    _need(value['schema_version'] == 'funded-fractional-initial-links-v1' and value['origin'] == 'synthetic',
          'SCOPE_HOLD: explicit synthetic initial links required')
    for key in ('input_id','reviewer'): stem._id(value[key])
    selection = data['source']['candidate']['selection']
    _need(value['context_sha256'] == context.sha256 and value['leaf_root_sha256'] == selection['leaf_root_sha256']
          and value['stem_root_sha256'] == selection['stem_root_sha256']
          and value['root_initial_state_sha256'] == manifest['initial_state_sha256'], 'SOURCE_HOLD: original initial-link identities required')
    crop.birth.leaf.stock._q(value['model_floor_area'], 'm2_floor')
    _need(value['model_floor_area'] == data['program']['model_floor_area'], 'BASIS_HOLD: common floor required')
    rights = value['rights']; crop.birth.point._closed(rights, {'declaration_id','revision','declared_at_utc',
        'ownership_asserted','access','store','use','transform','display','redistribute'})
    for key in ('declaration_id','revision'): stem._id(rights[key])
    stem._utc(rights['declared_at_utc'])
    _need(all(rights[k] is True for k in ('ownership_asserted','access','store','use','transform','display'))
          and type(rights['redistribute']) is bool, 'RIGHTS_HOLD: explicit initial-link rights required')
    links = value['initial_attachments']; _need(type(links) is list and len(links) == len(root_program['leaves']), 'ATTACHMENT_HOLD: complete initial leaf links required')
    for link, leaf in zip(links, root_program['leaves'], strict=True):
        crop.birth.point._closed(link, {'leaf_id','attachment_internode_id'})
        stem._id(link['leaf_id']); stem._id(link['attachment_internode_id'])
        _need(link['leaf_id'] == leaf['leaf_id'], 'ATTACHMENT_HOLD: original ordered root leaf IDs required')
    return value


def _leaf_links(context, data, declaration):
    source = data['source']; selection = source['candidate']['selection']
    with MorphologyBlobStore(context._leaf_directory, context._access) as store:
        raw = store.get(selection['leaf_root_sha256'], maximum=crop.birth.leaf.MAX); manifest = crop._parse(raw, crop.birth.leaf.MAX)
        _, root_program, _, _, frames, _, raws = crop.birth.leaf._graph(store, manifest)
        value = _declaration(declaration, context, data, manifest, root_program)
        index = source['candidate']['source_root_certificate']['source_bracket']['left_frame_index']; frame = frames[index]
        history = [] if frame['context'] is None else frame['context']['history']
        links = [{**link, 'birth_at': None, 'kind': 'explicit_preexisting_initial_link', 'event_id': None} for link in value['initial_attachments']]
        for kind, rows in [('original_funded_point', history), ('fractional_branch_point', data['records'])]:
            for row in rows:
                inputs = row['inputs']
                links.extend({'leaf_id': event['leaf']['leaf_id'], 'attachment_internode_id': event['attachment_internode_id'],
                    'birth_at': _fraction(inputs['at_elapsed_seconds_exact']), 'kind': kind, 'event_id': event['event_id']} for event in inputs['events'])
        _need([link['leaf_id'] for link in links] == [leaf['leaf_id'] for leaf in data['program']['leaves']], 'ATTACHMENT_HOLD: exact original complete leaf order required')
        crop.birth.leaf._fence(store, manifest, {**raws, 'root': raw})
    return links, value, manifest['source_rights']


def _length(age, curve, identity):
    return point.calculate_internode_length_point(inputs={'input_id': identity, 'origin': 'synthetic',
        'thermal_age_basis': 'since_internode_emergence', 'age_exact': _exact(age,'degC_day'), 'curve': curve})


def _shoot(data, payload, book, birth):
    source_state = book['state']; timeline = source_state['timeline_state']; elapsed = _fraction(payload['at']['elapsed_seconds_exact'])
    at_birth = _fraction(birth['at_elapsed_seconds_exact']); base = F(float(timeline['base_temperature']['value']))
    integral = F(payload['lifetime_integrated_transfers']['indoor_air_temperature_time']['value'])
    birth_integral = F(data['base_lifetime_transfers']['indoor_air_temperature_time']['value'])
    change = (integral-base*elapsed)/86400; shoot_age = _fraction(timeline['age_exact'])+change
    birth_shoot_age = _fraction(timeline['age_exact'])+(birth_integral-base*at_birth)/86400
    threshold = _fraction(birth['threshold_age_exact']); next_threshold = threshold+_fraction(timeline['phyllochron_exact'])
    _need(threshold <= birth_shoot_age <= shoot_age < next_threshold, 'EVENT_HOLD: unresolved or further shoot threshold')
    _need(elapsed >= at_birth, 'TIME_HOLD: current CP precedes numerical organ birth')
    nodes = []
    for node in source_state['internodes']:
        original = node['length_state']; normalized = length.normalize_rational_internode_length_state(state=original)
        _need(normalized == original, 'STATE_HOLD: original canonical stem state required')
        age = _fraction(original['clock_state']['age_exact'])+change
        _need(age >= _fraction(original['clock_state']['age_exact']), 'AGE_HOLD: reversing stored stem age unsupported')
        receipt = _length(age, original['curve'], _digest({'model':VERSION,'source':book['state_sha256'],'id':original['clock_state']['internode_id']}))
        nodes.append({'internode_id':original['clock_state']['internode_id'], 'sequence':node['sequence'], 'kind':'selected_original',
            'development_birth_seconds_exact':deepcopy(original['clock_state']['emerged_elapsed_seconds_exact']),
            'age_exact':_exact(age,'degC_day'), 'curve':deepcopy(original['curve']), 'curve_sha256':receipt['curve_sha256'],
            'length':receipt['length'], 'point_input_sha256':receipt['input_sha256'], 'source_length_state_sha256':_digest(original),
            'initial_anchor':deepcopy(original['anchor'])})
    profile = source_state['emergence_profile']; zero = _length(Fraction(0),profile['curve'],'funded-fractional-emergence-template')
    requested = length._quantity(profile['initial_length'])
    _need(isclose(requested['value'],zero['length']['value'],rel_tol=1e-12,abs_tol=0), 'INITIAL_LENGTH_HOLD: original emergence length required')
    age = (integral-birth_integral-base*(elapsed-at_birth))/86400
    _need(age >= 0, 'AGE_HOLD: new organ age cannot reverse')
    receipt = _length(age,profile['curve'],_digest({'model':VERSION,'candidate':birth['candidate_sha256'],'id':birth['internode_id']}))
    nodes.append({'internode_id':birth['internode_id'],'sequence':birth['sequence'],'kind':'numerical_threshold_birth',
        'development_birth_seconds_exact':deepcopy(birth['development_elapsed_seconds_exact']), 'age_exact':_exact(age,'degC_day'),
        'curve':deepcopy(profile['curve']), 'curve_sha256':receipt['curve_sha256'], 'length':receipt['length'],
        'point_input_sha256':receipt['input_sha256'], 'source_length_state_sha256':None,
        'initial_anchor':{'at_elapsed_seconds_exact':deepcopy(birth['at_elapsed_seconds_exact']), 'age_exact':_exact(Fraction(0),'degC_day'),
            'requested_initial_length':requested,'canonical_initial_length':zero['length']}})
    _need(len(nodes) <= 512 and len({node['internode_id'] for node in nodes}) == len(nodes), 'CAPACITY_HOLD: unique bounded actual organ inventory required')
    return {'internodes':nodes,'shoot_age_exact':_exact(shoot_age,'degC_day'),
        'birth':{**birth,'air_temperature_integral_at_birth':{'value':float(birth_integral),'unit':'degC_s'},
            'shoot_age_at_birth_exact':_exact(birth_shoot_age,'degC_day'),'threshold_overshoot_exact':_exact(birth_shoot_age-threshold,'degC_day')},
        'next_threshold_exact':_exact(next_threshold,'degC_day'), 'tracked_axis_length':{'value':fsum(n['length']['value'] for n in nodes),'unit':'m'}}


def bind_fractional_crop(context, checkpoint, initial_bindings):
    try:
        _fence(); pins = _pins(); data = crop._context(context)
        payload = crop._parse(crop.checkpoint_bytes(context,checkpoint),crop.MAX_CHECKPOINT_BYTES)
        crop._validate(context,data,payload)
        book = _stem_source(context,data['source']); birth = _birth(data['source'],book)
        shoot = _shoot(data,payload,book,birth); links,declaration,rights = _leaf_links(context,data,initial_bindings)
        parents = {n['internode_id']:n for n in shoot['internodes']}; elapsed = _fraction(payload['at']['elapsed_seconds_exact'])
        y = payload['last_confirmed']['state']; count = len(links); leaves = []
        for i,link in enumerate(links):
            _need(link['attachment_internode_id'] in parents, 'ATTACHMENT_HOLD: recorded leaf parent absent from actual coupled shoot')
            parent = parents[link['attachment_internode_id']]; parent_at = _fraction(parent['development_birth_seconds_exact'])
            leaf_at = Fraction(0) if link['birth_at'] is None else link['birth_at']
            _need(parent_at <= book['offset']+leaf_at <= book['offset']+elapsed, 'ATTACHMENT_HOLD: leaf precedes its actual parent')
            leaves.append({**{k:link[k] for k in ('leaf_id','attachment_internode_id','kind','event_id')},
                'birth_at_elapsed_seconds_exact':None if link['birth_at'] is None else _exact(leaf_at,'s'),
                'thermal_age':{'value':y[107+i],'unit':'degC_day'},'area':{'value':y[107+count+i],'unit':'m2'},
                'carbohydrate':{'value':y[107+2*count+i],'unit':crop.birth.point.MASS}})
        total = fsum(leaf['area']['value'] for leaf in leaves); _need(isfinite(total), 'NUMERIC_HOLD: finite tracked leaf area required')
        result = {'model_version':VERSION,'scope':'software_research_only','G0_G4':'not_assessed','R2':'not_approved',
            'claim_scope':'explicit_synthetic_coupled_geometry_not_validated_crop_growth','code_sha256':pins,
            'context_sha256':context.sha256,'checkpoint_sha256':checkpoint.sha256,'at':deepcopy(payload['at']),
            'checkpoint':deepcopy(payload),
            'phase':payload['phase'],'event_sequence':payload['event_sequence'],'output_cursor':payload['output_cursor'],
            'output_prefix_sha256':payload['output_prefix_sha256'],'model_floor_area':deepcopy(data['program']['model_floor_area']),
            'initial_bindings':declaration,'initial_bindings_sha256':_digest(declaration),'source_rights':{'leaf':rights,'stem':book['manifest']['program_rights']},
            'stem_source_state_sha256':book['state_sha256'],'stem_source_result_sha256':book['result_sha256'],
            'stem_program_sha256':book['program_sha256'],'development_origin_utc':book['state']['timeline_state']['started_at'],
            'simulation_start_development_seconds_exact':_exact(book['offset'],'s'),'shoot':shoot,'leaves':leaves,
            'tracked_leaf_area':{'value':total,'unit':'m2'},'derived':deepcopy(payload['last_confirmed']['derived']),
            'new_stem_carbon_allocation':'not_independently_allocated_in_aggregate_stem_pool',
            'initial_leaf_history':'explicit_carry_over_ages_and_links_not_verified_past_emergence',
            'checkpoint_ledger_sha256':_digest({k:v for k,v in payload.items() if 'transfer'in k or 'balance'in k}),
            'checkpoint_validation_RHS_evaluations':1,'past_ODE_or_clock_advances':0}
        _need(len(crop._canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded coupled binding output required')
        _need(_stem_source(context,data['source']) == book and _pins() == pins, 'SOURCE_HOLD: source/code changed before binding return')
        crop._context(context); _fence()
        return deepcopy(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise FractionalStemBindingHold(str(error)) from None
