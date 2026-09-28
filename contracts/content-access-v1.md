# Content access v1

Status: **software storage candidate**. It enables an explicitly configured
supervisor to read authority-owned content under a separate UID/group. It does
not pass G1/G4, attest complete services or provision production credentials,
tenant volumes, readonly mounts or operating accounts. The CLI production guard
remains closed.

[`ContentAccess(owner_uid, reader_gid)`](../backend/app/content_access.py) is
optional trusted JobStore configuration. The default private store retains its
existing owner-only creation policy. The shared profile requires the writer's
effective UID to equal owner_uid and the reader_gid to be its effective or
supplementary group. Readers may open existing content, but creating/writing
through the store is rejected for any other effective UID.

| Object | Exact shared metadata | Allowed data access |
| --- | --- | --- |
| Root, `.evidence`, hashed tenant directories | owner_uid, reader_gid, `0750` | Owner writes; group reads/searches; others none |
| Regular digest files | owner_uid, reader_gid, `0640` | Owner writes; group reads; others none |
| Private credential/key directories and files | Outside the content root; separate UID, `0700`/`0600` | Intended secret owner only in the tested DAC setup |

All shared objects reject special mode bits and POSIX access/default ACL xattrs.
Named ACL entries can grant another user access while the displayed mode remains
`0750` or `0640`; default ACLs can propagate those entries to new objects
([Linux ACL manual](https://man7.org/linux/man-pages/man5/acl.5.html)). Metadata
inspection therefore includes ACL checks on the opened descriptor. ACL presence
or an inspection error fails closed rather than removing permissions silently.
Other filesystem/ACL implementations are not accepted by this Linux policy.

## Descriptor checks and durability

Root and every content subdirectory are opened relative to directory descriptors
with `O_NOFOLLOW`. Shared reads validate owner, group, exact mode and ACLs on each
opened directory and on the final file descriptor. The byte hash is computed
from that same file descriptor. Final opens use `O_NONBLOCK` so a corrupt FIFO
does not block before the regular-file check. Symlinks and nonregular objects
are refused. `read_artifact` now uses this same bounded-size/metadata/hash path.

Directories are initially created private. Only a freshly created owned
descriptor receives the configured group/mode, followed by validation and
directory/parent fsync. A new temporary file remains private while bytes are
written; its group/mode is set on its descriptor, checked, and fsynced before
linking the digest name. Descriptor metadata operations avoid following a new
pathname to an unrelated object ([Python os APIs](https://docs.python.org/3/library/os.html)).

An existing directory/file is never chmodded or chowned by this policy. Existing
private roots therefore cannot be silently migrated into shared roots. Digest
deduplication opens the existing object without following symlinks and checks
regular type, size, metadata/ACL and SHA. It never overwrites the final name.
Temporary cleanup removes only the created temporary entry and fsyncs the
directory; failed SQL commits may leave validated orphan bytes, as before.
An interrupted new directory setup can leave an incomplete private object that
subsequent calls reject; operator recovery must inspect the owned object rather
than automatically widening it.

## Trust and tenant scope

The reader group covers the whole configured content root. It is not a tenant
ACL or source-rights approval. Production must provision separate tenant roots,
UIDs/groups and readonly supervisor mounts, retain scoped DB/source permission
checks, and keep general workers and per-job CLI UIDs outside the reader group
and secret locations. A group member can read files directly; store/API rights
checks alone do not constrain that credential/group holder. Root/provisioner
control and post-check privileged metadata changes remain outside this test
boundary. Ordinary Linux access checks use effective UID/GID and supplementary
groups ([Linux inode permissions](https://man7.org/linux/man-pages/man7/inode.7.html),
[group API](https://man7.org/linux/man-pages/man2/setgroups.2.html)).

The existing signed supervisor path and real SCRAM test helpers now propagate
this optional policy. Three extra shared-store cases run the complete three AI
stages with fake CLI/test keys under separately authenticated DB users. These
local service tests still share an OS UID; they do not prove full service
separation or actual runtime model execution.

## Verification

[Storage tests](../backend/tests/test_content_access.py) cover private umask,
correct metadata/hash/dedup inode preservation, each directory level, widened/
special file modes, wrong identities, effective UID/group admission, unchanged
private existing roots, artifact reads, sync-before-link, FIFO/symlink rejection,
and named/default/inherited ACL refusal. Real named ACLs first produced three
RED cases despite unchanged modes, then passed after descriptor ACL inspection.

[The hosted UID smoke](../scripts/check-content-uid-boundary.py) runs from a
trusted root test controller in a bounded temporary tree. It creates no system
users/groups and edits no system configuration. The actual publisher drops to
UID 11001 with reader GID 11010. Clean exec probes verify real/effective/saved
UID/GID and supplementary groups: UID 11002 reads/hash-checks content but cannot
write/create; UID 11003 without the group cannot read/write/create. Separate
private fixture credential/key files are readable only by their intended UIDs;
the other service and general worker are denied. A changed content-file owner
is rejected by the reader. Fixture secrets are generated after the writer exits,
are not logged, and the temporary tree is removed.

This is actual Linux filesystem DAC evidence with synthetic bytes and fixture
secrets. It is not complete authority/supervisor/CLI service identity, actual DB
secret custody, per-job containment/egress, independent signing control, model
execution, release/planning evidence, production HBA/TLS or G1/G4 acceptance.
Local rootless runs verify storage and SQL/process contracts; the distinct-UID
smoke requires the hosted runner's root permission and is a separate CI step.

Local PostgreSQL 16.15 verification on 2026-09-28: **26 focused storage tests**
and the full backend **1,190 passed, zero skipped** in 237.52 seconds. Two existing
Pydantic serializer warnings remain. The full suite includes the three extra
shared-store/real-SCRAM service cases. The UID smoke was not run locally because
the local account has no noninteractive root access; its hosted result must be
observed separately.
