"""Fresh-process calculation with self-authored QA repositories, no production DB."""
from pathlib import Path
from hashlib import sha256
import json
import sys

sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).parent)]
from app.economic_cost_trace import CostLineLedger,trace_bytes
from app.economic_production_batches import BatchEconomicScenario
from test_economic_production_batches import Repository

values=json.loads(Path(sys.argv[1]).read_bytes());hashes=[]
for value in values:
    s=BatchEconomicScenario.model_validate_json(json.dumps(value))
    result=CostLineLedger(Repository(s)).calculate(s);hashes.append(sha256(trace_bytes(result)).hexdigest())
Path(sys.argv[2]).write_text(json.dumps({'cases':len(values),'trace_sha256':hashes,'same_final_code':True},indent=2))
