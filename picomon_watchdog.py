import subprocess
import sys
import os
import importlib
from picomon import config
from picomon import mails


# launch picomon
retcode = subprocess.call(["python3", "picomon.py"] + sys.argv[1:])

# load config file
# (unprotected, will trigger exceptions if problems but real picomon beforehand)
configfile = "config.py"

if "-c" in sys.argv:
  configfile = sys.argv[sys.argv.index("-c")+1]
if "--config" in sys.argv:
  configfile = sys.argv[sys.argv.index("--config")+1]

sys.path.append(os.path.dirname(configfile))
filename  = os.path.basename(configfile)
base, ext = os.path.splitext(filename)
importlib.import_module(base)

# send warning
mails.send_email(config.emails.watchdog_subject,
                 "Picomon exited with status %s" % retcode)

