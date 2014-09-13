import socket
from .attrtree import AttrTree
from .checks import Checks


config = AttrTree()

# the list of checks
config.install_attr('checks', Checks())

# This is the base granularity (in seconds) for polling
# Each check may then individually be configured to run every N * tick
config.install_attr('base_tick', 60)

# Default "every" check parameter, can be overridden on a per-check basis
config.install_attr('default_every', 1)

# Default "error_every" (how often we retry checks that are in error) parameter
# -1 disables feature (same as regular "every"), can be also be overridden
config.install_attr('default_error_every', -1)

# Verbosity level (one of CRITICAL, ERROR, WARNING, INFO, DEBUG)
config.install_attr('verb_level', 'INFO')

# Email addresses to send to when an alert is triggered
config.install_attr('emails.to', [])
# The From: address
config.install_attr('emails.addr_from',
                    'Picomon <picomon@%s>' % socket.getfqdn())
# The SMTP host, with optional :port suffix
config.install_attr('emails.smtp_host', 'localhost:25')
# The inactive timeout after which to close the SMTP connection
config.install_attr('emails.smtp_keepalive_timeout', 60)
# Timeout after which to retry sending emails after a failure
config.install_attr('emails.smtp_retry_timeout', 60)
# Interval in seconds between global reports when some checks are in error
# 0 disables reports
config.install_attr('emails.report.every', 0)

# Subject template for state change email notifications
# available substitutions:
#   - state ("Problem" or "OK")
#   - check (check's name, like "CheckDNSRec6")
#   - dest  (the target of the check ie. an IP or a Host's 'name'
#            parameter)
config.install_attr('emails.subject_tpl',
                    '[DOMAIN] {state}: {check} on {dest}')
# reports email subject
config.install_attr('emails.report.subject', '[DOMAIN] Picomon error report')
# watchdog error email subject
config.install_attr('emails.watchdog_subject', '[DOMAIN] Picomon stopped')
