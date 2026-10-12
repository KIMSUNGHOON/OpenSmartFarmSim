"""Private browser evidence and rights monitoring in the owning supervisor."""
from pathlib import Path
import json
import os
import re
import stat
import tempfile


def private_bytes(path, *, maximum=2*1024**2):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                or info.st_size > maximum):
            raise ValueError('private browser input rejected')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(maximum+1)
        if len(raw) > maximum:
            raise ValueError('private browser input rejected')
        return raw
    finally:
        os.close(fd)


def atomic_bytes(path, raw):
    fd, name = tempfile.mkstemp(prefix='.browser-owned-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(raw); output.flush(); os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


class BrowserEvidence:
    def __init__(self, directory, *, request, access, rights, driver, playwright,
                 mode, origin, job_id=None):
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700)
        self.rights = Path(rights)
        self.original = private_bytes(self.rights)
        declaration = json.loads(self.original)
        body = json.loads(private_bytes(request))
        token = json.loads(private_bytes(access))['token']
        self.source = body['input']['source_sha256']
        if (type(declaration) is not dict or any(type(v) is not bool
                or not re.fullmatch('[0-9a-f]{64}', k) for k,v in declaration.items())
                or self.source not in declaration or mode not in ('profile','completed','hold','cancel')):
            raise ValueError('browser rights source rejected')
        context = {'origin':origin, 'mode':mode, 'token':token,
            'request_file':str(request), 'directory':str(self.directory),
            'playwright':str(playwright), 'job_id':job_id}
        self.context = self.directory/'context.private.json'
        atomic_bytes(self.context, json.dumps(context).encode())
        self.command = ['nice','-n','19','node','--expose-gc','--max-old-space-size=64',
            '--max-semi-space-size=1', str(driver), str(self.context)]
        self.changed = False

    def poll(self):
        for event, revoke in (('rights-revoke',True),('rights-restore',False)):
            request, ack = self.directory/event, self.directory/(event+'-ack')
            if not request.exists() and not request.is_symlink(): continue
            info = request.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size):
                raise ValueError('browser rights event rejected')
            if ack.exists(): continue
            if ack.is_symlink(): raise ValueError('browser rights acknowledgement rejected')
            raw = self.original
            if revoke:
                declaration = json.loads(raw); declaration[self.source] = False
                raw = json.dumps(declaration, sort_keys=True).encode()
            atomic_bytes(self.rights, raw)
            self.changed = revoke
            fd = os.open(ack, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
            os.close(fd)

    def close(self):
        if private_bytes(self.rights) != self.original:
            atomic_bytes(self.rights, self.original)
        self.changed = False

    def node_memory(self):
        path = self.directory/'node-memory.private.json'
        if not path.exists(): return None
        value = json.loads(private_bytes(path, maximum=16384))
        names = ('rss','heapUsed','heapTotal','external','arrayBuffers')
        if (type(value) is not dict or set(value) != {'stage','memory'}
                or value['stage'] not in ('starting','page','running','terminal','rights','mobile','closing')
                or type(value['memory']) is not dict or set(value['memory']) != set(names)
                or any(type(value['memory'][k]) is not int or value['memory'][k]<0 for k in names)):
            raise ValueError('browser memory evidence rejected')
        return value


def resource_snapshot(rss, *, elapsed, node=None):
    """All PID values belong to one sample; independent maxima are not added."""
    rows = []
    for pid, amount in sorted(rss.items()):
        try:
            fields = Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
            rows.append({'pid':pid, 'start_ticks':int(fields[19]),
                'comm':Path('/proc',str(pid),'comm').read_text().strip(), 'RSS_bytes':amount})
        except (FileNotFoundError,ProcessLookupError):
            rows.append({'pid':pid, 'start_ticks':None, 'comm':'exited_after_sample', 'RSS_bytes':amount})
    return {'elapsed_seconds':elapsed, 'combined_RSS_bytes':sum(rss.values()),
        'single_PID_RSS_bytes':max(rss.values(),default=0), 'processes':rows,
        'node':node}
