from subprocess import Popen, PIPE
import concurrent.futures
from time import sleep


def ip_version(addr):
    return 6 if ':' in addr else 4


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
        p = Popen(command, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        # with 3.3 we got timeout…
        # try:
            # out, err = p.communicate(timeout=timeout)
        # except TimeoutExpired:
            # p.kill()
            # out, err = p.communicate()
        ret = p.poll()
        if ret != 0:
            self.errmsg = "stdout: " + str(out) + '\n' + \
                          "stderr: " + str(err) + '\n'
        return ret == 0

    def exec_by_ip_family(self, addr, v4command, v6command):
        ipv = ip_version(addr)
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
