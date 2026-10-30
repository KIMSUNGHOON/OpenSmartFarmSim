"""Create a new own-public QA input before any source is calculated or stored.

Only the test input provider is scoped here; model and authority validators remain
unchanged. No existing private CAS, declaration or completed result is modified.
"""
from copy import deepcopy
from unittest.mock import patch

from test_crop_leaf_carbon_stock_artifact import inputs as numeric_template
import test_crop_supply_morphology_rhs as benchmark


def public_inputs(case=1, *, dt=.125, count=1):
    template = numeric_template(case, dt=dt, count=count)
    return {**{name:deepcopy(value) for name,value in template.items() if name != 'rights'},
            'rights': {'declaration_id':'own-public-supply-morphology-20261030',
                       'revision':'public-software-QA-v1',
                       'declared_at_utc':'2026-10-30T10:47:20Z',
                       **dict.fromkeys(('ownership_asserted','access','store','use','transform','display','redistribute'), True)}}


def make_public_current(directory, profiles):
    with patch.object(benchmark, 'crop_inputs', public_inputs):
        return benchmark.make_current(directory, profiles)
