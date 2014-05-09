from lib.subprocess_compat import TimeoutExpired, Popen, PIPE
import re
import lib.mails as mails
from collections import Iterable


class Host(object):
    def __init__(self, ipv4='192.0.2.1', ipv6='2001:db8::1', name=None):
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.name = name if name is not None else "%s/%s" % (ipv4, ipv6)

    def __repr__(self):
        return '<Host ipv4="%s" ipv6="%s">' % (self.ipv4, self.ipv6)


class Checks(list):
    def add(self, checks, dests, **options):
        if not isinstance(checks, Iterable):
            checks = [checks]
        if not isinstance(dests, Iterable):
            dests = [dests]
        for check in checks:
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
        self.target_name = options.get('target_name', 'Unknown')

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
                    mails.send_email_for_check(self)
            else:
                if not self.ok:
                    mails.send_email_for_check(self)
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
    def __init__(self, host, **options):
        super().__init__(**options)
        self.target_name = host.name

    def __repr__(self):
        return '<%s on %s>' % (super().__repr__(), self.addr)


class Check4(CheckIP):
    def __init__(self, host, **options):
        super().__init__(host, **options)
        self.addr = host.ipv4


class Check6(CheckIP):
    def __init__(self, host, **options):
        super().__init__(host, **options)
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
        self.target_name = "zone '%s'" % zone

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


class CheckHTTP(Check):
    def build_command(self):
        command = ['/usr/lib/nagios/plugins/check_http',
                   '-I', self.addr, '-t', '2']
        if 'status' in self._options:
            command += ['-e', str(self._options['status'])]
        if 'vhost' in self._options:
            command += ['-H', str(self._options['vhost'])]
        if 'string' in self._options:
            command += ['-s', str(self._options['string'])]
        if 'url' in self._options:
            command += ['-u', str(self._options['url'])]
        return command

    def check(self):
        command = self.build_command()
        return self.exec_with_timeout(command, timeout=3)


class CheckHTTPS(CheckHTTP):
    def check(self):
        command = self.build_command() + ['--ssl']
        return self.exec_with_timeout(command, timeout=3)


class CheckHTTP4(CheckHTTP, Check4):
    pass


class CheckHTTP6(CheckHTTP, Check6):
    pass


class CheckHTTPS4(CheckHTTPS, Check4):
    pass


class CheckHTTPS6(CheckHTTPS, Check6):
    pass


class CheckSMTP(Check):
    def build_command(self):
        command = ['/usr/lib/nagios/plugins/check_smtp',
                   '-H', self.addr,
                   '-f', self._options.get('from_addr',
                                           'picomon@localhost.local'),
                   '-t', '2']
        if 'command' in self._options:
            command += ['-C', str(self._options['command'])]
        if 'response' in self._options:
            command += ['-R', str(self._options['response'])]
        return command

    def check(self):
        command = self.build_command()
        return self.exec_with_timeout(command, timeout=3)


class CheckSMTP4(CheckSMTP, Check4):
    pass


class CheckSMTP6(CheckSMTP, Check6):
    pass
