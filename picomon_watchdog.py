import subprocess
import config
from lib import mails


retcode = subprocess.call(["python3", "picomon.py"])

mails.send_email(config.emails.watchdog_subject,
                 "Picomon exited with status %s" % retcode)

mails.quit()
