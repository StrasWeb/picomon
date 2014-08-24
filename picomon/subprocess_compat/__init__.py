from . import _timeout_popen
from . import _threaded_popen
from ._timeout_popen import TimeoutExpired
from subprocess import PIPE


class Popen(_timeout_popen.Popen, _threaded_popen.Popen):
    pass
