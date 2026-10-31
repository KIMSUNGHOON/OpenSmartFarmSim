"""Opt-in owned schema4 sources using the existing immutable job-input store."""
from .economic_production_batches import BatchEconomicScenario, OwnedProductionBatch
from .market_source_store import MarketSourceStore, MarketSourceDenied, _KINDS, _install_source_schema

VERSION = 'economic-batch-user-source-v1'
MODELS = {**_KINDS, 'economic_scenario': (BatchEconomicScenario, 'scenario_id', 'scenario_revision'),
          'production_batch': (OwnedProductionBatch, 'batch_id', 'revision')}
TABLE_NAME = 'economic_batch_source_records'


def install_economic_batch_source_schema(conn, schema):
    _install_source_schema(conn, schema, table=TABLE_NAME, version=VERSION,
        kinds=tuple(MODELS), function='reject_economic_batch_source_change',
        trigger='economic_batch_source_immutable')


class EconomicBatchSourceStore(MarketSourceStore):
    MODELS = MODELS
    VERSION = VERSION
    TABLE_NAME = TABLE_NAME

    def __init__(self, dsn, schema, *, principal_provider, runtime_identity):
        super().__init__(dsn, schema, principal_provider=principal_provider, runtime_identity=runtime_identity)
        if not self.runtime_identity[0].economic_batch_source_storage:
            raise ValueError('economic batch source profile is not enabled')

    def _tenant(self, scope):
        scope = {'market_source_read': 'economic_batch_source_read',
                 'market_source_write': 'economic_batch_source_write'}.get(scope, scope)
        return super()._tenant(scope)

    def _read_in_transaction(self, conn, tenant, kind, identity, revision, *, pin=False):
        result = super()._read_in_transaction(conn, tenant, kind, identity, revision, pin=pin)
        if self._tenant('economic_batch_source_read') != tenant:
            raise MarketSourceDenied('economic batch source lookup denied')
        return result

    def get_production_batch(self, batch_id, revision):
        return self._read('production_batch', batch_id, revision)
