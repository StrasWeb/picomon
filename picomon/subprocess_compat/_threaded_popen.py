from sys import hexversion as sys_hexversion
import subprocess


# Fix for bug http://bugs.python.org/issue18851
# FIXME: double check versions
#   found in 3.2.0r1, fixed in 3.3.3
#   found in 3.4.0, fixed in 3.4.0a1
if not ((sys_hexversion >= 0x030200C1 and sys_hexversion < 0x030303F0) or
        (sys_hexversion >= 0x03040000 and sys_hexversion < 0x030400A1)):
    class Popen(subprocess.Popen):
        pass
else:
    # as subprocess.Popen is not atomic when failing to spawn command,
    # lock globally (see above)
    from threading import Lock

    _Popen_lock = Lock()

    class Popen(subprocess.Popen):
        def __init__(self, *args, **kwargs):
            with _Popen_lock:
                super().__init__(*args, **kwargs)
