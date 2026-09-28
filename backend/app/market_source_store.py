"""Immutable typed user assumptions bound to actual deterministic job input bytes."""

from hashlib import sha256
from uuid import UUID

from psycopg import sql

from .economic_contracts import (EconomicScenario, OwnedEconomicRecord,
    OwnedScenarioPin, OwnedSettlementRecord, PriorBatchCostRecord)
from .jobs import canonical_input_bytes, MAX_INPUT_BYTES
from .market_scenario import JointShock, JointShockPin, InputRights, Applicability
from .market_runtime import connect_market, validate_market_identity


VERSION = 'market-user-source-v1'
_KINDS = {
    'economic_scenario': (EconomicScenario, 'scenario_id', 'scenario_revision'),
    'economic_input': (OwnedEconomicRecord, 'input_id', 'revision'),
    'joint_shock': (JointShock, 'shock_id', 'revision'),
    'input_rights': (InputRights, 'input_id', 'revision'),
    'settlement_applicability': (Applicability, 'binding_id', 'revision'),
    'settlement_evidence': (OwnedSettlementRecord, 'settlement_ref', 'revision'),
    'prior_batch_cost': (PriorBatchCostRecord, 'cost_ref', None),
}


def install_market_source_schema(conn, schema):
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.market_source_records (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            kind text NOT NULL CHECK (kind IN ('economic_scenario','economic_input',
                'joint_shock','input_rights','settlement_applicability',
                'settlement_evidence','prior_batch_cost')),
            record_id text NOT NULL CHECK (length(record_id) BETWEEN 1 AND 200),
            revision text NOT NULL CHECK (length(revision) BETWEEN 1 AND 200),
            job_id uuid NOT NULL,
            payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND 65536),
            payload_sha256 char(64) NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{{64}}$'),
            store_version text NOT NULL CHECK (store_version='market-user-source-v1'),
            admission_kind text NOT NULL CHECK (admission_kind='contract_valid_user_assumption'),
            admitted_by text NOT NULL CHECK (length(admitted_by) BETWEEN 1 AND 63),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, kind, record_id, revision),
            FOREIGN KEY (tenant_id, job_id) REFERENCES {}.jobs (tenant_id, job_id),
            CHECK (payload_sha256=encode(sha256(payload_raw),'hex'))
        )
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_market_source_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'market user source is immutable'; END
        $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER market_source_immutable BEFORE UPDATE OR DELETE ON {}.market_source_records
        FOR EACH ROW EXECUTE FUNCTION {}.reject_market_source_change()
    """).format(namespace, namespace))


def _name(value):
    return (type(value) is str and 1 <= len(value) <= 200 and value == value.strip()
            and all(ord(char) >= 32 for char in value))


class MarketSourceStore:
    def __init__(self, dsn, schema, *, principal_provider, runtime_identity):
        try:
            validate_market_identity(schema, runtime_identity, calculation=True, source_storage=True)
            if runtime_identity is None or not callable(principal_provider) or type(dsn) is not str or not dsn:
                raise ValueError()
        except ValueError:
            raise ValueError('market source binding rejected') from None
        self.dsn, self.schema = dsn, schema
        self.runtime_identity = runtime_identity
        self._principal_provider = principal_provider

    def connect(self):
        return connect_market(self.dsn, self.runtime_identity)

    def _table(self, name):
        return sql.SQL('{}.{}').format(sql.Identifier(self.schema), sql.Identifier(name))

    def _tenant(self, scope):
        try:
            principal = self._principal_provider()
            scopes = principal.get('scopes') if type(principal) is dict else None
            if (type(principal) is dict and principal.get('authenticated') is True and
                    _name(principal.get('tenant_id')) and type(scopes) in (list, tuple, set, frozenset)
                    and all(type(item) is str for item in scopes) and scope in scopes):
                return principal['tenant_id']
        except Exception:
            pass
        return None

    def tenant_is_authenticated(self, tenant):
        return _name(tenant) and self._tenant('market_source_read') == tenant

    @staticmethod
    def _model(kind, tenant, raw):
        try:
            if type(kind) is not str or kind not in _KINDS or type(raw) is not bytes or not 1 <= len(raw) <= MAX_INPUT_BYTES:
                raise ValueError()
            model_type, identity_field, revision_field = _KINDS[kind]
            model = model_type.model_validate_json(raw)
            identity = getattr(model, identity_field)
            revision = getattr(model, revision_field) if revision_field else 'single'
            if (model.tenant_id != tenant or not _name(identity) or not _name(revision) or
                    canonical_input_bytes(model.model_dump(mode='json')) != raw):
                raise ValueError()
            if kind == 'economic_scenario' and (model.market_context.kind != 'unavailable' or
                    model.scenario_market_context.kind != 'unavailable'):
                raise ValueError()
            return model, identity, revision
        except Exception:
            raise ValueError('market source input rejected') from None

    def _job_input(self, conn, tenant, job_id):
        row = conn.execute(sql.SQL('SELECT stage,input_bytes,input_sha256 FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(self._table('jobs')), (tenant, job_id)).fetchone()
        if (row is None or row['stage'] not in ('collection', 'simulation') or
                type(row['input_bytes']) is not bytes or sha256(row['input_bytes']).hexdigest() != row['input_sha256']):
            raise ValueError('market source input rejected')
        return row['input_bytes']

    def _verified(self, conn, row):
        model, identity, revision = self._model(row['kind'], row['tenant_id'], row['payload_raw'])
        if (row['store_version'] != VERSION or row['admission_kind'] != 'contract_valid_user_assumption' or
                row['admitted_by'] != self.runtime_identity[0].roles['authority'] or
                (identity, revision) != (row['record_id'], row['revision']) or
                sha256(row['payload_raw']).hexdigest() != row['payload_sha256'] or
                self._job_input(conn, row['tenant_id'], row['job_id']) != row['payload_raw']):
            raise ValueError('market source input rejected')
        return model

    def adopt_job(self, tenant, kind, job_id):
        if not _name(tenant) or self._tenant('market_source_write') != tenant:
            raise ValueError('market source admission denied')
        try:
            if type(job_id) is not str or str(UUID(job_id)) != job_id:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise ValueError('market source input rejected') from None
        with self.connect() as conn:
            raw = self._job_input(conn, tenant, job_id)
            _, identity, revision = self._model(kind, tenant, raw)
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id,kind,record_id,revision,job_id,payload_raw,
                    payload_sha256,store_version,admission_kind,admitted_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'contract_valid_user_assumption',current_user)
                ON CONFLICT (tenant_id,kind,record_id,revision) DO NOTHING
            """).format(self._table('market_source_records')),
                (tenant, kind, identity, revision, job_id, raw, sha256(raw).hexdigest(), VERSION))
            row = self._select(conn, tenant, kind, identity, revision)
            if row is None or row['payload_raw'] != raw:
                raise ValueError('market source version conflict')
            model = self._verified(conn, row)
        return model.model_dump(mode='python')

    def _select(self, conn, tenant, kind, identity, revision):
        return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s')
            .format(self._table('market_source_records')), (tenant, kind, identity, revision)).fetchone()

    def _read(self, kind, identity, revision, *, pin=False):
        tenant = self._tenant('market_source_read')
        if tenant is None or not _name(identity) or not _name(revision):
            return None
        with self.connect() as conn:
            row = self._select(conn, tenant, kind, identity, revision)
            if row is None:
                return None
            model = self._verified(conn, row)
        if pin and kind == 'economic_scenario':
            return OwnedScenarioPin(tenant_id=tenant, scenario_id=identity, scenario_revision=revision,
                decision_at=model.decision_at, payload_sha256=row['payload_sha256'],
                immutable_job_input_ref=str(row['job_id']), immutable_job_input_sha256=row['payload_sha256'],
                immutable=True).model_dump(mode='python')
        if pin and kind == 'joint_shock':
            return JointShockPin(tenant_id=tenant, shock_id=identity, revision=revision,
                sha256=row['payload_sha256'], immutable=True).model_dump(mode='python')
        return model.model_dump(mode='python')

    def get_economic_scenario(self, scenario_id, revision):
        return self._read('economic_scenario', scenario_id, revision)

    def get_economic_scenario_pin(self, scenario_id, revision):
        return self._read('economic_scenario', scenario_id, revision, pin=True)

    def get_economic_input(self, input_id, revision):
        return self._read('economic_input', input_id, revision)

    def get_joint_shock(self, shock_id, revision):
        return self._read('joint_shock', shock_id, revision)

    def get_joint_shock_pin(self, shock_id, revision):
        return self._read('joint_shock', shock_id, revision, pin=True)

    def get_input_rights(self, input_id, revision):
        return self._read('input_rights', input_id, revision)

    def get_settlement_applicability(self, binding_id, revision):
        return self._read('settlement_applicability', binding_id, revision)

    def get_settlement_evidence(self, settlement_ref, revision):
        return self._read('settlement_evidence', settlement_ref, revision)

    def get_prior_batch_cost(self, cost_ref):
        return self._read('prior_batch_cost', cost_ref, 'single')
