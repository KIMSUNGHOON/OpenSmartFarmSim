"""Sequential metadata discovery through the existing signed organ result reader."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re

from psycopg import sql

from . import crop_result_store as storage
from .crop_result_catalog import (VERSION, SELECTION_VERSION, MAX_CROPS, MAX_LIMIT,
    MAX_PAGE_BYTES, CropResultCatalogHold, _need, _time)
from .thermal_run_store import _canonical, _document

KIND='organ_v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
RESULT_ID=re.compile(r'crop-result-v1:[0-9a-f]{64}\Z')


def _request(kind,farm,limit,before):
    _need(kind==KIND and type(kind) is str and type(limit) is int and 1<=limit<=MAX_LIMIT)
    _need(type(farm) is dict and set(farm)=={'scenario_id','scenario_revision','registration_sha256','crop_id'})
    _need(all(storage._name(farm[k]) for k in ('scenario_id','scenario_revision','crop_id'))
          and type(farm['registration_sha256']) is str and storage.DIGEST.fullmatch(farm['registration_sha256']))
    if before is not None:
        _need(type(before) is dict and set(before)=={'recorded_at','result_id'})
        _need(type(before['recorded_at']) is datetime and before['recorded_at'].tzinfo is not None
              and before['recorded_at'].utcoffset() is not None
              and type(before['result_id']) is str and RESULT_ID.fullmatch(before['result_id']))


class OrganCropResultCatalog:
    def __init__(self,store):
        try:
            _need(type(store) is storage.CropResultStore)
            self.store=store
            self._fixed=(store,store._pointers())
            self._binding()
        except Exception:
            raise CropResultCatalogHold('stored organ catalog unavailable') from None

    def _binding(self):
        _need(type(self.store) is storage.CropResultStore
              and (self.store,self.store._pointers())==self._fixed
              and sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256)
        self.store._guard_binding()

    def _registration(self,tenant,farm):
        self._binding();self.store._guard(tenant)
        registration=self.store.farms.read_registration(tenant,farm['scenario_id'],
            farm['scenario_revision'],farm['registration_sha256'])
        _need(registration['scenario_sha256']==farm['registration_sha256']
              and registration['farm'].scenario_id==farm['scenario_id']
              and registration['farm'].scenario_revision==farm['scenario_revision']
              and ('crop_id' not in farm or any(c.crop_id==farm['crop_id'] for c in registration['farm'].crops)))
        self.store._guard(tenant)
        return registration

    @contextmanager
    def open_farm_selection(self,tenant,farm_ref):
        try:
            _need(type(farm_ref) is dict and set(farm_ref)=={'scenario_id','scenario_revision','registration_sha256'})
            _need(all(storage._name(farm_ref[k]) for k in ('scenario_id','scenario_revision'))
                  and type(farm_ref['registration_sha256']) is str and storage.DIGEST.fullmatch(farm_ref['registration_sha256']))
            farm=deepcopy(farm_ref);registration=deepcopy(self._registration(tenant,farm))
            crops=registration['farm'].crops
            _need(len(crops)<=MAX_CROPS and len({c.crop_id for c in crops})==len(crops))
            items=[{'crop_id':c.crop_id,'batch_id':c.batch_id,'species':c.species,'variety':c.variety,
                'occupancy':{'start':_time(c.occupancy.start),'end':_time(c.occupancy.end)},
                'profile_status':c.profile_status,'origin':c.provenance.origin,
                'evidence_level':c.provenance.evidence_level} for c in sorted(crops,key=lambda c:c.crop_id)]
            page={'version':SELECTION_VERSION,'scope':'registered_user_inputs_only','farm':farm,
                'items':items,'selection_validation_required':True,'rights_or_gate_approval':False}
            _need(len(_canonical(page))<=MAX_PAGE_BYTES)
            _need(self._registration(tenant,farm)==registration)
            yield deepcopy(page)
            _need(self._registration(tenant,farm)==registration)
        except PermissionError:
            raise
        except Exception:
            raise CropResultCatalogHold('stored organ farm selection unavailable') from None

    def _rows(self,tenant,farm,limit,before):
        args=[tenant,farm['scenario_id'],farm['scenario_revision'],farm['registration_sha256'],farm['crop_id']]
        cursor=sql.SQL('')
        if before is not None:
            cursor=sql.SQL(' AND (recorded_at,result_id)<(%s,%s)')
            args.extend((before['recorded_at'].astimezone(timezone.utc),before['result_id']))
        args.append(limit+1)
        with self.store.jobs.connect() as conn:
            return conn.execute(sql.SQL('SELECT result_id,recorded_at FROM {} WHERE tenant_id=%s '
                'AND scenario_id=%s AND scenario_revision=%s AND registration_sha256=%s '
                "AND convert_from(payload_raw,'UTF8')::jsonb #>> '{{request,farm,crop_id}}'=%s{} "
                'ORDER BY recorded_at DESC,result_id DESC LIMIT %s').format(
                    self.store.jobs._table('crop_research_results'),cursor),args).fetchall()

    def _item(self,tenant,farm,row):
        _need(type(row['result_id']) is str and RESULT_ID.fullmatch(row['result_id']))
        record=self.store.get(tenant,row['result_id'],farm)
        _need(record is not None and record['result_id']==row['result_id']
              and record['recorded_at']==row['recorded_at']
              and record['payload_sha256']==sha256(record['payload_raw']).hexdigest())
        packet=_document(record['payload_raw'],max_size=storage.MAX_PACKET_BYTES)
        request,result=packet['request'],packet['result']
        _need(request['farm']==farm and result['status'] in ('completed','hold')
              and type(result['samples']) is list and type(result['events']) is list)
        item={'result_id':record['result_id'],'recorded_at':_time(record['recorded_at']),
            'calculation_status':result['status'],'claim_scope':'synthetic_crop_math_only',
            'study_id':request['study_id'],'revision':request['revision'],
            'period':{'start':request['program']['segments'][0]['start'],
                      'end':request['program']['segments'][-1]['end']},
            'sample_count':len(result['samples']),'event_count':len(result['events'])}
        return item,record['payload_sha256']

    @contextmanager
    def open(self,tenant,kind,farm_ref,*,limit=10,before=None):
        try:
            _request(kind,farm_ref,limit,before)
            farm=deepcopy(farm_ref);before=deepcopy(before)
            registration=deepcopy(self._registration(tenant,farm))
            rows=self._rows(tenant,farm,limit,before)
            _need(len(rows)<=limit+1)
            keys=[(r['recorded_at'],r['result_id']) for r in rows]
            _need(keys==sorted(keys,reverse=True) and len(set(keys))==len(keys)
                  and (before is None or all(k<(before['recorded_at'],before['result_id']) for k in keys)))
            def inspect():
                items=[]
                for row in rows:
                    items.append(self._item(tenant,farm,row))
                return items
            snapshots=inspect()
            items=[item for item,_ in snapshots]
            cursor={k:items[limit-1][k] for k in ('recorded_at','result_id')} if len(items)>limit else None
            page={'version':VERSION,'scope':'stored_research_metadata_only','kind':KIND,'farm':farm,
                'items':items[:limit],'next_cursor':cursor,
                'selection_validation_required':True,'rights_or_gate_approval':False}
            _need(len(_canonical(page))<=MAX_PAGE_BYTES)
            def recheck():
                _need(self._registration(tenant,farm)==registration)
                _need(inspect()==snapshots)
                _need(self._registration(tenant,farm)==registration)
            recheck()
            yield deepcopy(page)
            recheck()
        except PermissionError:
            raise
        except Exception:
            raise CropResultCatalogHold('stored organ catalog unavailable') from None
