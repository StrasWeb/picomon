from lib.checks import *
from lib import config


# This is a sample config file, so that you have the most useful parameters
# to hand in there, along with their default value
# For a full, explained list see lib/__init__.py


# Polling
#########

# This is the base granularity (in seconds) for polling
# Each check may then individually be configured to run every N * base_tick
#config.base_tick = 60

# Default 'every' parameter for all checks, overridable on a per-check basis
#config.default_every = 1

# Default 'error_every' parameter for all checks (also overridable) to
# set a different 'every' parameter to checks in error state
# (-1 ⇒ same as 'every')
#config.default_error_every = -1


# Email notifications
#####################

# Email addresses to send to when an alert is triggered
config.emails.to.append('me@localhost')
config.emails.to.append('them@localhost')

# The From: address of generated mails
#config.emails.addr_from = 'Picomon <picomon@getfqdn()>

# The SMTP host, with optional :port suffix
#config.emails.smtp_host = 'localhost:25'

# Subject template for state change email notifications
# available substitutions:
#   - state ("Problem" or "OK")
#   - check (check's name, like "CheckDNSRec6")
#   - dest  (the target of the check ie. an IP or a Host's 'name' parameter)
#config.emails.subject_tpl = "[DOMAIN] {state}: {check} on {dest}"

# Interval in seconds between global reports when some checks are in error
# 0 disables reports
#config.emails.report.every = 0

# Subject of these report emails
#config.emails.report.subject = "[DOMAIN] Picomon report"


# Hosts
#######

localhost = Host(ipv4='127.0.0.1', ipv6='::1', name='localhost')
h1        = Host(ipv4='127.0.0.0', ipv6='::42', name='Strange IPs')
unnamed   = Host(ipv4='127.0.0.1', ipv6='::1')
v6only    = Host(ipv6='2001:0DB8::beef')


# Checks
########

day     = 86400 / config.base_tick
halfday = 43200 / config.base_tick

# For a list of checks, see the different classes in lib/checks.py

config.checks.add([CheckPing4, CheckPing6], [localhost, h1], retry=2, every=5)
#config.checks.add(CheckDNSZone, ["example.net", "example.org"], ip_version=4)
#config.checks.add(CheckDNSRec4, [h1])
#config.checks.add(CheckJabber6, [h1])
#config.checks.add(CheckSMTP4, [h1])
#config.checks.add(CheckSMTP6, [unnamed, v6only])

# SMTP : domaine address ok, relay refused
#config.checks.add([CheckSMTP4, CheckSMTP6], h1,
#                  from_addr='picomon@example.com',
#                  command='RCPT TO: postmaster@example.net', response='(250)',
#                  timeout=15, every=60)
#config.checks.add([CheckSMTP4, CheckSMTP6], h1,
#                  from_addr='picomon@example.com',
#                  command='RCPT TO: a@example.com', response='554',
#                  timeout=15, every=halfday)

# website with redirect to url on root
#config.checks.add([CheckHTTP4, CheckHTTP6], web,
#                  status=302, vhost='www.example.org', every=day)
#config.checks.add([CheckHTTP4, CheckHTTP6], web,
#                  string='hello world', vhost='www.example.org',
#                  url='/summary/router-edge/ipv4', every=halfday)
