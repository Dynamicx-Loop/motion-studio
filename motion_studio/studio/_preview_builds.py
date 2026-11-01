"""Share derivative-build locks across Studio instances using the same state."""
import threading
import weakref


_BUILD_LOCKS = weakref.WeakValueDictionary()
_BUILD_LOCKS_GUARD = threading.Lock()


def _build_lock(state, preview_key):
    # Keep locks alive only while a builder or waiting caller holds a reference.
    key = (str(state), preview_key)
    with _BUILD_LOCKS_GUARD:
        lock = _BUILD_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _BUILD_LOCKS[key] = lock
        return lock
