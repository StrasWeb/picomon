import smtplib
from email.mime.text import MIMEText
from email.utils import make_msgid
from collections import defaultdict
from sys import stderr
from time import strftime
import email.charset
from threading import Thread
import queue

# Switch to quoted-printable so that we don't get something completely
# unreadable for non-ASCII chars if we have to look at raw email
email.charset.add_charset('utf-8', email.charset.QP, email.charset.QP, 'utf-8')


class ThreadedSMTP(object):
    """A helper class managing a thread sending emails through smtplib"""

    def __init__(self):
        self._queue = queue.Queue()
        self._loop = True
        self._thread = Thread(target=self.__loop)
        self._thread.deamon = True
        self._thread.start()

    def quit(self):
        if self._loop:
            self._loop = False
            self._queue.put(((), {}))  # put a dummy item to wake up the thread
            self._queue.join()
            self._thread.join()

    def __server_quit(self, server=None):
        if server is not None:
            server.quit()
        return None

    def __loop(self):
        from . import config
        host = config.emails.smtp_host
        timeout = config.emails.smtp_keepalive_timeout

        server = None
        while self._loop or not self._queue.empty():
            try:
                args, kwargs = self._queue.get(timeout=timeout)
            except queue.Empty:
                server = self.__server_quit(server)
            except KeyboardInterrupt as e:
                break
            else:
                if len(args) or len(kwargs):  # ignore empty items
                    try:
                        if server is None:
                            server = smtplib.SMTP(host)
                        server.sendmail(*args, **kwargs)
                    except Exception as e:
                        print("Couldn't send email: %s" % str(e), file=stderr)
            finally:
                if server:  # server is None on exception queue.Empty
                    self._queue.task_done()
        self.__server_quit(server)

    def sendmail(self, *args, **kwargs):
        self._queue.put((args, kwargs))


_mailer = ThreadedSMTP()


def quit():
    _mailer.quit()

def _send_email(subject, body, extra_headers={}):
    from . import config

    # encode / decode is a fix that didn't make it into Debian Wheezy
    # http://bugs.python.org/issue16948
    msg = MIMEText(body.encode('utf-8').decode('latin1'), 'plain', 'utf-8')

    msg['Subject'] = subject
    msg['From']    = config.emails.addr_from
    msg['To']      = ", ".join(config.emails.to)
    msg['Date']    = strftime('%a, %d %b %Y %H:%M:%S %z')

    for (key, val) in extra_headers.items():
        msg[key] = val

    _mailer.sendmail(config.emails.addr_from, config.emails.to,
                     msg.as_string())

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

    extra_headers={}
    extra_headers['Message-ID'] = make_msgid(type(check).__name__)
    # if check is OK it's a follow up, so set In-Reply-To
    if check.ok and hasattr(check, 'mails_msgid'):
        extra_headers['In-Reply-To'] = check.mails_msgid
        extra_headers['References'] = check.mails_msgid
    check.mails_msgid = extra_headers['Message-ID']

    _send_email(subject, msg_text, extra_headers)

def send_email_report(text):
    from . import config
    _send_email(config.emails.report.subject, text)
