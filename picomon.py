import concurrent.futures
from time import sleep
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

    class TimeoutExpired(subprocess.CalledProcessError):
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

    def setup(self):
        pass

    def teardown(self):
        pass

    def check(self, host, addr):
        pass

    def run(self):
        self.setup()
        self.ok = self.check()
        self.teardown()
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


class CheckIP(Check):
    def __repr__(self):
        return '<%s on %s, options=%s>' % (self.__class__.__name__, self.addr, self._options)


class Check4(CheckIP):
    def __init__(self, host, **options):
        super().__init__(**options)
        self.addr = host.ipv4


class Check6(CheckIP):
    def __init__(self, host, **options):
        super().__init__(**options)
        self.addr = host.ipv6


class CheckPing4(Check4):
    def check(self):
        command = ['/bin/ping', '-c', '1', self.addr]
        return self.exec_with_timeout(command)


class CheckPing6(Check6):
    def check(self):
        command = ['/bin/ping6', '-c', '1', self.addr]
        return self.exec_with_timeout(command)


class CheckDNSZone(Check):
    def __init__(self, zone, **options):
        super().__init__(**options)
        self.zone = zone

    def __repr__(self):
        return '<%s on %s, options=%s>' % (self.__class__.__name__, self.zone, self._options)

    def check(self):
        self.errmsg = "Unimplemented"
        return False
        command = ['check_dns_soa', '-4', '-H', self.zone]
        return self.exec_with_timeout(command)


class CheckDNSRec(Check):
    def check(self, host, addr):
        self.errmsg = "Unimplemented"
        return False


class CheckDNSAut(Check):
    def check(self, host, addr):
        self.errmsg = "Unimplemented"
        return False


class Host(object):
    def __init__(self, ipv4, ipv6):
        self.ipv4 = ipv4
        self.ipv6 = ipv6

    def __repr__(self):
        return '<Host ipv4="%s" ipv6="%s">' % (self.ipv4, self.ipv6)


def genChecks(check, dests):
    return [check(d) for d in dests]


mail   = Host(ipv4='127.0.0.1', ipv6='::1')
web    = Host(ipv4='127.0.0.0', ipv6='::42')
alsace = Host(ipv4='127.0.0.1', ipv6='::1')

checks = \
  genChecks(CheckDNSZone, ["arn-fai.net", "netlib.re"]) + \
  genChecks(CheckPing4, [mail, web]) + \
  genChecks(CheckPing6, [mail, web])
  # genChecks(CheckSMTP4, [mail, alsace])
  # genChecks(CheckSMTP6, [mail, alsace])


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        def runner(check):
            return check.run(), check

        futures = []
        for check in checks:
            futures.append(executor.submit(runner, check))

        for future in concurrent.futures.as_completed(futures):
            success, check = future.result()
            if success:
                print("Check %s successful!" % (str(check)))
            else:
                print("Check %s failed:\n%s" %
                      (str(check), check.errmsg))
