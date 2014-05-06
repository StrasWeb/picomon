from lib.subprocess_compat import TimeoutExpired, Popen, PIPE
import re


class Host(object):
    def __init__(self, ipv4, ipv6):
        self.ipv4 = ipv4
        self.ipv6 = ipv6

    def __repr__(self):
        return '<Host ipv4="%s" ipv6="%s">' % (self.ipv4, self.ipv6)


class Checks(list):
    def add(self, check, dests, **options):
        self += [check(d, **options) for d in dests]


class Check(object):
    def __init__(self, **options):
        self._options    = options
        self.retry       = options.get('retry', 0)
        self.retry_count = 0
        self.every       = options.get('every', 1)
        self.every_count = 0
        self.errmsg      = ''
        self.ok          = True

    def __repr__(self):
        return '{:<15s} N={}/{}, R={}/{}, {}'.format(self.__class__.__name__,
            self.every_count, self.every, self.retry_count, self.retry,
            self._options)

    def setup(self):
        pass

    def teardown(self):
        pass

    def check(self, host, addr):
        pass

    def run(self, immediate=False):
        self.every_count = (self.every_count + 1) % self.every
        if self.every_count == 0 or immediate:
            self.setup()
            if not self.check():
                self.retry_count = min(self.retry_count + 1, self.retry)
                if self.retry_count == self.retry or immediate:
                    self.ok = False
            else:
                self.ok = True
                self.retry_count = 0
            self.teardown()
        return self.ok

    def exec_with_timeout(self, command, timeout=2, pattern=''):
        self.errmsg = ''
        try:
            p = Popen(command, stdout=PIPE, stderr=PIPE)
        except OSError as e:
            self.errmsg = 'Check not available: ' + e.strerror
            return False
        try:
            out, err = p.communicate(timeout=timeout)
        except TimeoutExpired:
            p.kill()
            out, err = p.communicate()
            self.errmsg += "Operation timed out\n"
            return False
        if p.returncode != 0:
            if len(out) > 0:
                self.errmsg += "stdout:\n" + \
                               out.decode(errors='replace') + '\n'
            if len(err) > 0:
                self.errmsg += "stderr:\n" + \
                               err.decode(errors='replace') + '\n'
        if re.search(pattern, str(out), flags=re.M) is None:
            self.errmsg += ("Pattern '%s' not found in reply.\nstdout: %s"
                            % (pattern, out.decode(errors='replace')))
            return False
        return p.returncode == 0


class CheckIP(Check):
    def __repr__(self):
        return '<%s on %s>' % (super().__repr__(), self.addr)


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
        return '<%s for %s>' % (super().__repr__(), self.zone)

    def check(self):
        command = ['check_dns_soa', '-H', self.zone]
        if self._options.get('ip_version', 0) in [4, 6]:
            command.append('-' + str(self._options['ip_version']))
        return self.exec_with_timeout(command)


class CheckDNSRec(Check):
    def check(self):
        command = ['dig', 'www.google.com', '@' + self.addr]
        return self.exec_with_timeout(command, pattern='status: NOERROR')


class CheckDNSRec4(CheckDNSRec, Check4):
    pass


class CheckDNSRec6(CheckDNSRec, Check6):
    pass


class CheckDNSAut(Check):
    def check(self, host, addr):
        self.errmsg = "Unimplemented"
        return False
