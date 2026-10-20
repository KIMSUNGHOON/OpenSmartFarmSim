from contextlib import nullcontext
from app import crop_greenhouse_solar_execution_query as query
SOURCE='''def _current(self, tenant, value, raw, binding_raw):
    self._guard(tenant)
    directory, evidence = self.checkpoints.admission._resolve(tenant, value['request'])
    farms = self.server.binding.farms
    ref = value['request']['farm']
    scope = (farms.registration_read_scope(tenant, ref['scenario_id'], ref['scenario_revision'],
        ref['registration_sha256']) if farms._registration_read.get() is None else nullcontext())
    with scope:
        self.server.binding.current(tenant, raw, directory, evidence, binding_raw, write=False)
    self._guard(tenant)
'''
def install(patch):
    scratch={}
    exec(compile(SOURCE,'private-query-current-registration','exec'),query.__dict__,scratch)
    patch.setattr(query,'nullcontext',nullcontext,raising=False)
    patch.setattr(query.SolarExecutionQuery,'_current',scratch['_current'])
