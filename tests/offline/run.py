"""Run only the offline unit suite under a Linux syscall-level network deny.

Requires Linux x86_64 with seccomp. Fails closed on unsupported systems; this
is not a general sandbox for untrusted code or a way to run the E2E suite.
"""
import ctypes
import errno
import os
from pathlib import Path
import platform
import sys
import unittest


class Filter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]


class Program(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(Filter))]


def block_network():
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise RuntimeError("Offline runner requires Linux x86_64 and seccomp")
    # seccomp_data.arch must be AUDIT_ARCH_X86_64; reject x32 syscall ABI.
    bpf = [Filter(0x20, 0, 0, 4), Filter(0x15, 1, 0, 0xC000003E),
           Filter(0x06, 0, 0, 0x80000000), Filter(0x20, 0, 0, 0),
           Filter(0x45, 0, 1, 0x40000000), Filter(0x06, 0, 0, 0x80000000)]
    # Deny socket operations and io_uring setup (which could issue socket ops).
    for number in list(range(41, 56)) + [288, 299, 307, 425]:
        bpf += [Filter(0x15, 0, 1, number), Filter(0x06, 0, 0, 0x00050000 | errno.EPERM)]
    bpf.append(Filter(0x06, 0, 0, 0x7FFF0000))
    filters = (Filter * len(bpf))(*bpf)
    program = Program(len(bpf), filters)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                           ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise OSError(ctypes.get_errno(), "PR_SET_NO_NEW_PRIVS failed")
    if libc.prctl(22, 2, ctypes.addressof(program), 0, 0) != 0:  # PR_SET_SECCOMP
        raise OSError(ctypes.get_errno(), "seccomp filter failed")


def main():
    # Guard is installed before test discovery/import. It is inherited by children.
    block_network()
    root = Path(__file__).resolve().parents[2]
    os.chdir(root)
    sys.path.insert(0, str(root))
    suite = unittest.defaultTestLoader.discover(str(root / "tests" / "offline"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    sys.exit(main())
