import smtplib
from email.mime.text import MIMEText
from collections import defaultdict
from sys import stderr
import email.charset

# Switch to quoted-printable so that we don't get something completely
# unreadable for non-ASCII chars if we have to look at raw email
email.charset.add_charset('utf-8', email.charset.QP, email.charset.QP, 'utf-8')

def send_email_for_check(check):
    from . import config
    # ensure we do not traceback with unknown substitutions
    subject = config.emails.subject_tpl.format_map(
              defaultdict(lambda: "<no substitution>",
                          state='OK' if check.ok else 'Problem',
                          check=check.__class__.__name__,
                          dest=check.target_name))

    msg_text = ''
    if not check.ok:
        msg_text += ("Check %s failed:\n%s" %
                    (str(check), check.errmsg.strip()))

    # encode / decode is a fix that didn't make it into Debian Wheezy
    # http://bugs.python.org/issue16948
    msg = MIMEText(msg_text.encode('utf-8').decode('latin1'), 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From']    = config.emails.addr_from
    msg['To']      = ", ".join(config.emails.to)

    try:
        server = smtplib.SMTP(config.emails.smtp_host)
        # server.set_debuglevel(1)
        server.sendmail(config.emails.addr_from, config.emails.to, msg.as_string())
        server.quit()
    except Exception as e:
        print("Couldn't send email: %s" % str(e), file=stderr)
