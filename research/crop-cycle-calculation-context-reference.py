"""Resume owned synthetic evidence in a fresh Python process; no farm claim."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app import crop_cycle_calculation_context as calculation
from app.crop_cycle_input_evidence import InputEvidenceAuthority
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('directory', 'evidence', 'key', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--root', required=True)
    parser.add_argument('--issuer', required=True)
    parser.add_argument('--key-id', required=True)
    parser.add_argument('--checkpoint', type=Path)
    args = parser.parse_args()
    profiles = {
        'growth_profile': ReferenceParameters((ROOT / 'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
        'cohort_profile': ReferenceFruitCohortParameters((ROOT / 'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
        'transport_profile': ReferenceFruitTransportParameters((ROOT / 'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()),
    }
    server = InputEvidenceAuthority(profiles, (ROOT / 'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes(),
                                    integrity_key=args.key.read_bytes(), issuer_id=args.issuer, key_id=args.key_id)
    before = len(os.listdir('/proc/self/fd'))
    with calculation.open_calculation_context(args.directory, args.root, args.evidence.read_bytes(), authority=server) as context:
        checkpoint = (calculation.restore_checkpoint(context, args.checkpoint.read_bytes())
                      if args.checkpoint else calculation.start(context))
        restored = json.loads(json.dumps(checkpoint))
        samples, events = [], []
        while True:
            result = calculation.advance_chunk(context, checkpoint, {'max_steps': 7, 'max_transitions': 13})
            assert result['output_start'] == restored['output_cursor'] + len(samples)
            assert result['event_start'] == restored['event_cursor'] + len(events)
            samples.extend(result['samples']); events.extend(result['events'])
            if result['status'] != 'yielded':
                break
            checkpoint = calculation.restore_checkpoint(context, calculation.checkpoint_bytes(context, result['checkpoint']))
        result = {**result, 'samples': samples, 'events': events}
    after = len(os.listdir('/proc/self/fd'))
    assert before == after
    value = {'scope': 'owned_synthetic_calculation_restart_only', 'pid': os.getpid(),
             'restored_checkpoint': restored, 'result': result, 'fd_before': before, 'fd_after': after,
             'process_max_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
             'calculation_code_sha256': calculation.CODE_SHA256}
    with args.output.open('x') as handle:
        os.chmod(args.output, 0o400)
        json.dump(value, handle, sort_keys=True); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    print(json.dumps({'status': result['status'], 'steps': result['steps'],
                      'samples': len(samples), 'events': len(events),
                      'output_sha256': sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
