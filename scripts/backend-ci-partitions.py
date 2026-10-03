"""Partition the complete default pytest collection by file, preserving its order."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import pytest

PARTITION_COUNT = 6
DELEGATED = "tests/test_authored_full_software_path.py"


def partition_nodes(node_ids):
    if not node_ids or len(node_ids) != len(set(node_ids)):
        raise ValueError("The default collection must be nonempty with unique node IDs")
    files = sorted({node.split("::", 1)[0] for node in node_ids})
    if len(files) < PARTITION_COUNT:
        raise ValueError("Every partition must contain at least one collected file")
    owners = {file: index % PARTITION_COUNT for index, file in enumerate(files)}
    partitions = [[] for _ in range(PARTITION_COUNT)]
    for node in node_ids:
        partitions[owners[node.split("::", 1)[0]]].append(node)
    return partitions


class FilePartition:
    def __init__(self, index, manifest, output=None, summary=None):
        if index not in range(PARTITION_COUNT):
            raise ValueError("Invalid partition index")
        self.index = index
        self.manifest = Path(manifest)
        self.output = output
        self.summary = summary
        self.collected = []
        self.selected = None

    def pytest_itemcollected(self, item):
        self.collected.append(item.nodeid)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, config, items):
        nodes = [item.nodeid for item in items]
        if sorted(nodes) != sorted(self.collected):
            raise pytest.UsageError("Another collection filter changed the default inventory")
        try:
            partitions = partition_nodes(nodes)
        except ValueError as error:
            raise pytest.UsageError(str(error)) from error
        self.selected = partitions[self.index]
        selected = set(self.selected)
        removed = [item for item in items if item.nodeid not in selected]
        items[:] = [item for item in items if item.nodeid in selected]
        config.hook.pytest_deselected(items=removed)

    def pytest_collection_finish(self, session):
        if session.testsfailed or self.selected is None:
            return
        if [item.nodeid for item in session.items] != self.selected:
            raise pytest.UsageError("A later filter changed the partition")
        nodes = sorted(self.collected)
        inventory = json.dumps(nodes, ensure_ascii=True, separators=(",", ":"))
        digest = hashlib.sha256(inventory.encode()).hexdigest()
        data = {
            "schema_version": "backend-ci-partition-v1",
            "partition_count": PARTITION_COUNT,
            "partition": self.index,
            "inventory_sha256": digest,
            "all_node_ids": nodes,
            "selected_node_ids": self.selected,
        }
        raw = json.dumps(data, ensure_ascii=True, indent=2) + "\n"
        self.manifest.write_text(raw, encoding="utf-8")
        if self.output:
            with open(self.output, "a", encoding="utf-8") as stream:
                stream.write(f"inventory_{self.index}={digest}\n")
        if self.summary:
            with open(self.summary, "a", encoding="utf-8") as stream:
                stream.write(f"## Backend partition {self.index}\n\n```json\n{raw}```\n")
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        reporter.write_line(
            f"Partition {self.index}/{PARTITION_COUNT}: {len(self.selected)} of "
            f"{len(nodes)} nodes; complete inventory SHA-256 {digest}"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("partition", type=int, choices=range(PARTITION_COUNT))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args()
    if os.environ.get("PYTEST_ADDOPTS") or os.environ.get("PYTEST_PLUGINS"):
        parser.error("Environment-supplied pytest options/plugins are not permitted")
    manifest = args.manifest.resolve()
    os.chdir(Path(__file__).resolve().parents[1] / "backend")
    options = ["-q", "-rs", "--tb=short", "--durations=20", f"--ignore={DELEGATED}"]
    if args.collect_only:
        options.append("--collect-only")
    plugin = FilePartition(args.partition, manifest, os.environ.get("GITHUB_OUTPUT"),
                           os.environ.get("GITHUB_STEP_SUMMARY"))
    return pytest.main(options, plugins=[plugin])


if __name__ == "__main__":
    raise SystemExit(main())
