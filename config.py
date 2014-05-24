from lib.checks import *
from lib import config


# This is the base granularity (in seconds) for polling
# Each check may then individually be configured to run every N * tick
config.base_tick = 60

# Email addresses to send to when an alert is triggered
config.emails.to.append('john@localhost')
# The From: address
#config.emails.addr_from = 'Picomon <picomon@domain.tld>
# The SMTP host, with optional :port suffix
#config.emails.smtp_host = 'localhost:25'

# Subject template for state change email notifications
# available substitutions:
#   - state ("Problem" or "OK")
#   - check (check's name, like "CheckDNSRec6")
#   - dest  (the target of the check ie. an IP or a Host's 'name' parameter)
config.emails.subject_tpl = "[ARN] {state}: {check} on {dest}"


mail     = Host(ipv4='127.0.0.1', ipv6='::1', name='LXC mail')
web      = Host(ipv4='127.0.0.0', ipv6='::42', name='Bad IPs')
alsace   = Host(ipv4='127.0.0.1', ipv6='::1')
recursif = Host(ipv4='89.234.141.66', ipv6='2a00:5881:8100:1000::31',
                name='DNS récursif')

config.checks.add(CheckDNSZone, ["arn-fai.net", "netlib.re"], ip_version=4)
config.checks.add(CheckPing4, [mail, web], retry=2)
config.checks.add(CheckPing6, [mail, web], retry=2)
config.checks.add(CheckDNSRec4, [recursif])
config.checks.add(CheckDNSRec6, [recursif])
# config.checks.add(CheckSMTP4, [mail, alsace])
# config.checks.add(CheckSMTP6, [mail, alsace])
