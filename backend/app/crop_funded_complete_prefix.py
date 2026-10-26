"""Bind the original confirmed prefix and a complete fractional crop branch."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import fsum, isfinite
from pathlib import Path

from . import crop_funded_fractional_stem_binding as binding
from .crop_morphology_artifact_io import MorphologyBlobStore, _need

VERSION = 'funded-complete-source-prefix-fractional-geometry-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
crop = binding.crop
F = Fraction.from_float


class CompletePrefixHold(ValueError):
    pass


def _pins():
    return {**binding._pins(), 'backend/app/crop_funded_complete_prefix.py': sha256(Path(__file__).read_bytes()).hexdigest()}


def _fence():
    _need(_pins()['backend/app/crop_funded_complete_prefix.py'] == CODE_SHA256, 'CODE_HOLD: original complete-prefix binding required')


def _bounded(value):
    size = len(crop._canonical(value))
    _need(size <= MAX_BYTES, f'CAPACITY_HOLD: bounded complete prefix required ({size}/{MAX_BYTES} bytes)')
    return value


def _view(sample):
    return {name: deepcopy(sample[name]) for name in ('state','derived','curve_residuals','curve_invariant_changes')}


def _snapshot(frame):
    cp = frame['evidence']['checkpoint']
    return frame['snapshot'] if cp is None else cp['last_confirmed']


def _existing_shoot(book, at, transfers):
    timeline = book['state']['timeline_state']; elapsed = binding._fraction(at['elapsed_seconds_exact'])
    integral = F(transfers['indoor_air_temperature_time']['value']); base = F(float(timeline['base_temperature']['value']))
    change = (integral-base*elapsed)/86400; age = binding._fraction(timeline['age_exact'])+change
    _need(change >= 0 and age < binding._fraction(timeline['next_threshold_exact']), 'EVENT_HOLD: unresolved original prefix threshold')
    nodes = []
    for source in book['state']['internodes']:
        original = source['length_state']; normalized = binding.length.normalize_rational_internode_length_state(state=original)
        _need(normalized == original, 'STATE_HOLD: actual canonical original organ required')
        node_age = binding._fraction(original['clock_state']['age_exact'])+change
        receipt = binding._length(node_age,original['curve'],binding._digest({'model':VERSION,'source':book['state_sha256'],'id':original['clock_state']['internode_id']}))
        nodes.append({'internode_id':original['clock_state']['internode_id'],'sequence':source['sequence'],'kind':'selected_original',
            'development_birth_seconds_exact':deepcopy(original['clock_state']['emerged_elapsed_seconds_exact']),
            'age_exact':binding._exact(node_age,'degC_day'),'curve':deepcopy(original['curve']),'curve_sha256':receipt['curve_sha256'],
            'length':receipt['length'],'point_input_sha256':receipt['input_sha256'],'source_length_state_sha256':binding._digest(original),
            'initial_anchor':deepcopy(original['anchor'])})
    return {'internodes':nodes,'shoot_age_exact':binding._exact(age,'degC_day'),'birth':None,
        'next_threshold_exact':deepcopy(timeline['next_threshold_exact']),
        'tracked_axis_length':{'value':fsum(node['length']['value'] for node in nodes),'unit':'m'}}


def _leaves(program, sample, receipts, bases, declaration, book, shoot, elapsed, dt):
    parents = {node['internode_id']:node for node in shoot['internodes']}; y = sample['state']; n = len(program['leaves'])
    root_links = {row['leaf_id']:row['attachment_internode_id'] for row in declaration['initial_attachments']}; result = []
    for i,(leaf,receipt,basis) in enumerate(zip(program['leaves'],receipts,bases,strict=True)):
        initial = receipt['kind'] == 'initial'
        parent_id = root_links[leaf['leaf_id']] if initial else receipt['value']['attachment_internode_id']
        birth = None if initial else dt*basis['step_index']
        _need(parent_id in parents, 'ATTACHMENT_HOLD: original leaf parent absent from actual prefix')
        parent_at = binding._fraction(parents[parent_id]['development_birth_seconds_exact'])
        _need(parent_at <= book['offset']+(Fraction(0) if birth is None else birth) <= book['offset']+elapsed,
              'ATTACHMENT_HOLD: original leaf precedes its parent')
        result.append({'leaf_id':leaf['leaf_id'],'attachment_internode_id':parent_id,
            'kind':'explicit_preexisting_initial_link' if initial else 'original_funded_point',
            'event_id':None if initial else receipt['value']['event_id'],
            'birth_at_elapsed_seconds_exact':None if birth is None else binding._exact(birth,'s'),
            'thermal_age':{'value':y[107+i],'unit':'degC_day'},'area':{'value':y[107+n+i],'unit':'m2'},
            'carbohydrate':{'value':y[107+2*n+i],'unit':crop.birth.point.MASS},'curve_sha256':binding._digest(leaf['curve'])})
    return result


def _frame(at, phase, sequence, cursor, prefix, program, sample, shoot, leaves, evidence, flows, points, ledgers):
    total = fsum(leaf['area']['value'] for leaf in leaves); _need(isfinite(total), 'NUMERIC_HOLD: finite complete leaf area required')
    value = {'at':deepcopy(at),'phase':phase,'event_sequence':sequence,'output_cursor':cursor,'output_prefix_sha256':prefix,
        'program_sha256':binding._digest(program),'shoot':shoot,
        'leaves':[{k:v for k,v in leaf.items() if k not in ('thermal_age','area','carbohydrate')} for leaf in leaves],
        'tracked_leaf_area':{'value':total,'unit':'m2'},'evidence':evidence,
        'quantities_storage':'checkpoint' if evidence['checkpoint'] is not None else 'source_prefix_plus_dense_partial'}
    if evidence['checkpoint'] is None:
        value.update(snapshot=_view(sample),lifetime_integrated_transfers=deepcopy(flows),lifetime_point_transfers=deepcopy(points),ledgers=deepcopy(ledgers))
    return value


def _prefix(context, initial_bindings):
    data = crop._context(context); _need(len(data['records']) == 1, 'SCOPE_HOLD: first fractional context required for original prefix')
    source = data['source']; selection = source['candidate']['selection']; book = binding._stem_source(context,source)
    birth = binding._birth(source,book); left = source['candidate']['source_root_certificate']['source_bracket']['left_frame_index']
    frames = []; dt = F(data['original']['grid_step_seconds'])
    with MorphologyBlobStore(context._leaf_directory,context._access) as store:
        raw = store.get(selection['leaf_root_sha256'],maximum=crop.birth.leaf.MAX); manifest = crop._parse(raw,crop.birth.leaf.MAX)
        _,root_program,_,_,original,_,raws = crop.birth.leaf._graph(store,manifest)
        declaration = binding._declaration(initial_bindings,context,data,manifest,root_program)
        for i,current in enumerate(original[:left+1]):
            cp = current['checkpoint']; descriptor = manifest['samples'][i]; sample = cp['last_confirmed']; program = current['program']
            at = {'time_origin_utc':manifest['time_origin_utc'],'elapsed_seconds_exact':deepcopy(descriptor['elapsed_seconds_exact'])}
            shoot = _existing_shoot(book,at,cp['integrated_transfers'])
            leaves = _leaves(program,sample,current['creation_receipts'],current['creation_bases'],declaration,book,shoot,binding._fraction(at['elapsed_seconds_exact']),dt)
            points = cp.get('point_totals',crop._sum_rows(crop.POINT_UNITS))
            ledgers = {key:cp.get('global_'+key,cp[key]) for key in ('balance_residuals','balance_budgets')}
            cp_raw = store.get(descriptor['checkpoint_sha256'],maximum=crop.birth.leaf.CHECKPOINT_MAX)
            _need(crop._canonical(cp) == cp_raw, 'SOURCE_HOLD: exact original checkpoint representation required')
            frames.append(_frame(at,descriptor['phase'],descriptor['event_sequence'],cp['output_cursor'],cp['output_prefix_sha256'],program,
                sample,shoot,leaves,{'kind':'original_funded_checkpoint','source_frame_index':i,'checkpoint_sha256':descriptor['checkpoint_sha256'],'checkpoint':deepcopy(cp)},
                cp['integrated_transfers'],points,ledgers))
        before = data['branch_initial']; sequence = data['original']['left_checkpoint'].get('event_sequence',0)+1
        before_prefix = crop._prefix(frames[-1]['output_prefix_sha256'],before,sequence,'before_birth')
        flows = {key:deepcopy(data['base_lifetime_transfers'][key]) for key in crop.short._flux_units(source['program'])}
        shoot = binding._shoot(data,{'at':before['at'],'lifetime_integrated_transfers':flows},book,birth)
        current = original[left]; leaves = _leaves(source['program'],before,current['creation_receipts'],current['creation_bases'],declaration,book,shoot,
            binding._fraction(before['at']['elapsed_seconds_exact']),dt)
        balance_data = {**data,'program':source['program'],'records':[],'_latent':context._profiles[-1].values['latent_heat']}
        residuals,budgets = crop._balances(balance_data,before,flows,binding._fraction(before['at']['elapsed_seconds_exact']),0,lifetime=True)
        frames.append(_frame(before['at'],'before_birth',sequence,frames[-1]['output_cursor']+1,before_prefix,source['program'],before,shoot,leaves,
            {'kind':'checked_dense_candidate','candidate_sha256':binding._digest(source['candidate']),'candidate':deepcopy(source['candidate']),
             'checkpoint_sha256':None,'checkpoint':None},flows,crop._point_totals(balance_data,True),{'balance_residuals':residuals,'balance_budgets':budgets}))
        crop.birth.leaf._fence(store,manifest,{**raws,'root':raw})
    basis = {'model_version':VERSION,'scope':'software_research_only','G0_G4':'not_assessed','R2':'not_approved','code_sha256':_pins(),
        'source_selection':deepcopy(selection),'model_floor_area':deepcopy(data['program']['model_floor_area']),
        'stem_source_state_sha256':book['state_sha256'],'development_origin_utc':book['state']['timeline_state']['started_at'],
        'simulation_start_development_seconds_exact':binding._exact(book['offset'],'s'),'initial_bindings':declaration,
        'source_rights':{'leaf':manifest['source_rights'],'stem':book['manifest']['program_rights']},
        'equation_reference':deepcopy(book['manifest']['equation_reference']),
        'new_stem_carbon_allocation':'not_independently_allocated_in_aggregate_stem_pool',
        'initial_leaf_history':'explicit_carry_over_ages_and_links_not_verified_past_emergence'}
    _need(binding._stem_source(context,source) == book, 'SOURCE_HOLD: prefix stem source changed')
    crop._context(context)
    return basis,frames,data


def bind_original_prefix(context, initial_bindings):
    try:
        _fence(); pins = _pins(); basis,frames,_ = _prefix(context,initial_bindings)
        _need(_pins() == pins, 'CODE_HOLD: source changed during prefix binding'); _fence()
        return _bounded({'basis':basis,'status':'confirmed_prefix_only','frames':frames})
    except (OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError) as error:
        raise CompletePrefixHold(str(error)) from None


def _segments(segments):
    _need(type(segments) is list and 1 <= len(segments) <= 511, 'CAPACITY_HOLD: bounded nonempty actual segments required')
    prepared = []; prior = None; prior_data = None; prior_context = None; scalar = 0
    for j,segment in enumerate(segments):
        crop.birth.point._closed(segment,{'context','checkpoints','initial_bindings'})
        context = segment['context']; data = crop._context(context); checkpoints = segment['checkpoints']
        _need(type(checkpoints) is list and 1 <= len(checkpoints) <= 512, 'CAPACITY_HOLD: bounded nonempty actual checkpoints required')
        _need(len(data['records']) == j+1 and (j == 0 or data['records'][:-1] == prior_data['records']), 'EVENT_HOLD: consecutive original point histories required')
        if j:
            _need(all(data[key] == prior_data[key] for key in ('source','original','base_lifetime_transfers','base_prior_budgets','branch_initial')),
                  'SOURCE_HOLD: original common branch basis required')
            record = data['records'][-1]
            _need(record['before_checkpoint_sha256'] == prior.sha256 and record['inputs']['context_sha256'] == prior_context.sha256,
                  'EVENT_HOLD: point must adopt the exact preceding checkpoint/context')
            before_decl = {k:v for k,v in segments[j-1]['initial_bindings'].items() if k != 'context_sha256'}
            after_decl = {k:v for k,v in segment['initial_bindings'].items() if k != 'context_sha256'}
            _need(before_decl == after_decl, 'ATTACHMENT_HOLD: initial bindings cannot change across a branch')
        _need(crop.checkpoint_bytes(context,checkpoints[0]) == crop.start(context)._raw, 'SEQUENCE_HOLD: segment must begin at its original point seed')
        values = []
        for k,cp in enumerate(checkpoints):
            value = crop._parse(crop.checkpoint_bytes(context,cp),crop.MAX_CHECKPOINT_BYTES)
            if k or j:
                previous = prior.value
                _need(value['output_cursor'] == previous['output_cursor']+1, 'SEQUENCE_HOLD: every original cursor required')
                if k:
                    _need(value['segment_steps'] == previous['segment_steps']+1 and value['event_sequence'] == previous['event_sequence']
                          and binding._fraction(value['at']['elapsed_seconds_exact']) > binding._fraction(previous['at']['elapsed_seconds_exact']),
                          'SEQUENCE_HOLD: consecutive original grid checkpoints required')
                else:
                    _need(value['at'] == previous['at'] and value['event_sequence'] == previous['event_sequence']+1,
                          'SEQUENCE_HOLD: same-time point sequence required')
                phase = 'grid_endpoint' if k else 'after_birth'
                _need(value['output_prefix_sha256'] == crop._prefix(previous['output_prefix_sha256'],value['last_confirmed'],value['event_sequence'],phase),
                      'PREFIX_HOLD: original preceding checkpoint prefix required')
            values.append(value); prior = cp; scalar += len(value['last_confirmed']['state'])+2*len(data['program']['leaves'])+8
        prepared.append((segment,data,values)); prior_data,prior_context = data,context
    last = prepared[-1][2][-1]; original = prepared[0][1]['original']
    _need(binding._fraction(last['at']['elapsed_seconds_exact']) == F(original['grid_step_seconds'])*original['grid_step_count'],
          'INCOMPLETE_HOLD: original horizon required')
    return prepared,scalar


def bind_complete_trajectory(segments):
    try:
        _fence(); pins = _pins(); prepared,scalar = _segments(segments)
        first = prepared[0][0]; basis,frames,data = _prefix(first['context'],first['initial_bindings'])
        scalar += sum(len(_snapshot(frame)['state'])+2*len(frame['leaves'])+8 for frame in frames)
        _need(len(frames)+sum(len(item[2]) for item in prepared) <= 512 and scalar <= 32768, 'CAPACITY_HOLD: complete sample budget exceeded')
        previous = frames[-1]
        first_cp = prepared[0][2][0]
        _need(first_cp['output_cursor'] == previous['output_cursor']+1
              and first_cp['output_prefix_sha256'] == crop._prefix(previous['output_prefix_sha256'],first_cp['last_confirmed'],first_cp['event_sequence'],'after_birth'),
              'PREFIX_HOLD: actual dense before/after pair required')
        receipts = []
        for segment,segment_data,values in prepared:
            context = segment['context']
            receipts.append({'context_sha256':context.sha256,'initial_bindings_sha256':binding._digest(segment['initial_bindings']),
                             'first_checkpoint_sha256':segment['checkpoints'][0].sha256,'last_checkpoint_sha256':segment['checkpoints'][-1].sha256})
            for cp,value in zip(segment['checkpoints'],values,strict=True):
                bound = binding.bind_fractional_crop(context,cp,segment['initial_bindings'])
                leaves = [{**leaf,'curve_sha256':binding._digest(program['curve'])} for leaf,program in zip(bound['leaves'],segment_data['program']['leaves'],strict=True)]
                frames.append(_frame(value['at'],value['phase'],value['event_sequence'],value['output_cursor'],value['output_prefix_sha256'],segment_data['program'],
                    value['last_confirmed'],bound['shoot'],leaves,{'kind':'fractional_checkpoint','context_sha256':context.sha256,'checkpoint_sha256':cp.sha256,'checkpoint':deepcopy(value)},
                    value['lifetime_integrated_transfers'],value['lifetime_point_transfers'],
                    {'balance_residuals':value['global_balance_residuals'],'balance_budgets':value['global_balance_budgets']}))
            crop._context(context)
        _need(_pins() == pins, 'CODE_HOLD: source changed during complete binding'); _fence()
        for segment,_,_ in prepared: crop._context(segment['context'])
        return _bounded({'basis':basis,'status':'completed_software_fixture','segment_receipts':receipts,'sample_scalars':scalar,
                         'frames':frames,'current_checkpoint_RHS_evaluations':sum(len(item[2]) for item in prepared),'past_ODE_or_clock_advances':0})
    except (OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError) as error:
        raise CompletePrefixHold(str(error)) from None
