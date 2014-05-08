import socket
import smtplib
from email.mime.text import MIMEText
from collections import defaultdict
from sys import stderr
import email.charset

# Switch to quoted-printable so that we don't get something completely
# unreadable for non-ASCII chars if we have to look at raw email
email.charset.add_charset('utf-8', email.charset.QP, email.charset.QP, 'utf-8')

def send_email_for_check(check):
    from config import emails, subject_tpl
    addr_from  = "Picomon <picomon@%s>" % socket.getfqdn()

    # ensure we do not traceback with unknown substitutions
    subject = subject_tpl.format_map(
              defaultdict(lambda: "<no substitution>",
                          state='OK' if check.ok else 'Problem',
                          check=check.__class__.__name__,
                          dest=check.target_name))

    msg_text = ''
    if check.ok:
        msg_text = "FYI last error for this check was:\n"
    msg_text += ("Check %s failed:\n%s" %
                (str(check), check.errmsg.strip()))

    # encode / decode is a fix that didn't make it into Debian Wheezy
    # http://bugs.python.org/issue16948
    msg = MIMEText(msg_text.encode('utf-8').decode('latin1'), 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From']    = addr_from
    msg['To']      = ", ".join(emails)

    try:
        server = smtplib.SMTP('localhost')
        # server.set_debuglevel(1)
        server.sendmail(addr_from, emails, msg.as_string())
        server.quit()
    except Exception as e:
        print("Couldn't send email: %s" % str(e), file=stderr)
