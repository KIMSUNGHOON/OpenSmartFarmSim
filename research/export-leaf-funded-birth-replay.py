"""Export approved own-public funded fixtures without importing growth code."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
from app.content_access import ContentAccess
from app import crop_leaf_funded_birth_artifact_reader as reader
from app.crop_morphology_artifact_io import MorphologyBlobStore, _need
from app.crop_morphology_artifact_reader import _canonical

CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256, 'CODE_HOLD: original funded exporter required')


def _grants(manifest):
    _need(all(manifest['source_rights'][key] is True for key in ('use', 'display', 'redistribute')),
          'RIGHTS_HOLD: own input use/display/redistribute grants required')


class _Output:
    def __init__(self, path):
        self.path = path; self.fd = None; self.access = ContentAccess(os.getuid(), os.getgid())
        try:
            path.mkdir(mode=0o750)
            self.fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            self.access.prepare_new(self.fd, directory=True)
            self.identity = self._identity(self.fd); self.guard()
        except BaseException:
            self.close(); raise

    def __enter__(self): return self
    def __exit__(self, *args): self.close()

    def close(self):
        if self.fd is not None: os.close(self.fd); self.fd = None

    @staticmethod
    def _identity(fd):
        info = os.fstat(fd)
        return info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid

    def guard(self):
        self.access.validate(self.fd, directory=True)
        _need(self.path.absolute() == self.path.resolve(), 'STORAGE_HOLD: original nonsymlink output path required')
        current = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            _need(self._identity(current) == self.identity == self._identity(self.fd), 'STORAGE_HOLD: output directory replaced')
        finally: os.close(current)

    def write(self, name, raw):
        self.guard()
        _need(type(name) is str and Path(name).name == name and name not in ('.', '..')
              and type(raw) is bytes and 0 < len(raw) <= reader.MAX, 'CAPACITY_HOLD: bounded named export file required')
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o640, dir_fd=self.fd)
        try:
            self.access.prepare_new(fd, directory=False)
            with os.fdopen(fd, 'wb', closefd=False) as handle:
                handle.write(raw); handle.flush(); os.fsync(fd)
        finally: os.close(fd)
        self.guard()
        return {'path': name, 'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)}

    def verify(self, written):
        self.guard()
        _need(set(os.listdir(self.fd)) == {d['path'] for d in written}, 'STORAGE_HOLD: original output file set required')
        for descriptor in written:
            fd = os.open(descriptor['path'], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.fd)
            try:
                self.access.validate(fd, directory=False); before = os.fstat(fd)
                _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'STORAGE_HOLD: single-link output required')
                with os.fdopen(fd, 'rb', closefd=False) as handle: raw = handle.read(reader.MAX+1)
                after = os.fstat(fd)
                _need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                      == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'STORAGE_HOLD: output changed during read')
            finally: os.close(fd)
            _need(len(raw) == descriptor['bytes'] and sha256(raw).hexdigest() == descriptor['sha256'], 'HASH_HOLD: original written bytes required')
        self.guard()

    def publish(self, raw):
        self.write('.index.pending', raw); self.guard()
        os.rename('.index.pending', 'index.json', src_dir_fd=self.fd, dst_dir_fd=self.fd)
        os.fsync(self.fd); self.guard()


def export(directory, root_sha256, output):
    _fence()
    directory, output = Path(directory), Path(output)
    source, target = directory.resolve(), output.resolve()
    _need(output.is_absolute() and not output.is_symlink() and output.absolute() == target
          and source != target and source not in target.parents and target not in source.parents,
          'STORAGE_HOLD: new nonsymlink output outside source/ancestors required')
    access = ContentAccess(os.getuid(), os.getgid())
    manifest = reader.read_funded_leaf_manifest(directory, access, root_sha256); _grants(manifest)
    written = []; sources = []; events = []; checkpoints = []; frames = []
    with _Output(output) as target_dir:
        def write(name, raw):
            descriptor = target_dir.write(name, raw); written.append(descriptor); return descriptor
        with MorphologyBlobStore(directory, access) as store:
            sources.append({'role': 'root', **write('root.json', store.get(root_sha256, maximum=reader.MAX))})
            for role, descriptor in manifest['sources'].items():
                name = 'NOTICE.txt' if role == 'license_notice' else f'source-{role}.json'
                sources.append({'role': role, **write(name, store.get(descriptor['sha256'], maximum=reader.MAX))})
            for i, event in enumerate(manifest['events']):
                events.append({**event,
                    'point': write(f'event-{i}.json', store.get(event['point']['sha256'], maximum=reader.MAX)),
                    'context_snapshot': write(f'context-{i}.json', store.get(event['context_snapshot']['sha256'], maximum=reader.MAX))})
            for i, sample in enumerate(manifest['samples']):
                frame = reader.read_funded_leaf_frame(directory, access, root_sha256, index=i)
                checkpoints.append({**sample, **write(f'checkpoint-{i}.json', store.get(sample['checkpoint_sha256'], maximum=reader.CHECKPOINT_MAX))})
                frames.append({**{key: frame[key] for key in ('index', 'step_index', 'phase', 'event_sequence', 'at',
                    'context_sha256', 'checkpoint_sha256', 'sample_sha256', 'state_sha256')}, **write(f'frame-{i}.json', _canonical(frame))})
        public = {**reader.ROOT_CONSTANTS, 'schema_version': 'funded-leaf-public-fixture-v1', 'artifact_sha256': root_sha256,
            'input_id': manifest['input_id'], 'source_rights': manifest['source_rights'], 'exporter_sha256': CODE_SHA256,
            'sources': sources, 'events': events, 'checkpoints': checkpoints, 'frames': frames}
        raw = _canonical(public); _need(len(raw) <= reader.MAX, 'CAPACITY_HOLD: bounded public index required')
        target_dir.verify(written)
        latest = reader.read_funded_leaf_manifest(directory, access, root_sha256); _grants(latest)
        _need(_canonical(latest) == _canonical(manifest), 'HASH_HOLD: original funded source changed')
        target_dir.verify(written); _fence(); target_dir.publish(raw)
    return {'artifact_sha256': root_sha256, 'index_sha256': sha256(raw).hexdigest(),
            'frames': len(frames), 'events': len(events), 'public_files': len(written)+1}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('directory', type=Path); parser.add_argument('root_sha256'); parser.add_argument('output', type=Path)
    args = parser.parse_args(); print(json.dumps(export(args.directory, args.root_sha256, args.output), sort_keys=True))
