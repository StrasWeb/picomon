from lib.checks import *


# This is the base granularity (in seconds) for polling
# Each check may then individually be configured to run every N * tick
base_tick = 60


mail     = Host(ipv4='127.0.0.1', ipv6='::1')
web      = Host(ipv4='127.0.0.0', ipv6='::42')
alsace   = Host(ipv4='127.0.0.1', ipv6='::1')
recursif = Host(ipv4='89.234.141.66', ipv6='2a00:5881:8100:1000::3')

checks = Checks()
checks.add(CheckDNSZone, ["arn-fai.net", "netlib.re"], ip_version=4)
checks.add(CheckPing4, [mail, web], retry=2)
checks.add(CheckPing6, [mail, web], retry=2)
checks.add(CheckDNSRec4, [recursif])
checks.add(CheckDNSRec6, [recursif])
# checks.add(CheckSMTP4, [mail, alsace])
# checks.add(CheckSMTP6, [mail, alsace])
