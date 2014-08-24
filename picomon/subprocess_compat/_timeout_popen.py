from sys import hexversion as sys_hexversion
import subprocess


# Import or implement Popen() with timeout support
if sys_hexversion >= 0x03030000:
    # on Python 3.3 Popen() supports timeout, we have nothing to do
    from subprocess import TimeoutExpired

    class Popen(subprocess.Popen):
        pass
else:
    # on Python < 3.3, implement timeout with a thread
    from threading import Thread

    class TimeoutExpired(subprocess.CalledProcessError):
        def __init__(self, args, timeout=None, output=None):
            self.args, self.timeout, self.output = args, timeout, output

        def __str__(self):
            return 'Command %s timed out after %g seconds' % (self.args,
                                                              self.timeout)

    class Popen(subprocess.Popen):
        def __init__(self, args, *pargs, **kwargs):
            self.args = args
            self._out = None
            self._err = None
            self._exc = None
            self._thread = None
            super().__init__(args=args, *pargs, **kwargs)

        def _communicate_thread(self, input=None):
            try:
                self._out, self._err = super().communicate(input=input)
            except Exception as ex:
                self._exc = ex

        def communicate(self, input=None, timeout=None):
            if timeout is None and not self._thread:
                # without a timeout, default implementation is fine
                return super().communicate(input=input)
            elif self._thread and not self._thread.is_alive():
                # if this is a second call and the thread finished, return
                # the existing result
                if self._exc:
                    raise self._exc
                return self._out, self._err
            else:
                # otherwise, implement the timeout
                if not self._thread:
                    self._thread = Thread(target=self._communicate_thread,
                                          args=(input,))
                    self._thread.start()
                self._thread.join(timeout=timeout)
                if self._thread.is_alive():
                    raise TimeoutExpired(self.args, timeout)
                else:
                    if self._exc:
                        raise self._exc
                    return self._out, self._err
