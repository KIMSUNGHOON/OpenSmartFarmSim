"""Explicit owner-write/group-read content metadata; not a tenant ACL."""

from dataclasses import dataclass
import os
import stat


@dataclass(frozen=True)
class ContentAccess:
    owner_uid: int
    reader_gid: int

    def __post_init__(self):
        if any(type(value) is not int or not 0 <= value < 2**32 - 1
               for value in (self.owner_uid, self.reader_gid)):
            raise ValueError("explicit content owner and reader group required")

    def require_writer(self):
        if (os.geteuid() != self.owner_uid or
                self.reader_gid not in {os.getegid(), *os.getgroups()}):
            raise ValueError("content writer identity or group differs")

    def validate(self, fd, *, directory):
        info = os.fstat(fd)
        expected_type = stat.S_ISDIR if directory else stat.S_ISREG
        if (not expected_type(info.st_mode) or info.st_uid != self.owner_uid or
                info.st_gid != self.reader_gid or
                stat.S_IMODE(info.st_mode) != (0o750 if directory else 0o640)):
            raise ValueError("shared content metadata differs")
        if {"system.posix_acl_access", "system.posix_acl_default"} & set(os.listxattr(fd)):
            raise ValueError("shared content ACL is not permitted")

    def prepare_new(self, fd, *, directory):
        self.require_writer()
        info = os.fstat(fd)
        expected_type = stat.S_ISDIR if directory else stat.S_ISREG
        if not expected_type(info.st_mode) or info.st_uid != self.owner_uid:
            raise ValueError("new content descriptor is not owned by writer")
        if {"system.posix_acl_access", "system.posix_acl_default"} & set(os.listxattr(fd)):
            raise ValueError("inherited content ACL is not permitted")
        os.fchown(fd, -1, self.reader_gid)
        os.fchmod(fd, 0o750 if directory else 0o640)
        self.validate(fd, directory=directory)
