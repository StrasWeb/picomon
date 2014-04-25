import concurrent.futures
from time import sleep
from subprocess_compat import TimeoutExpired, Popen, PIPE


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
        command = ['/bin/ping', '-c', '1', '-W', '2', self.addr]
        return self.exec_with_timeout(command, timeout=3)


class CheckPing6(Check6):
    def check(self):
        command = ['/bin/ping6', '-c', '1', '-W', '2', self.addr]
        return self.exec_with_timeout(command, timeout=3)


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


class Checks(list):
    def add(self, check, dests):
        self += [check(d) for d in dests]


mail   = Host(ipv4='127.0.0.1', ipv6='::1')
web    = Host(ipv4='127.0.0.0', ipv6='::42')
alsace = Host(ipv4='127.0.0.1', ipv6='::1')

checks = Checks()
checks.add(CheckDNSZone, ["arn-fai.net", "netlib.re"])
checks.add(CheckPing4, [mail, web])
checks.add(CheckPing6, [mail, web])
# checks.add(CheckSMTP4, [mail, alsace])
# checks.add(CheckSMTP6, [mail, alsace])


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
