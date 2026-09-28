"""Versioned synthetic thermal execution intents; registration grants no gate."""

from hashlib import sha256
import json
import re
from typing import Literal

from pydantic import Field
from psycopg import sql

from .economic_contracts import untrusted_data
from .jobs import canonical_input_bytes
from .market import UnavailableMarketContext
from .market_hold_store import MarketHoldStore, _time
from .provenance import FrozenContract
from .runtime_roles import RuntimeLoginPolicy, NAME
from .thermal_run_store import ThermalRunStore


IDENTIFIER = r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$'


class ThermalScenario(FrozenContract):
    schema_version: Literal['thermal-scenario-v1']
    scenario_id: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_revision: str = Field(pattern=IDENTIFIER, max_length=200)
    tenant_id: str = Field(pattern=IDENTIFIER, max_length=200)
    snapshot_id: str = Field(pattern=r'^thermal-snapshot-v1:[0-9a-f]{64}$', min_length=84, max_length=84)
    decision_context_id: str = Field(pattern=IDENTIFIER, max_length=200)
    market_context: UnavailableMarketContext
    zone_id: str = Field(pattern=IDENTIFIER, max_length=200)
    goal_id: Literal['historical-thermal-replay']
    model_version: Literal['thermal-v1']
    parameter_set_version: Literal['synthetic-thermal-parameters-v1']
    origin: Literal['user']
    evidence_level: Literal['assumed']


class ThermalScenarioHold(ValueError):
    pass


class ThermalScenarioConflict(ThermalScenarioHold):
    pass


def install_thermal_scenario_schema(conn, schema):
    """Provisioner-only, before explicit v6 grants; runtime never creates objects."""
    if type(schema) is not str or not NAME.fullmatch(schema):
        raise ValueError('invalid scenario schema')
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL('''
        CREATE TABLE {}.thermal_scenarios (
            tenant_id text NOT NULL,
            scenario_id text NOT NULL CHECK (length(scenario_id) BETWEEN 1 AND 200),
            revision text NOT NULL CHECK (length(revision) BETWEEN 1 AND 200),
            snapshot_id text NOT NULL,
            decision_context_id text NOT NULL,
            payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND 4096),
            payload_sha256 char(64) NOT NULL CHECK (payload_sha256=encode(sha256(payload_raw),'hex')),
            pins_raw bytea NOT NULL CHECK (octet_length(pins_raw) BETWEEN 1 AND 1024),
            registered_by text NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, scenario_id, revision),
            FOREIGN KEY (tenant_id, snapshot_id) REFERENCES {}.thermal_input_snapshots (tenant_id,snapshot_id),
            FOREIGN KEY (tenant_id,snapshot_id,decision_context_id)
                REFERENCES {}.decision_contexts (tenant_id,snapshot_id,decision_context_id)
        )
    ''').format(namespace, namespace, namespace))
    conn.execute(sql.SQL('''
        CREATE FUNCTION {}.reject_thermal_scenario_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'thermal scenario is immutable'; END
        $$
    ''').format(namespace))
    conn.execute(sql.SQL('''
        CREATE TRIGGER thermal_scenario_immutable BEFORE UPDATE OR DELETE ON {}.thermal_scenarios
        FOR EACH ROW EXECUTE FUNCTION {}.reject_thermal_scenario_change()
    ''').format(namespace, namespace))


class ThermalScenarioStore:
    def __init__(self, runs, holds):
        self.runs, self.holds = runs, holds
        self._binding()
        self.dsn, self.schema, self.runtime_identity = runs.dsn, runs.schema, runs.runtime_identity

    def _binding(self):
        binding = getattr(self.runs, 'runtime_identity', None)
        if (type(self.runs) is not ThermalRunStore or type(self.holds) is not MarketHoldStore or
                type(binding) is not tuple or len(binding) != 2 or
                type(binding[0]) is not RuntimeLoginPolicy or binding[1] != 'authority' or
                binding[0].thermal_scenario_storage is not True or binding[0].schema != self.runs.schema or
                self.holds.runtime_identity != binding or self.holds.schema != self.runs.schema or
                type(self.runs.dsn) is not str or not self.runs.dsn or self.holds.dsn != self.runs.dsn or
                self.holds._context_store is not self.runs or
                not callable(self.runs._principal_provider) or
                self.holds._principal_provider is not self.runs._principal_provider):
            raise ThermalScenarioHold('thermal scenario binding rejected')
        if hasattr(self, 'dsn') and (self.dsn != self.runs.dsn or self.schema != self.runs.schema or
                                     self.runtime_identity != binding):
            raise ThermalScenarioHold('thermal scenario binding rejected')

    def connect(self):
        self._binding()
        try:
            return self.runs.connect()
        except Exception:
            raise ThermalScenarioHold('thermal scenario login rejected') from None

    def _table(self):
        return sql.SQL('{}.thermal_scenarios').format(sql.Identifier(self.schema))

    @staticmethod
    def _model(raw):
        try:
            if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
                raise ValueError()
            model = ThermalScenario.model_validate_json(raw)
            if canonical_input_bytes(model.model_dump(mode='json')) != raw:
                raise ValueError()
            return model
        except Exception:
            raise ThermalScenarioHold('thermal scenario input rejected') from None

    def _references(self, model):
        self._binding()
        try:
            snapshot = self.runs.get_snapshot(model.tenant_id, model.snapshot_id)
            context = self.runs.get_decision_context(model.tenant_id, model.snapshot_id, model.decision_context_id)
            hold = self.holds.get_market_hold_report(model.market_context.hold_report_id)
            if snapshot is None or context is None or hold is None:
                raise ValueError()
            manifest, weather, thermal = (json.loads(snapshot[key]) for key in
                                         ('manifest_raw', 'weather_raw', 'thermal_raw'))
            if (manifest.get('claim_scope') != 'synthetic_g1_software_input_only' or
                    snapshot['tenant_id'] != model.tenant_id or snapshot['snapshot_id'] != model.snapshot_id or
                    (context['tenant_id'], context['snapshot_id'], context['decision_context_id']) !=
                        (model.tenant_id, model.snapshot_id, model.decision_context_id) or
                    weather.get('synthetic') is not True or thermal.get('synthetic') is not True or
                    weather.get('fixture_id') != 'synthetic-weather-v1' or
                    thermal.get('fixture_id') != model.parameter_set_version or
                    context['claim_mode'] != 'ex_post_replay' or
                    hold['hold_report_id'] != model.market_context.hold_report_id or
                    any(hold[key] != context[key] for key in ('tenant_id', 'snapshot_id',
                        'decision_context_id', 'claim_mode', 'decision_time_kind')) or
                    hold['decision_at'] != _time(context['decision_at_utc'])):
                raise ValueError()
            return {key: snapshot[key] for key in ('manifest_sha256', 'weather_sha256', 'thermal_sha256')} | {
                'context_sha256': context['context_sha256']}
        except Exception:
            raise ThermalScenarioHold('thermal scenario references unavailable') from None

    def _record(self, row):
        model = self._model(row['payload_raw'])
        pins = self._references(model)
        if ((row['tenant_id'], row['scenario_id'], row['revision'], row['snapshot_id'], row['decision_context_id']) !=
                (model.tenant_id, model.scenario_id, model.scenario_revision, model.snapshot_id, model.decision_context_id) or
                row['payload_sha256'] != sha256(row['payload_raw']).hexdigest() or
                row['pins_raw'] != canonical_input_bytes(pins) or
                row['registered_by'] != self.runtime_identity[0].roles['authority']):
            raise ThermalScenarioHold('thermal scenario stored record differs')
        return {'scenario': model, 'scenario_sha256': row['payload_sha256'], 'pins': pins,
                'status': 'registered_intent', 'recorded_at': row['recorded_at']}

    def put(self, tenant, value):
        self._binding()
        if not self.runs._scope(tenant, 'thermal_scenario_write'):
            raise ThermalScenarioHold('thermal scenario registration denied')
        try:
            raw = canonical_input_bytes(untrusted_data(value))
        except Exception:
            raise ThermalScenarioHold('thermal scenario input rejected') from None
        model = self._model(raw)
        if model.tenant_id != tenant:
            raise ThermalScenarioHold('thermal scenario registration denied')
        pins = self._references(model)
        with self.connect() as conn:
            if not self.runs._scope(tenant, 'thermal_scenario_write'):
                raise ThermalScenarioHold('thermal scenario registration denied')
            conn.execute(sql.SQL('''
                INSERT INTO {} (tenant_id,scenario_id,revision,snapshot_id,decision_context_id,
                    payload_raw,payload_sha256,pins_raw,registered_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
            ''').format(self._table()), (tenant, model.scenario_id, model.scenario_revision,
                model.snapshot_id, model.decision_context_id, raw, sha256(raw).hexdigest(),
                canonical_input_bytes(pins), self.runtime_identity[0].roles['authority']))
            row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s')
                .format(self._table()), (tenant, model.scenario_id, model.scenario_revision)).fetchone()
            if row is None or row['payload_raw'] != raw:
                raise ThermalScenarioConflict('conflicting immutable scenario')
            record = self._record(row)
            self._binding()
            if not self.runs._scope(tenant, 'thermal_scenario_write'):
                raise ThermalScenarioHold('thermal scenario registration denied')
            return record

    def get(self, tenant, scenario_id, revision):
        self._binding()
        if not self.runs._scope(tenant, 'thermal_scenario_read'):
            return None
        if any(type(value) is not str or len(value) > 200 or not re.fullmatch(IDENTIFIER, value)
               for value in (scenario_id, revision)):
            return None
        with self.connect() as conn:
            row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s')
                .format(self._table()), (tenant, scenario_id, revision)).fetchone()
        return self._record(row) if row else None
