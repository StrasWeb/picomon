import concurrent.futures
from time import sleep
from IPy import IP
from sys import hexversion as sys_hexversion


# Import or implement Popen() with timeout support
if sys_hexversion >= 0x03030000:
    # on Python 3.3 Popen() supports timeout, we have nothing to do
    from subprocess import TimeoutExpired, Popen, PIPE
else:
    # on Python < 3.3, implement timeout with a thread
    from threading import Thread
    import subprocess
    from subprocess import PIPE

    class TimeoutExpired(subprocess.SubprocessError):
        def __init__(self, args, timeout=None, output=None):
            self.cmd, self.timeout, self.output = args, timeout, output

        def __str__(self):
            return 'Command %s timed out after %g seconds' % (self.args,
                                                              self.timeout)

    class Popen(subprocess.Popen):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._out = None
            self._err = None
            self._exc = None
            self._thread = None

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


class Check(object):
    def __init__(self, **options):
        self._options = options
        self.errmsg = ''
        self.ok = True

    def __repr__(self):
        return '<%s options=%s>' % (self.__class__.__name__, self._options)

    def setup(self, host, addr):
        print("Starting to check for %s on %s (using ip %s)." %
              (str(self), str(host), str(addr)))
        pass

    def teardown(self, host, addr):
        if not self.ok:
            print("Check %s on %s (using ip %s) failed!" %
                  (str(self), str(host), str(addr)))
            print("Further information:\n" + self.errmsg)
        else:
            print("Check %s on %s (using ip %s) successful!" %
                  (str(self), str(host), str(addr)))

    def check(self, host, addr):
        pass

    def run(self, host, addr):
        self.setup(host, addr)
        self.ok = self.check(host, addr)
        self.teardown(host, addr)
        return self.ok

    def exec_with_timeout(self, command, timeout=2):
        self.errmsg = ''
        p = Popen(command, stdout=PIPE, stderr=PIPE)
        try:
            out, err = p.communicate(timeout=timeout)
        except TimeoutExpired:
            p.kill()
            out, err = p.communicate()
            self.errmsg += "Operation timed out\n"
        if p.returncode != 0:
            self.errmsg += "stdout: " + str(out) + '\n' + \
                           "stderr: " + str(err) + '\n'
        return p.returncode == 0

    def exec_by_ip_family(self, addr, v4command, v6command):
        ipv = IP(addr).version()
        if ipv == 4:
            return self.exec_with_timeout(v4command)
        if ipv == 6:
            return self.exec_with_timeout(v6command)
        self.errmsg = "Unknown IP version %s" % ipv
        return False


class CheckPing(Check):
    def check(self, host, addr):
        v4command = ['/bin/ping', '-c', '1', addr]
        v6command = ['/bin/ping6', '-c', '1', addr]
        return self.exec_by_ip_family(addr, v4command, v6command)


class CheckDNSRec(Check):
    def check(self, host, addr):
        self.errmsg = "Unimplemented"
        return False


class CheckDNSAut(Check):
    def check(self, host, addr):
        self.errmsg = "Unimplemented"
        return False


class Host(object):
    def __init__(self, ipv4, ipv6, checks):
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.checks = checks

    def __repr__(self):
        return '<Host ipv4="%s" ipv6="%s">' % (self.ipv4, self.ipv6)

    def check(self, executor):
        fail = 0
        for chk in self.checks:
            for addr in [self.ipv4, self.ipv6]:
                executor.submit(chk.run, self, addr)


hosts = [
    Host(ipv4='127.0.0.1', ipv6='::1', checks=[
        CheckPing(),
        CheckDNSAut(zone='prout.net'),
        CheckDNSRec(test='AAAA google.fr')
    ]),
    Host(ipv4='127.0.0.0', ipv6='::42', checks=[CheckPing()]),
]


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for host in hosts:
            host.check(executor)
