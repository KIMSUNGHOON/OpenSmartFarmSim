"""The browser's closed source roots must match the actual canonical models."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.market_source_store import _KINDS


def test_browser_source_roots_match_current_server_models():
    raw=(Path(__file__).resolve().parents[2]/'web/src/source-fields.ts').read_text()
    fields=json.loads(raw.removeprefix('export const SOURCE_FIELDS = ').removesuffix(' as const;\n'))
    assert fields=={kind:[key for key in _KINDS[kind][0].model_fields if key!='tenant_id']
        for kind in ('economic_input','economic_scenario','joint_shock','input_rights')}
