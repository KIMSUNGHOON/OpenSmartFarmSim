"""Small immutable job references; no numerical calculation or producer imports."""
from hashlib import sha256
from pathlib import Path

from . import crop_leaf_population_signed_artifact as signed


VERSION = 'leaf-population-execution-publication-v1'
LINK_VERSION = 'leaf-population-execution-result-link-v1'
RESULT_EVENT_KIND = 'leaf_population_result_registered_v1'
START_EVENT_KIND = 'leaf_population_calculation_started_v1'
MAX_LINK_BYTES = 4096
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_CONTRACT = (VERSION, LINK_VERSION, RESULT_EVENT_KIND, START_EVENT_KIND, MAX_LINK_BYTES)


class LeafPopulationResultLinkHold(ValueError):
    """A job has no valid original leaf population completion reference."""


def _need(condition):
    if not condition:
        raise LeafPopulationResultLinkHold('leaf population result reference unavailable')


def _binding():
    _need((VERSION, LINK_VERSION, RESULT_EVENT_KIND, START_EVENT_KIND, MAX_LINK_BYTES) == _CONTRACT
        and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)


def result_link(job, result_sha256):
    _binding()
    signed.reader._hash(result_sha256); signed.reader._hash(job['input_sha256'])
    return signed.reader._canonical({'schema_version': LINK_VERSION,
        'job_id': str(job['job_id']), 'input_sha256': job['input_sha256'],
        'result_sha256': result_sha256, **signed.FLAGS})


def read_link(raw, job):
    try:
        _binding()
        value = signed.reader._parse(raw, MAX_LINK_BYTES)
        _need(result_link(job, value['result_sha256']) == raw)
        return value
    except Exception:
        raise LeafPopulationResultLinkHold('leaf population result reference unavailable') from None


def publication_manifest(job, raw, result_sha256, worker_code_sha256):
    signed.reader._hash(worker_code_sha256)
    _need(read_link(raw, job)['result_sha256'] == result_sha256)
    _need(type(job['attempt_count']) is int and job['attempt_count'] >= 1)
    return {'schema_version': '1', 'publication_version': VERSION,
        'job_id': str(job['job_id']), 'stage': 'simulation', 'attempt': job['attempt_count'],
        'input_sha256': job['input_sha256'], 'artifact_sha256': sha256(raw).hexdigest(),
        'artifact_size': len(raw), 'result_sha256': result_sha256,
        'worker_code_sha256': worker_code_sha256, **signed.FLAGS}
