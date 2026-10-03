"""A CI partition must cover the default collection and preserve failures."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/backend-ci-partitions.py"
spec = importlib.util.spec_from_file_location("backend_ci_partitions", SCRIPT)
partitioner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(partitioner)


def test_partition_union_is_exact_and_files_are_atomic():
    nodes = [f"tests/test_{i:02}.py::test_case[{j}]" for i in range(13) for j in range(3)]
    groups = partitioner.partition_nodes(nodes)
    flattened = [node for group in groups for node in group]
    assert sorted(flattened) == sorted(nodes)
    assert len(flattened) == len(set(flattened))
    reverse = partitioner.partition_nodes(list(reversed(nodes)))
    for group, reversed_group in zip(groups, reverse):
        assert list(reversed(group)) == reversed_group
        assert group
    for i in range(13):
        assert sum(any(f"test_{i:02}.py::" in node for node in group) for group in groups) == 1


@pytest.mark.parametrize("nodes", [[], ["test_a.py::test_a"],
                                    ["test_a.py::test_a"] * 6])
def test_unusable_inventory_is_refused(nodes):
    with pytest.raises(ValueError):
        partitioner.partition_nodes(nodes)


@pytest.mark.parametrize("index", [-1, 6, "0"])
def test_invalid_partition_is_refused(index, tmp_path):
    with pytest.raises(ValueError):
        partitioner.FilePartition(index, tmp_path / "manifest.json")


CHILD = """
import importlib.util, sys
import pytest
spec = importlib.util.spec_from_file_location('partitioner', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
index, manifest, mode = sys.argv[2:]
options = ['-q', '--rootdir=.', '--tb=short']
plugins = []
if mode == 'baseline':
    class Baseline:
        def pytest_collection_finish(self, session):
            import json
            from pathlib import Path
            Path(manifest).write_text(json.dumps([item.nodeid for item in session.items]))
    plugins.append(Baseline())
    options.append('--collect-only')
else:
    plugins.append(module.FilePartition(int(index), manifest, manifest + '.output',
                                        manifest + '.summary'))
    if mode == 'collect':
        options.append('--collect-only')
    if mode == 'filter':
        options += ['-k', 'nothing_matches']
    if mode == 'late-filter':
        class LateFilter:
            @pytest.hookimpl(hookwrapper=True)
            def pytest_collection_modifyitems(self, items):
                yield
                items.pop()
        plugins.append(LateFilter())
raise SystemExit(pytest.main(options, plugins=plugins))
"""


def child(tmp_path, index, mode):
    manifest = tmp_path / f"{index}-{mode}.json"
    env = {key: value for key, value in os.environ.items()
           if key not in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}}
    result = subprocess.run([sys.executable, "-c", CHILD, str(SCRIPT), str(index),
                             str(manifest), mode], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=30)
    return result, manifest


def test_real_collection_union_output_consistency_and_failure_propagation(tmp_path):
    for index in range(7):
        assertion = "False" if index == 6 else "True"
        (tmp_path / f"test_{index:02}.py").write_text(
            f"import pytest\n@pytest.mark.parametrize('case', [0, 1])\n"
            f"def test_case(case):\n    assert {assertion}\n")
    baseline, baseline_path = child(tmp_path, 0, "baseline")
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr
    nodes = json.loads(baseline_path.read_text())
    groups = []
    digests = set()
    for index in range(6):
        result, manifest = child(tmp_path, index, "collect")
        assert result.returncode == 0, result.stdout + result.stderr
        data = json.loads(manifest.read_text())
        assert data["all_node_ids"] == sorted(nodes)
        groups.extend(data["selected_node_ids"])
        digests.add(data["inventory_sha256"])
        assert Path(str(manifest) + ".output").read_text() == (
            f"inventory_{index}={data['inventory_sha256']}\n")
        assert manifest.read_text() in Path(str(manifest) + ".summary").read_text()
    assert sorted(groups) == sorted(nodes)
    assert len(groups) == len(set(groups))
    assert len(digests) == 1
    failed, _ = child(tmp_path, 0, "run")
    passed, _ = child(tmp_path, 1, "run")
    assert failed.returncode == 1, failed.stdout + failed.stderr
    assert "2 failed" in failed.stdout
    assert passed.returncode == 0, passed.stdout + passed.stderr
    filtered, filtered_path = child(tmp_path, 0, "filter")
    assert filtered.returncode != 0
    assert "filter changed the default inventory" in filtered.stderr
    assert not filtered_path.exists()
    filtered, filtered_path = child(tmp_path, 0, "late-filter")
    assert filtered.returncode != 0
    assert "later filter changed the partition" in filtered.stderr
    assert not filtered_path.exists()


def test_collection_error_never_emits_a_valid_inventory(tmp_path):
    for index in range(7):
        (tmp_path / f"test_{index:02}.py").write_text("def test_case():\n    pass\n")
    (tmp_path / "test_broken.py").write_text("raise RuntimeError('collection error')\n")
    result, manifest = child(tmp_path, 0, "collect")
    assert result.returncode != 0
    assert "collection error" in result.stdout
    assert not manifest.exists()
    assert not Path(str(manifest) + ".output").exists()
    assert not Path(str(manifest) + ".summary").exists()


def test_repository_default_inventory_is_repeatable(tmp_path):
    env = {key: value for key, value in os.environ.items() if key not in {
        "PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH", "GITHUB_OUTPUT", "GITHUB_STEP_SUMMARY",
        "OSSF_REAL_CLI_SMOKE", "OSSF_REAL_AUTHORED_FULL_CLI_SMOKE"}}
    inventories = []
    for index in range(2):
        manifest = tmp_path / f"repository-{index}.json"
        result = subprocess.run([sys.executable, str(SCRIPT), "0", "--manifest", str(manifest),
                                 "--collect-only"], env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        inventories.append(json.loads(manifest.read_text())["all_node_ids"])
    assert inventories[0] == inventories[1], "The repository's default inventory changes between processes"


@pytest.mark.parametrize("key", ["PYTEST_ADDOPTS", "PYTEST_PLUGINS"])
def test_environment_options_cannot_silently_remove_tests(key, tmp_path):
    env = dict(os.environ)
    env[key] = "--collect-only" if key == "PYTEST_ADDOPTS" else "untrusted_plugin"
    result = subprocess.run([sys.executable, str(SCRIPT), "0", "--manifest",
                             str(tmp_path / "manifest.json")], env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert "not permitted" in result.stderr
    assert not (tmp_path / "manifest.json").exists()
