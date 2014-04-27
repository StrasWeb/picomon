from lib.checks import *


mail   = Host(ipv4='127.0.0.1', ipv6='::1')
web    = Host(ipv4='127.0.0.0', ipv6='::42')
alsace = Host(ipv4='127.0.0.1', ipv6='::1')

checks = Checks()
checks.add(CheckDNSZone, ["arn-fai.net", "netlib.re"])
checks.add(CheckPing4, [mail, web])
checks.add(CheckPing6, [mail, web])
# checks.add(CheckSMTP4, [mail, alsace])
# checks.add(CheckSMTP6, [mail, alsace])
