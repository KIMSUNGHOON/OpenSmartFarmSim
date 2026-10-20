"""Rejected research candidate: bulk dictionary creation changes opaque hooks."""
import ast
from pathlib import Path


def build_candidate(stream):
    """Build only the proposed pairs-loop replacement in the original globals."""
    module = ast.parse(Path(stream.__file__).read_bytes())
    function = next(node for node in module.body
                    if isinstance(node, ast.FunctionDef) and node.name == '_json')
    pairs = next(node for node in function.body
                 if isinstance(node, ast.FunctionDef) and node.name == 'pairs')
    pairs.body = ast.parse("""
result = dict(items)
_need(len(result) == len(items), 'INPUT_HOLD: duplicate JSON key')
return result
""").body
    candidate = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace = {}
    exec(compile(candidate, __file__, 'exec'), stream.__dict__, namespace)
    return namespace['_json']
