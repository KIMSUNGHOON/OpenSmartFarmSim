"""Explicit initial stock lineage; crop-stem-root-initial-binding-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from . import crop_stem_root_stock_continuation as crop
from . import crop_leaf_carbon_stock_artifact_reader as carbon
from . import crop_rational_morphology_artifact_reader as stem
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore

VERSION = 'explicit-stem-root-initial-source-binding-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
BASIS = 'one_tracked_shoot_on_declared_model_floor_research_v1'


class InitialStemCarbonBindingHold(MorphologyArtifactHold):
    def __init__(self, reason, *, evidence=None):
        super().__init__(reason)
        self.hold_evidence = deepcopy(evidence)


def _need(condition, reason):
    if not condition: raise InitialStemCarbonBindingHold(reason)


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: bounded initial source binding required')
    return raw


def _digest(value): return sha256(_canonical(value)).hexdigest()


def _pins():
    root = Path(__file__).resolve().parents[2]
    paths = dict.fromkeys((*carbon.SOURCE_PATHS, *stem.SOURCE_PATHS,
        'backend/app/crop_stem_root_initial_binding.py', 'backend/app/crop_stem_root_stock_continuation.py',
        'backend/app/crop_stem_root_stock_dynamics.py', 'backend/app/crop_stem_root_carbon_stock_rhs.py',
        'backend/app/crop_stem_root_partition_climate_rhs.py', 'backend/app/crop_stem_root_carbon_partition.py'))
    return {name:sha256((root/name).read_bytes()).hexdigest() for name in paths}


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256, 'CODE_HOLD: original initial binding source required')


def _declaration(value):
    carbon._closed(value, {'schema_version','input_id','origin','context_sha256','crop_root_sha256','crop_initial_state_sha256',
        'stem_root_sha256','stem_start_index','stem_source_state_sha256','time_origin_utc','model_floor_area','tracking_basis','rights','reviewer'})
    raw = _canonical(value); d = json.loads(raw)
    _need(d['schema_version'] == 'stem-root-initial-source-binding-input-v1' and d['origin'] == 'synthetic',
          'SCOPE_HOLD: explicit synthetic initial binding required')
    for key in ('input_id','reviewer'): carbon._id(d[key])
    for key in ('context_sha256','crop_root_sha256','crop_initial_state_sha256','stem_root_sha256','stem_source_state_sha256'): carbon._hash(d[key])
    carbon._utc(d['time_origin_utc']); floor = crop.short.stock.part._number(d['model_floor_area'],'m2_floor')
    _need(floor > 0, 'BASIS_HOLD: positive declared footprint required')
    rights = d['rights']; carbon._closed(rights, {'declaration_id','revision','declared_at_utc','ownership_asserted','access','store','use','transform','display','redistribute'})
    for key in ('declaration_id','revision'): carbon._id(rights[key])
    carbon._utc(rights['declared_at_utc'])
    _need(all(rights[k] is True for k in ('ownership_asserted','access','store','use','transform','display')) and type(rights['redistribute']) is bool,
          'RIGHTS_HOLD: explicit input rights required')
    basis = d['tracking_basis']; carbon._closed(basis, {'kind','shoot_id','model_floor_area','tracked_shoot_count'})
    carbon._id(basis['shoot_id']); carbon._closed(basis['tracked_shoot_count'], {'value','unit'})
    _need(basis['kind'] == BASIS and type(basis['tracked_shoot_count']['value']) is int and basis['tracked_shoot_count'] == {'value':1,'unit':'tracked_shoot'},
          'BASIS_HOLD: one explicit tracked shoot mapping required')
    crop.short.stock.part._number(basis['model_floor_area'],'m2_floor')
    _need(basis['model_floor_area'] == d['model_floor_area'], 'BASIS_HOLD: consistent declared footprint required')
    return d,raw


def _stem_source(store, directory, access, root, index, pins):
    m = stem._load_manifest(store,root)
    _need(m['code_sha256'] == {name:pins[name] for name in stem.SOURCE_PATHS}, 'CODE_HOLD: current original stem source required')
    _need(type(index) is int and -1 <= index < len(m['samples']), 'INDEX_HOLD: actual selected stem index required')
    program_raw = store.get(m['program_sha256'],maximum=stem.PROGRAM_MAX); program = stem._parse(program_raw,stem.PROGRAM_MAX)
    result_sha = result_raw = None
    if index == -1:
        state = program['initial_state']; state_sha = m['initial_state_sha256']
    else:
        dto = stem.read_rational_morphology_frame(directory,access,root,index=index); desc = m['samples'][index]
        result_sha = desc['result_sha256']; result_raw = store.get(result_sha,maximum=stem.RESULT_MAX)
        state = stem._parse(result_raw,stem.RESULT_MAX)['state']; state_sha = desc['state_sha256']
        _need(dto['result_sha256'] == result_sha and dto['at'] == state['timeline_state']['at'], 'SOURCE_HOLD: same selected stem result required')
    stem._state(state); _need(_digest(state) == state_sha, 'SOURCE_HOLD: actual stem state digest required')
    _need(all(m['program_rights'][k] is True for k in ('use','display')), 'RIGHTS_HOLD: original stem grants required')
    return m,state,state_sha,result_sha,program_raw,result_raw


def _balance(source, values, unit):
    original = crop.short.stock.part._number(source,unit)
    exact = sum((Fraction.from_float(float(v)) for v in values),Fraction(0))
    total = crop.short.stock.part._normal(float(exact)); residual = Fraction.from_float(original)-exact
    return {'source':{'value':original,'unit':unit}, 'declared_once_rounded_sum':{'value':total,'unit':unit},
            'exact_signed_residual':{'numerator':str(residual.numerator),'denominator':str(residual.denominator),'unit':unit},
            'once_rounded_matches_source':total == original}


def _without_stem(program, *, individual):
    result = deepcopy(program)
    if individual:
        result.pop('stem_root_stock_policy'); result.pop('stem_root_compartments')
    else:
        result['scenario']['plant_state'].pop('stem_root'); result['scenario']['removals'].pop('stem_root')
    return result


def bind_initial_stem_carbon(context, crop_directory, stem_directory, access, *, crop_root_sha256,
                            stem_root_sha256, stem_start_index, declaration):
    try:
        _fence(); pins = _pins(); p,seed,manifest = crop._context(context); d,raw = _declaration(declaration)
        carbon._hash(crop_root_sha256); carbon._hash(stem_root_sha256)
        _need(type(stem_start_index) is int and stem_start_index >= -1 and type(d['stem_start_index']) is int and d['stem_start_index'] == stem_start_index,
              'INDEX_HOLD: explicit original selected index required')
        _need(d['context_sha256'] == context.root_sha256 and d['crop_root_sha256'] == crop_root_sha256 and d['stem_root_sha256'] == stem_root_sha256,
              'SOURCE_HOLD: declaration must bind these original sources')
        captured_context = (context._request,context._program,context._seed,context._manifest)
        with MorphologyBlobStore(crop_directory,access) as cs, MorphologyBlobStore(stem_directory,access) as ss:
            root_raw = cs.get(crop_root_sha256,maximum=carbon.MAX); cm = carbon._parse(root_raw,carbon.MAX)
            inputs,original,old_manifest,old_seed,checkpoints,raws = carbon._graph(cs,cm); raws['root'] = root_raw
            old_state = checkpoints[0]['last_confirmed']['state']
            _need(_digest(old_state) == cm['initial_state_sha256'] == d['crop_initial_state_sha256'], 'SOURCE_HOLD: independent original initial crop state required')
            sm,state,state_sha,result_sha,stem_program_raw,result_raw = _stem_source(ss,stem_directory,access,stem_root_sha256,stem_start_index,pins)
            timeline = state['timeline_state']
            _need(state_sha == d['stem_source_state_sha256'] and timeline['at'] == cm['time_origin_utc'] == d['time_origin_utc'],
                  'TIME_HOLD: actual stem selection and original crop epoch must match')
            _need(d['tracking_basis']['shoot_id'] == timeline['shoot_id'], 'BASIS_HOLD: actual selected shoot required')
            _need(p['model_floor_area'] == original['model_floor_area'] == d['model_floor_area'], 'BASIS_HOLD: original crop and declared inventory footprint required')
            _need(manifest['identity']['profile_sha256'] == {name:cm['sources'][name+'_profile']['sha256'] for name in crop.PROFILE_NAMES},
                  'PROFILE_HOLD: same original crop profiles required')
            rows = p['stem_root_compartments']; nodes = state['internodes']
            ids = [n['length_state']['clock_state']['internode_id'] for n in nodes]
            _need([r['compartment_id'] for r in rows if r['kind']=='internode'] == ids and
                  len([r for r in rows if r['kind']=='root_system']) == 1 and
                  all(r['compartment_id'] not in ids for r in rows if r['kind']=='root_system'),
                  'INVENTORY_HOLD: complete ordered actual internodes and separate root required')
            balance = {'carbon':_balance({'value':old_state[1],'unit':crop.short.stock.part.source.MASS_UNIT},
                                        [r['initial_carbon']['value'] for r in rows],crop.short.stock.part.source.MASS_UNIT),
                       'removal':_balance(original['scenario']['removals']['stem_root'],
                                         [r['carbon_removal']['value'] for r in rows],crop.short.stock.part.source.RATE_UNIT)}
            if not all(v['once_rounded_matches_source'] for v in balance.values()):
                raise InitialStemCarbonBindingHold('CARBON_BALANCE_HOLD: explicit unassigned or overallocated initial inventory/removal',evidence=balance)
            _need(_canonical(_without_stem(json.loads(context._request),individual=True)) == _canonical(_without_stem(json.loads(raws['request']),individual=False)) and
                  _canonical(_without_stem(p,individual=True)) == _canonical(_without_stem(original,individual=False)),
                  'STATE_HOLD: original remaining request/program must be preserved')
            n = len(p['leaves']); offset = 106+3*n
            projected = [seed['state'][0],balance['carbon']['declared_once_rounded_sum']['value'],*seed['state'][1:offset]]
            _need(_canonical(projected) == _canonical(old_state) and seed['initial_area_receipts'] == old_seed['initial_area_receipts'] and
                  seed['evaluation']['curve_residuals'] == old_seed['evaluation']['curve_residuals'],
                  'STATE_HOLD: original initial state and area receipts must be preserved')
            rights = {'crop':deepcopy(cm['source_rights']), 'stem':deepcopy(sm['program_rights']), 'declaration':deepcopy(d['rights'])}
            result = {'model_version':VERSION,'code_sha256':CODE_SHA256,'source_code_sha256':pins,
                'scope':'software_research_only','claim_scope':'synthetic_initial_stored_source_identity_and_declared_footprint_binding_only',
                'time_kind':'synthetic_model_clock_not_observation',
                'G0_G4':'not_assessed','context_sha256':context.root_sha256,'context_manifest':deepcopy(manifest),
                'declaration':deepcopy(d),'declaration_sha256':sha256(raw).hexdigest(),
                'crop_selection':{'root_sha256':crop_root_sha256,'sample_index':0,'state_sha256':cm['initial_state_sha256'],
                    'checkpoint_sha256':cm['samples'][0]['checkpoint_sha256'],'program_sha256':cm['sources']['program']['sha256'],
                    'request_sha256':cm['sources']['request']['sha256'],'seed_sha256':cm['sources']['seed']['sha256'],
                    'context_sha256':cm['context_sha256'],'time_origin_utc':cm['time_origin_utc']},
                'stem_selection':{'root_sha256':stem_root_sha256,'index':stem_start_index,'program_sha256':sm['program_sha256'],
                    'state_sha256':state_sha,'result_sha256':result_sha,'source_state':deepcopy(state)},
                'initial_inventory':deepcopy(rows),'inventory_sha256':_digest(rows),'balance':balance,
                'basis_receipt':{'native_stem_floor_basis':False,'tracking_declaration':deepcopy(d['tracking_basis']),
                    'perplant_mass_conversion':'not_performed','biological_density_validation':'not_assessed'},
                'source_rights':rights,'redistribution_authorized':all(v['redistribute'] is True for v in rights.values()),
                'initialization_scope':'identity_and_declared_basis_only_no_C_from_geometry','growth_RHS_evaluations':0}
            result['calculation_sha256'] = _digest(result); _canonical(result)
            carbon._fence(cs,cm,raws)
            _need(stem._load_manifest(ss,stem_root_sha256) == sm and ss.get(sm['program_sha256'],maximum=stem.PROGRAM_MAX) == stem_program_raw,
                  'SOURCE_HOLD: original stem program/rights changed before return')
            if result_sha is not None:
                _need(ss.get(result_sha,maximum=stem.RESULT_MAX) == result_raw, 'SOURCE_HOLD: selected stem state changed before return')
            _need(crop._context(context) == (p,seed,manifest) and captured_context == (context._request,context._program,context._seed,context._manifest),
                  'CONTEXT_HOLD: initial context changed before return')
            _need(_pins() == pins, 'CODE_HOLD: initial binding dependencies changed'); _fence()
            return deepcopy(result)
    except InitialStemCarbonBindingHold:
        raise
    except (MorphologyArtifactHold,crop.ContinuationRejected,OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError) as error:
        raise InitialStemCarbonBindingHold(str(error)) from None
