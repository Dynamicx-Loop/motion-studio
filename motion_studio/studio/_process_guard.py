"""Owned Linux process guard: native children cannot outlive a dead service.

Executed as a standalone stdlib script, independent of scientific runtime imports.
The guard and native descendants share a process group. PID birth identities avoid
signalling an unrelated process after PID reuse.
"""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def process_identity(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()
        return fields[19] if fields[0] != 'Z' else None
    except (OSError, ValueError, IndexError):
        return None


def process_scope():
    """Identify the boot and PID namespace in which stored PIDs have meaning.

    Missing OS visibility is unknown, never evidence that another owner died.
    """
    try:
        return {'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'pid_namespace': os.readlink('/proc/self/ns/pid')}
    except OSError:
        return None


def main():
    owner, identity = int(sys.argv[1]), sys.argv[2]
    stopping = False
    deadline = None

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    if process_identity(owner) != identity:
        return 125
    child = subprocess.Popen(sys.argv[3:])
    while True:
        if process_identity(owner) != identity:
            stopping = True
        if stopping and deadline is None:
            deadline = time.monotonic() + 2
            os.killpg(os.getpgrp(), signal.SIGTERM)
        if deadline is not None and time.monotonic() >= deadline:
            os.killpg(os.getpgrp(), signal.SIGKILL)
        code = child.poll()
        if code is not None and not stopping:
            return code
        # On stop, keep the guard alive until group KILL even if native exits:
        # descendants may ignore TERM while the native leader exits promptly.
        time.sleep(.05)


if __name__ == '__main__':
    sys.exit(main())
